"""AOSP section models and reconstruction. Opaque padding/trailers are preserved explicitly."""

import os
from pathlib import Path
import struct
import tempfile
from secripts.images.android import inspect_image
from secripts.images.artifacts import (
    read,
    digest,
    canonical,
    exclusive,
    json_model,
    child,
    NewWorkspace,
    evidence,
    CAP,
)
from secripts.images.comparison import Comparison
from secripts.safety import SecError

RAMDISK_TYPES = {0: "NONE", 1: "PLATFORM", 2: "RECOVERY", 3: "DLKM"}


def model(path):
    path = Path(path)
    raw = read(path)
    parsed = inspect_image(path)
    if parsed["sha256"] != digest(raw):
        raise SecError("Input changed during model inspection", 4)
    if parsed["type"] not in {"ANDROID_BOOT", "VENDOR_BOOT"}:
        raise SecError("Extraction/reconstruction supports AOSP Android boot/vendor_boot only", 5)
    # Unsupported compression/CPIO does not invalidate container geometry.
    if parsed["avb"]["status"] == "FAIL":
        raise SecError("Malformed AVB metadata; reconstruction refused", 4)
    version = parsed["properties"]["header_version"]
    vendor = parsed["type"] == "VENDOR_BOOT"
    sections = []
    for name, section in parsed["sections"].items():
        if name.startswith("fragment_"):
            continue
        offset, size = section["offset"], section["size"]
        sections.append(
            {
                "name": name,
                "offset": offset,
                "size": size,
                "sha256": digest(raw[offset : offset + size]),
            }
        )
    sections.sort(key=lambda s: (s["offset"], s["name"]))
    # Zero-size entries do not own bytes; all other bytes have disjoint explicit ownership.
    ranges = []
    cursor = 0
    for section in [s for s in sections if s["size"]]:
        if section["offset"] < cursor:
            raise SecError("Section overlap", 4)
        if section["offset"] > cursor:
            ranges.append(
                {
                    "name": f"opaque_{len(ranges):04d}",
                    "offset": cursor,
                    "size": section["offset"] - cursor,
                    "kind": "OPAQUE",
                }
            )
        ranges.append({**section, "kind": "COMPONENT"})
        cursor = section["offset"] + section["size"]
    if cursor < len(raw):
        ranges.append(
            {"name": "opaque_tail", "offset": cursor, "size": len(raw) - cursor, "kind": "OPAQUE"}
        )
    for index, section in enumerate(ranges):
        section["sha256"] = digest(raw[section["offset"] : section["offset"] + section["size"]])
        section["file"] = f"extracted/part-{index:04d}.bin"

    def u32(at):
        return struct.unpack_from("<I", raw, at)[0]

    header_fields = {"header_version": version, "page_size": parsed["properties"]["page_size"]}
    if vendor:
        header_fields.update(
            kernel_address=u32(16),
            ramdisk_address=u32(20),
            tags_address=u32(2076),
            dtb_address=struct.unpack_from("<Q", raw, 2104)[0],
            command_line_sha256=digest(raw[28:2076]),
            board_name_sha256=digest(raw[2080:2096]),
        )
    elif version >= 3:
        header_fields.update(os_version_patch=u32(16), command_line_sha256=digest(raw[44:1580]))
    else:
        header_fields.update(
            kernel_address=u32(12),
            ramdisk_address=u32(20),
            second_address=u32(28),
            tags_address=u32(32),
            os_version_patch=u32(44),
            command_line_sha256=digest(raw[64:576] + raw[608:1632]),
            board_name_sha256=digest(raw[48:64]),
        )
    residual = bytearray(raw[: next(s["size"] for s in sections if s["name"] == "header")])
    mutable = (
        (24, 2100, 2112, 2124)
        if vendor and version == 4
        else (24, 2100)
        if vendor
        else (8, 12)
        if version >= 3
        else (8, 16, 24)
    )
    for offset in mutable:
        residual[offset : offset + 4] = bytes(4)
    header_fields["residual_header_sha256"] = digest(residual)
    fragments = [
        {
            **f,
            "type_name": RAMDISK_TYPES.get(f["type"], "UNKNOWN"),
            "sha256": digest(raw[f["offset"] : f["offset"] + f["size"]]),
        }
        for f in parsed["properties"].get("fragments", [])
    ]
    return {
        "schema": 1,
        "model": "android-image",
        "format": parsed["type"],
        "source_sha256": digest(raw),
        "source_size": len(raw),
        "header": header_fields,
        "sections": sections,
        "parts": ranges,
        "fragments": fragments,
        "avb": parsed["avb"],
        "partition_role": parsed.get("role", {"value": "UNKNOWN", "state": "UNKNOWN"}),
        "reconstruction": "EXACT_LAYOUT; modern AOSP unsigned images additionally permit component resizing",
        "qualification": {
            "device_compatibility": "UNTESTED",
            "bootability": "UNTESTED",
            "cryptographic_validity": "UNVERIFIED",
        },
    }


def unpack(path, output):
    raw = read(path)
    value = model(path)
    if value["source_sha256"] != digest(raw):
        raise SecError("Input changed before extraction", 4)
    with NewWorkspace(output) as root:
        exclusive(root / "source/artifact.bin", raw)
        os.chmod(root / "source/artifact.bin", 0o400)
        for part in value["parts"]:
            exclusive(root / part["file"], raw[part["offset"] : part["offset"] + part["size"]])
        for fragment in value["fragments"]:
            fragment["file"] = f"extracted/fragment-{fragment['index']:04d}.bin"
            exclusive(
                root / fragment["file"],
                raw[fragment["offset"] : fragment["offset"] + fragment["size"]],
            )
        canonical(root / "model/image.json", value)
    receipt = evidence(
        "image.unpack",
        source=path,
        workspace=str(output),
        format=value["format"],
        components=value["sections"],
        fragment_count=len(value["fragments"]),
    )
    return {
        "status": "UNPACKED",
        "workspace": str(output),
        "model": value,
        "receipt_id": receipt["receipt_id"],
    }


def load_workspace(path):
    path = Path(path)
    if path.is_symlink():
        raise SecError("Symlink workspace refused", 4)
    value = json_model(child(path, "model/image.json"), "android-image")
    original_path = child(path, "source/artifact.bin")
    original = read(original_path)
    if digest(original) != value["source_sha256"]:
        raise SecError("Immutable source snapshot changed", 4)
    baseline = model(original_path)
    # Treat local manifests as untrusted too. Editable content lives only in payload files.
    left = {k: v for k, v in value.items() if k != "fragments"}
    right = {k: v for k, v in baseline.items() if k != "fragments"}
    if left != right or len(value["fragments"]) != len(baseline["fragments"]):
        raise SecError("Image model metadata changed; unsupported schema/edit contract", 4)
    for stored, expected in zip(value["fragments"], baseline["fragments"], strict=True):
        if {k: v for k, v in stored.items() if k != "file"} != expected or stored.get(
            "file"
        ) != f"extracted/fragment-{stored['index']:04d}.bin":
            raise SecError("Fragment model metadata changed", 4)
    return value, original


def rebuild(workspace, output):
    workspace = Path(workspace)
    value, original = load_workspace(workspace)
    if Path(output).resolve() == child(workspace, "source/artifact.bin"):
        raise SecError("Source overwrite refused", 4)
    parts = []
    total = 0
    for part in value["parts"]:
        data = read(child(workspace, part["file"]))
        total += len(data)
        if total > CAP:
            raise SecError("Reconstruction aggregate limit", 4)
        if part["kind"] == "OPAQUE" and digest(data) != part["sha256"]:
            raise SecError("Opaque padding/trailer modification refused", 4)
        if part["name"] == "header" and digest(data) != part["sha256"]:
            raise SecError("Raw header edits refused; no arbitrary configuration injection", 4)
        parts.append((part, data))
    components = {part["name"]: data for part, data in parts if part["kind"] == "COMPONENT"}
    fragment_changes = False
    for fragment in value["fragments"]:
        payload = read(child(workspace, fragment["file"]))
        if digest(payload) != fragment["sha256"]:
            fragment_changes = True
    if fragment_changes:
        full = components["vendor_ramdisk"]
        original_full = next(
            s["sha256"] for s in value["sections"] if s["name"] == "vendor_ramdisk"
        )
        if digest(full) != original_full:
            raise SecError("Ambiguous edits: modify fragments or whole vendor ramdisk, not both", 4)
        fragments = value["fragments"]
        relative = next(s["offset"] for s in value["sections"] if s["name"] == "vendor_ramdisk")
        if [f["offset"] - relative for f in fragments] != [
            sum(f["size"] for f in fragments[:i]) for i in range(len(fragments))
        ] or sum(f["size"] for f in fragments) != len(full):
            raise SecError("Fragment resizing requires a contiguous complete ramdisk table", 4)
        table = bytearray(components["vendor_ramdisk_table"])
        entry_size = struct.unpack_from("<I", components["header"], 2120)[0]
        chunks = []
        offset = 0
        for fragment in fragments:
            chunk = read(child(workspace, fragment["file"]))
            struct.pack_into("<II", table, fragment["index"] * entry_size, len(chunk), offset)
            chunks.append(chunk)
            offset += len(chunk)
        components["vendor_ramdisk"] = b"".join(chunks)
        components["vendor_ramdisk_table"] = bytes(table)
    changed = fragment_changes or any(digest(data) != part["sha256"] for part, data in parts)
    if changed and (
        value["avb"].get("detected")
        or any(s["name"] == "boot_signature" and s["size"] for s in value["sections"])
    ):
        raise SecError(
            "Signed/AVB-bearing image modification refused; existing signatures cannot authenticate edits",
            4,
        )
    if value["fragments"] and not fragment_changes:
        full = components.get("vendor_ramdisk", b"")
        original_size = next(s["size"] for s in value["sections"] if s["name"] == "vendor_ramdisk")
        if len(full) != original_size:
            raise SecError(
                "Resize vendor_boot v4 through individual fragments; whole-blob fragment mapping is unresolved",
                4,
            )
    resize = any(len(components.get(part["name"], data)) != part["size"] for part, data in parts)
    if not resize:
        rebuilt = b"".join(components.get(part["name"], data) for part, data in parts)
    else:
        if value["header"]["header_version"] < 3:
            raise SecError(
                "Legacy component resizing unsupported; exact-layout reconstruction only", 5
            )
        page = value["header"]["page_size"]
        header = bytearray(components["header"])

        def aligned(data):
            return data + bytes((-len(data)) % page)

        if value["format"] == "ANDROID_BOOT":
            kernel = components.get("kernel", b"")
            ramdisk = components.get("ramdisk", b"")
            struct.pack_into("<II", header, 8, len(kernel), len(ramdisk))
            rebuilt = aligned(bytes(header)) + aligned(kernel) + aligned(ramdisk)
        else:
            ramdisk = components.get("vendor_ramdisk", b"")
            dtb = components.get("dtb", b"")
            struct.pack_into("<I", header, 24, len(ramdisk))
            struct.pack_into("<I", header, 2100, len(dtb))
            rebuilt = aligned(bytes(header)) + aligned(ramdisk) + aligned(dtb)
            if value["header"]["header_version"] == 4:
                table = components.get("vendor_ramdisk_table", b"")
                config = components.get("bootconfig", b"")
                struct.pack_into("<I", header, 2112, len(table))
                struct.pack_into("<I", header, 2124, len(config))
                rebuilt = (
                    aligned(bytes(header))
                    + aligned(ramdisk)
                    + aligned(dtb)
                    + aligned(table)
                    + aligned(config)
                )
        # Do not discard unknown padding or trailing bytes to make a resized image appear valid.
        if any(any(data) for part, data in parts if part["kind"] == "OPAQUE"):
            raise SecError("Nonzero opaque padding/trailing bytes prevent safe resizing", 4)
        tail = next((data for part, data in parts if part["name"] == "opaque_tail"), b"")
        if any(tail):
            raise SecError("Nonzero trailing bytes prevent safe resizing", 4)
    if len(rebuilt) > CAP:
        raise SecError("Rebuilt image exceeds output limit", 4)
    with tempfile.TemporaryDirectory(prefix="js-rebuild-check-") as directory:
        temporary = Path(directory) / "image.bin"
        temporary.write_bytes(rebuilt)
        after = model(temporary)
    exclusive(output, rebuilt)
    receipt = evidence(
        "image.rebuild",
        source=child(workspace, "source/artifact.bin"),
        output=output,
        format=value["format"],
        component_hashes=after["sections"],
        resized=resize,
        cryptographic_state="UNVERIFIED",
        parameters={"layout": "AOSP_REALIGNED" if resize else "PRESERVED"},
    )
    return {
        "status": "REBUILT",
        "sha256": digest(rebuilt),
        "bytes": len(rebuilt),
        "resized": resize,
        "receipt_id": receipt["receipt_id"],
        "qualification": after["qualification"],
    }


def compare(first, second):
    raw_a, raw_b = read(first), read(second)
    a, b = model(first), model(second)
    result = Comparison(raw_a, raw_b)
    if a["format"] != b["format"] or a["header"]["header_version"] != b["header"]["header_version"]:
        result.add(
            "container",
            "STRUCTURE",
            [a["format"], a["header"]["header_version"]],
            [b["format"], b["header"]["header_version"]],
            "Container generation differs",
        )
        result.value.update(structural_equivalence="DIFFERENT", semantic_equivalence="DIFFERENT")
        return result.finish()
    x, y = {s["name"]: s for s in a["sections"]}, {s["name"]: s for s in b["sections"]}
    content = True
    semantic_content = True
    for name in sorted(set(x) | set(y)):
        left, right = x.get(name), y.get(name)
        if left is None or right is None:
            result.add(name, "STRUCTURE", left, right, "Component added/removed")
            content = False
            semantic_content = False
            continue
        if left["sha256"] != right["sha256"]:
            result.add(
                name,
                "METADATA"
                if name == "header"
                else "SIGNATURE"
                if "signature" in name
                else "CONTENT",
                left["sha256"],
                right["sha256"],
                "Component bytes differ",
            )
            if name != "header":
                content = False
                equivalent = False
                if name == "ramdisk":
                    from secripts.images.comparison import ramdisks

                    try:
                        comparison = ramdisks(
                            raw_a[left["offset"] : left["offset"] + left["size"]],
                            raw_b[right["offset"] : right["offset"] + right["size"]],
                        )
                        equivalent = comparison["semantic_equivalence"] == "SEMANTICALLY_EQUIVALENT"
                        result.add(
                            name + "/decoded",
                            "COMPRESSION",
                            comparison["original_sha256"],
                            comparison["rebuilt_sha256"],
                            "Decoded ramdisk semantics matched"
                            if equivalent
                            else "Decoded ramdisk semantics differ",
                            expected=equivalent,
                        )
                    except ValueError:
                        pass
                if not equivalent:
                    semantic_content = False
        if (left["offset"], left["size"]) != (right["offset"], right["size"]):
            result.add(
                name,
                "ALIGNMENT",
                [left["offset"], left["size"]],
                [right["offset"], right["size"]],
                "Component geometry differs",
            )
    metadata = a["header"] == b["header"] and a["fragments"] == b["fragments"]
    if a["header"] != b["header"]:
        result.add(
            "header-fields",
            "METADATA",
            a["header"],
            b["header"],
            "Preserved AOSP field values differ",
        )
    if raw_a != raw_b and not result.value["difference_count"]:
        result.add(
            "opaque-bytes",
            "UNKNOWN",
            digest(raw_a),
            digest(raw_b),
            "Unmodeled padding/trailer bytes differ; semantic equivalence unresolved",
        )
        result.value["unresolved"].append("Opaque bytes differ")
    identical = raw_a == raw_b
    result.value.update(
        structural_equivalence="STRUCTURALLY_EQUIVALENT" if list(x) == list(y) else "DIFFERENT",
        component_equivalence="CONTENT_EQUIVALENT" if content else "DIFFERENT",
        metadata_equivalence="SEMANTICALLY_EQUIVALENT" if metadata else "DIFFERENT",
        semantic_equivalence="SEMANTICALLY_EQUIVALENT"
        if identical or semantic_content and metadata and not result.value["unresolved"]
        else "DIFFERENT",
    )
    return result.finish()


def roundtrip(path, output=None):
    if output is None:
        with tempfile.TemporaryDirectory(prefix="js-roundtrip-") as directory:
            return roundtrip(path, Path(directory) / "workspace")
    unpack(path, output)
    rebuilt = Path(output) / "rebuilt/image.bin"
    rebuild(output, rebuilt)
    result = compare(path, rebuilt)
    canonical(Path(output) / "reports/roundtrip.json", result)
    receipt = evidence("image.roundtrip", source=path, output=rebuilt, comparison=result)
    return {
        **result,
        "receipt_id": receipt["receipt_id"],
        "workspace": str(output) if Path(output).exists() else "TEMPORARY",
    }
