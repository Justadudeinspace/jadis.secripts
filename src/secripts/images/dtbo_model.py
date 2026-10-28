"""DT table canonical reconstruction, shared blobs and controlled virtual extraction."""

from pathlib import Path
import struct
from secripts.images.devicetree import dtbo, fdt
from secripts.images.artifacts import read, digest, exclusive, canonical, NewWorkspace, evidence
from secripts.images.comparison import Comparison


def model(data):
    value = dtbo(data)
    value.update(
        schema=1,
        model="android-dt-table",
        source_sha256=digest(data),
        header_size=struct.unpack_from(">I", data, 8)[0],
        entry_size=struct.unpack_from(">I", data, 12)[0],
        entries_offset=struct.unpack_from(">I", data, 20)[0],
    )
    payloads = {}
    for entry in value["entries"]:
        key = (entry["offset"], entry["size"])
        if key not in payloads:
            payloads[key] = data[key[0] : key[0] + key[1]]
        entry["payload"] = payloads[key]
    return value


def pack(value):
    if value.get("schema") != 1 or value.get("model") != "android-dt-table":
        raise ValueError("Unsupported DTBO model")
    if value.get("header_size", 32) != 32 or value.get("entry_size", 32) != 32:
        raise ValueError("Extended DTBO header/entry reconstruction unsupported")
    entries = value["entries"]
    version = value["version"]
    page = value["page_size"]
    if (
        len(entries) > 4096
        or version not in (0, 1)
        or not 512 <= page <= 65536
        or page & (page - 1)
    ):
        raise ValueError("Invalid DTBO canonical fields")
    count = len(entries)
    table_end = 32 + 32 * count
    output = bytearray(table_end)
    unique = {}
    validated = set()
    for index, entry in enumerate(entries):
        compressed = version == 1 and entry["custom"][0] & 15
        payload = entry["payload"]
        if len(payload) > 32 * 1024**2:
            raise ValueError("DTBO entry input limit")
        key = digest(payload)
        validation = (key, compressed)
        if validation not in validated:
            if compressed:
                from secripts.images.codecs import decode

                if compressed not in (1, 2):
                    raise ValueError("COMPRESSED_ENTRY_UNSUPPORTED")
                decoded, _ = decode(payload, "zlib" if compressed == 1 else "gzip")
                fdt(decoded)
            else:
                fdt(payload)
            validated.add(validation)
        if key not in unique:
            output.extend(bytes((-len(output)) % 4))
            unique[key] = len(output)
            output.extend(payload)
        fields = [len(payload), unique[key], entry["id"], entry["revision"], *entry["custom"]]
        if len(fields) != 8 or any(type(n) is not int or not 0 <= n <= 0xFFFFFFFF for n in fields):
            raise ValueError("Invalid DTBO entry fields")
        struct.pack_into(">8I", output, 32 + 32 * index, *fields)
        if len(output) > 32 * 1024**2:
            raise ValueError("DTBO aggregate output limit")
    struct.pack_into(">8I", output, 0, 0xD7B7AB1E, len(output), 32, 32, count, 32, page, version)
    return bytes(output)


def extract(path, output):
    raw = read(path, 32 * 1024**2)
    value = model(raw)
    with NewWorkspace(output) as root:
        exclusive(root / "source/artifact.bin", raw)
        __import__("os").chmod(root / "source/artifact.bin", 0o400)
        files = {}
        for entry in value["entries"]:
            key = (entry["offset"], entry["size"])
            payload = entry.pop("payload")
            if key not in files:
                files[key] = f"extracted/dt-{entry['index']:04d}.bin"
                exclusive(root / files[key], payload)
            entry["file"] = files[key]
        canonical(root / "model/dtbo.json", value)
    receipt = evidence(
        "dtbo.extract", source=path, workspace=str(output), entries=len(value["entries"])
    )
    return {
        "status": "EXTRACTED",
        "entries": len(value["entries"]),
        "receipt_id": receipt["receipt_id"],
    }


def rebuild(workspace, output):
    from secripts.images.artifacts import json_model, child

    root = Path(workspace)
    value = json_model(child(root, "model/dtbo.json"), "android-dt-table")
    raw = read(child(root, "source/artifact.bin"), 32 * 1024**2)
    if digest(raw) != value["source_sha256"]:
        raise ValueError("Immutable DTBO source changed")
    original = model(raw)
    expected = {
        **original,
        "entries": [{k: v for k, v in e.items() if k != "payload"} for e in original["entries"]],
    }
    stored = {
        **value,
        "entries": [{k: v for k, v in e.items() if k != "file"} for e in value["entries"]],
    }
    if stored != expected:
        raise ValueError("DTBO metadata model changed; unsupported editing contract")
    payloads = {}
    total = 0
    for entry in value["entries"]:
        filename = entry["file"]
        if filename not in payloads:
            data = read(child(root, filename), 32 * 1024**2)
            total += len(data)
            if total > 32 * 1024**2:
                raise ValueError("DTBO workspace aggregate budget")
            payloads[filename] = data
        entry["payload"] = payloads[filename]
    result = pack(value)
    exclusive(output, result)
    receipt = evidence(
        "dtbo.rebuild",
        source=child(root, "source/artifact.bin"),
        output=output,
        determinism="Canonical 32-byte header/entries; 4-byte blob alignment; identical blobs shared",
    )
    return {"status": "REBUILT", "sha256": digest(result), "receipt_id": receipt["receipt_id"]}


def compare(first, second):
    raw_a, raw_b = read(first, 32 * 1024**2), read(second, 32 * 1024**2)
    a, b = model(raw_a), model(raw_b)
    result = Comparison(raw_a, raw_b)

    def semantic(value):
        return {
            "version": value["version"],
            "page_size": value["page_size"],
            "entries": [
                {k: e[k] for k in ("id", "revision", "custom", "sha256")} for e in value["entries"]
            ],
        }

    equal = semantic(a) == semantic(b)
    if not equal:
        result.add(
            "entries",
            "CONTENT",
            semantic(a),
            semantic(b),
            "DTBO entry metadata/content/order differs",
        )
    elif raw_a != raw_b:
        result.add(
            "table-layout",
            "ALIGNMENT",
            {
                "header": a["header_size"],
                "entry": a["entry_size"],
                "offset": a["entries_offset"],
                "size": len(raw_a),
            },
            {
                "header": b["header_size"],
                "entry": b["entry_size"],
                "offset": b["entries_offset"],
                "size": len(raw_b),
            },
            "Canonical table packing or shared-blob/padding layout differs",
            expected=True,
        )
    result.value.update(
        structural_equivalence="STRUCTURALLY_EQUIVALENT"
        if len(a["entries"]) == len(b["entries"])
        else "DIFFERENT",
        semantic_equivalence="SEMANTICALLY_EQUIVALENT" if equal else "DIFFERENT",
        metadata_equivalence="SEMANTICALLY_EQUIVALENT" if equal else "DIFFERENT",
        component_equivalence="CONTENT_EQUIVALENT"
        if [e["sha256"] for e in a["entries"]] == [e["sha256"] for e in b["entries"]]
        else "DIFFERENT",
    )
    if (
        a["header_size"] > 32
        or b["header_size"] > 32
        or a["entry_size"] > 32
        or b["entry_size"] > 32
    ):
        result.value.update(
            semantic_equivalence="UNVERIFIED",
            unresolved=["Extended header/entry bytes not semantically modeled"],
        )
    return result.finish()
