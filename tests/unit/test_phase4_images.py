import json
import struct

import pytest

from secripts.images import bootmodel, dtbo_model, workflows
from secripts.images.artifacts import digest
from secripts.images.devicetree import fdt, dtbo
from secripts.safety import SecError
from tests.fixtures import images
from tests.unit.test_image_phase2 import boot, newc


def vendor(path, version=4):
    page = 4096
    header = bytearray(page)
    header[:8] = b"VNDRBOOT"
    struct.pack_into("<II", header, 8, version, page)
    blobs = [b"fragment-one", b"fragment-two"]
    rd = b"".join(blobs)
    struct.pack_into("<I", header, 24, len(rd))
    struct.pack_into("<I", header, 2096, 2112 if version == 3 else 2128)
    dt = images.fdt()
    struct.pack_into("<I", header, 2100, len(dt))
    body = rd + bytes((-len(rd)) % page) + dt + bytes((-len(dt)) % page)
    if version == 4:
        entries = []
        offset = 0
        for index, blob in enumerate(blobs):
            entry = bytearray(108)
            struct.pack_into("<III", entry, 0, len(blob), offset, index + 1)
            entry[12:18] = b"frag" + str(index).encode() + b"\0"
            struct.pack_into("<16I", entry, 44, *range(16))
            entries.append(entry)
            offset += len(blob)
        table = b"".join(entries)
        config = b"androidboot.test=synthetic\n"
        struct.pack_into("<4I", header, 2112, len(table), 2, 108, len(config))
        body += table + bytes((-len(table)) % page) + config + bytes((-len(config)) % page)
    path.write_bytes(header + body)
    return path


@pytest.mark.parametrize("version", range(5))
def test_boot_exact_layout_roundtrip(tmp_path, version):
    p = tmp_path / "boot.img"
    p.write_bytes(images.boot(version))
    # Preserve deliberately noncanonical tail bytes as explicit opaque evidence.
    p.write_bytes(p.read_bytes() + b"UNMODELED_SYNTHETIC_TAIL")
    output = tmp_path / "workspace"
    result = workflows.roundtrip(p, output)
    assert result["byte_identity"] == "BYTE_IDENTICAL"
    assert result["semantic_equivalence"] == "SEMANTICALLY_EQUIVALENT"
    assert result["cryptographic_state"] == "UNVERIFIED"
    assert result["device_compatibility"] == "UNTESTED"
    assert (output / "rebuilt/artifact.bin").read_bytes() == p.read_bytes()


@pytest.mark.parametrize("version", [3, 4])
def test_vendor_boot_preserves_fragments_and_order(tmp_path, version):
    p = vendor(tmp_path / "vendor_boot.img", version)
    result = workflows.roundtrip(p, tmp_path / "workspace")
    assert result["byte_identity"] == "BYTE_IDENTICAL"
    model = bootmodel.model(p)
    if version == 4:
        assert [f["type_name"] for f in model["fragments"]] == ["PLATFORM", "RECOVERY"]
        assert model["fragments"][0]["board_ids"] == list(range(16))
        assert (tmp_path / "workspace/extracted/fragment-0001.bin").read_bytes() == b"fragment-two"


@pytest.mark.parametrize("version", [3, 4])
def test_modern_boot_component_resize(tmp_path, version):
    p = boot(tmp_path / "boot.img", newc(), b"kernel", version)
    workspace = tmp_path / "workspace"
    bootmodel.unpack(p, workspace)
    manifest = json.loads((workspace / "model/image.json").read_text())
    part = next(s for s in manifest["parts"] if s["name"] == "ramdisk")
    (workspace / part["file"]).write_bytes(newc(payload=b"a" * 6000))
    out = tmp_path / "rebuilt.img"
    value = bootmodel.rebuild(workspace, out)
    assert value["resized"]
    rebuilt = bootmodel.model(out)
    assert next(s for s in rebuilt["sections"] if s["name"] == "ramdisk")["size"] > 4096
    assert bootmodel.compare(p, out)["semantic_equivalence"] == "DIFFERENT"
    assert digest(p.read_bytes()) == manifest["source_sha256"]


def test_vendor_fragment_resize_and_ambiguous_edits(tmp_path):
    p = vendor(tmp_path / "vendor_boot.img")
    workspace = tmp_path / "workspace"
    bootmodel.unpack(p, workspace)
    fragment = workspace / "extracted/fragment-0000.bin"
    fragment.write_bytes(b"expanded" * 1000)
    out = tmp_path / "rebuilt.img"
    bootmodel.rebuild(workspace, out)
    parsed = bootmodel.model(out)
    assert parsed["fragments"][0]["size"] == 8000
    assert parsed["fragments"][1]["size"] == len(b"fragment-two")
    manifest = json.loads((workspace / "model/image.json").read_text())
    part = next(s for s in manifest["parts"] if s["name"] == "vendor_ramdisk")
    (workspace / part["file"]).write_bytes(b"also-edited")
    with pytest.raises(SecError, match="Ambiguous"):
        bootmodel.rebuild(workspace, tmp_path / "bad.img")


def test_workspace_source_output_and_manifest_guards(tmp_path):
    p = boot(tmp_path / "boot.img", newc(), b"kernel")
    root = tmp_path / "workspace"
    bootmodel.unpack(p, root)
    with pytest.raises(SecError, match="new directory"):
        bootmodel.unpack(p, root)
    with pytest.raises(SecError, match="overwrite"):
        bootmodel.rebuild(root, p)
    model_path = root / "model/image.json"
    value = json.loads(model_path.read_text())
    value["parts"][0]["file"] = "../../escape"
    model_path.write_text(json.dumps(value))
    with pytest.raises(SecError, match="metadata changed"):
        bootmodel.rebuild(root, tmp_path / "output")
    value["schema"] = 99
    model_path.write_text(json.dumps(value))
    with pytest.raises(SecError, match="unsupported"):
        bootmodel.rebuild(root, tmp_path / "output")


def test_signed_container_modification_refused(tmp_path):
    p = boot(tmp_path / "boot.img", newc(), b"kernel")
    raw = bytearray(p.read_bytes())
    struct.pack_into("<I", raw, 1580, 4)
    raw.extend(b"SIGN")
    p.write_bytes(raw)
    root = tmp_path / "workspace"
    bootmodel.unpack(p, root)
    value = json.loads((root / "model/image.json").read_text())
    part = next(s for s in value["parts"] if s["name"] == "kernel")
    (root / part["file"]).write_bytes(b"KERNEL")
    with pytest.raises(SecError, match="Signed/AVB"):
        bootmodel.rebuild(root, tmp_path / "out")


def test_unknown_tail_resizing_refused(tmp_path):
    p = boot(tmp_path / "boot.img", newc(), b"kernel")
    p.write_bytes(p.read_bytes() + b"NONZERO")
    root = tmp_path / "workspace"
    bootmodel.unpack(p, root)
    value = json.loads((root / "model/image.json").read_text())
    part = next(s for s in value["parts"] if s["name"] == "kernel")
    (root / part["file"]).write_bytes(b"longer-kernel")
    with pytest.raises(SecError, match="trailing"):
        bootmodel.rebuild(root, tmp_path / "out")


def test_dtbo_shared_blob_canonical_pack_and_roundtrip(tmp_path):
    raw = images.dtbo()
    value = dtbo_model.model(raw)
    value["entries"].append({**value["entries"][0], "index": 1, "id": 8})
    packed = dtbo_model.pack(value)
    parsed = dtbo(packed)
    assert parsed["entries"][0]["offset"] == parsed["entries"][1]["offset"]
    assert parsed["entries"][0]["id"] != parsed["entries"][1]["id"]
    p = tmp_path / "dtbo.img"
    p.write_bytes(packed)
    result = workflows.roundtrip(p, tmp_path / "workspace")
    assert result["semantic_equivalence"] == "SEMANTICALLY_EQUIVALENT"
    assert result["byte_identity"] == "BYTE_IDENTICAL"
    parsed = dtbo_model.model(packed)
    assert dtbo_model.pack(parsed) == packed


def test_dtb_canonical_model_and_comparison(tmp_path):
    p = tmp_path / "a.dtb"
    p.write_bytes(images.fdt())
    q = tmp_path / "b.dtb"
    q.write_bytes(p.read_bytes() + bytes(8))
    value = fdt(p.read_bytes(), canonical=True)
    assert value["model"] == "fdt" and value["header"]["version"] == 17
    assert all("sha256" in row for row in value["properties"])
    result = workflows.compare(p, q)
    assert result["byte_identity"] == "DIFFERENT"
    assert result["semantic_equivalence"] == "SEMANTICALLY_EQUIVALENT"


def test_roundtrip_temporary_workspace_discarded(tmp_path):
    p = boot(tmp_path / "boot.img", newc(), b"kernel")
    value = workflows.roundtrip(p)
    assert value["workspace"] == "TEMPORARY_DISCARDED"
    assert value["byte_identity"] == "BYTE_IDENTICAL"
