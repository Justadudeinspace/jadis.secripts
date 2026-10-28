"""Synthetic image structures are test evidence only, never real boot artifacts."""

import bz2
import gzip
import lzma
import struct
import pytest
from secripts.recovery.inspection import inspect_image, audit_tree
from secripts.recovery.ramdisk import inspect_ramdisk
from secripts.safety import SecError


def newc(name="init", payload=b"fixture"):
    def entry(name, payload):
        name = name.encode() + b"\0"
        fields = [0, 0o100644, 0, 0, 1, 0, len(payload), 0, 0, 0, 0, len(name), 0]
        value = b"070701" + b"".join(f"{field:08x}".encode() for field in fields) + name
        value += b"\0" * ((-len(value)) % 4)
        value += payload
        value += b"\0" * ((-len(value)) % 4)
        return value

    return entry(name, payload) + entry("TRAILER!!!", b"")


def boot(path, ramdisk=b"", kernel=b"", version=4):
    header = bytearray(4096)
    header[:8] = b"ANDROID!"
    struct.pack_into("<I", header, 40, version)
    struct.pack_into("<I", header, 20, 1584 if version == 4 else 1580)
    struct.pack_into("<II", header, 8, len(kernel), len(ramdisk))
    data = (
        bytes(header)
        + kernel
        + b"\0" * ((-len(kernel)) % 4096)
        + ramdisk
        + b"\0" * ((-len(ramdisk)) % 4096)
    )
    path.write_bytes(data)
    return path


@pytest.mark.parametrize("compress", [gzip.compress, bz2.compress, lzma.compress, lambda x: x])
def test_ramdisk_metadata_and_init_boot_candidate(tmp_path, compress):
    p = boot(tmp_path / "init_boot.img", compress(newc()))
    value = inspect_image(p)
    assert value["role"] == {"value": "INIT_BOOT_CANDIDATE", "state": "INFERRED"}
    assert value["sections"]["ramdisk"]["inspection"]["cpio"]["markers"] == ["init"]
    assert value["device_compatibility"] == "UNTESTED" and value["bootability"] == "UNTESTED"
    assert value["avb"]["signature_verification"] == "UNTESTED"


def test_ramdisk_bomb_truncation_and_cpio_traversal(monkeypatch):
    import secripts.recovery.ramdisk as r

    monkeypatch.setattr(r, "LIMIT", 1024)
    data = gzip.compress(b"x" * 2000)
    assert inspect_ramdisk(data, len(data))["status"] == "FAIL"
    assert inspect_ramdisk(b"\x1f\x8b", 2)["status"] == "FAIL"
    data = newc("../unsafe")
    assert inspect_ramdisk(data, len(data))["cpio"]["unsafe_paths"] == 1
    assert inspect_ramdisk(b"\x04\x22\x4d\x18", 4)["status"] == "FAIL"


def test_boot_payload_and_header_bounds(tmp_path):
    p = boot(tmp_path / "boot.img", gzip.compress(newc()), b"kernel")
    value = inspect_image(p)
    assert value["sections"]["kernel"]["offset"] == 4096
    assert value["sections"]["ramdisk"]["offset"] == 8192
    header = bytearray(p.read_bytes())
    struct.pack_into("<I", header, 20, 0)
    p.write_bytes(header)
    with pytest.raises(SecError, match="header size"):
        inspect_image(p)
    p.write_bytes(b"ANDROID!")
    with pytest.raises(SecError, match="Truncated"):
        inspect_image(p)


def test_vendor_fragments_and_overlap(tmp_path):
    rd = gzip.compress(newc())
    page = 4096
    header = bytearray(page)
    header[:8] = b"VNDRBOOT"
    struct.pack_into("<II", header, 8, 4, page)
    struct.pack_into("<I", header, 24, len(rd))
    struct.pack_into("<I", header, 2096, 2128)
    struct.pack_into("<IIII", header, 2112, 108, 1, 108, 0)
    entry = bytearray(page)
    struct.pack_into("<III", entry, 0, len(rd), 0, 2)
    entry[12:20] = b"recovery"
    p = tmp_path / "vendor_boot.img"
    p.write_bytes(header + rd + b"\0" * (page - len(rd)) + entry)
    value = inspect_image(p)
    assert value["properties"]["fragments"][0]["type"] == 2
    assert value["sections"]["fragment_0"]["inspection"]["status"] == "PASS"
    entry = bytearray(entry)
    struct.pack_into("<I", entry, 0, len(rd) + 1)
    p.write_bytes(header + rd + b"\0" * (page - len(rd)) + entry)
    with pytest.raises(SecError, match="fragment bounds"):
        inspect_image(p)


def vbmeta():
    header = bytearray(256)
    header[:4] = b"AVB0"
    struct.pack_into(">II", header, 4, 1, 0)
    struct.pack_into(">I", header, 28, 1)
    struct.pack_into(">Q", header, 112, 42)
    return header


def test_avb_footer_and_vbmeta_are_not_verification(tmp_path):
    p = tmp_path / "vbmeta.img"
    p.write_bytes(vbmeta())
    value = inspect_image(p)
    assert value["avb"]["algorithm"] == "SHA256_RSA2048"
    assert value["avb"]["rollback_index"] == 42
    assert value["avb"]["signature_verification"] == "UNTESTED"
    footer = bytearray(64)
    footer[:4] = b"AVBf"
    struct.pack_into(">IIQQQ", footer, 4, 1, 0, 4096, 4096, 256)
    p = boot(tmp_path / "boot.img")
    p.write_bytes(p.read_bytes() + vbmeta() + footer)
    assert inspect_image(p)["avb"]["detected"] is True
    struct.pack_into(">Q", footer, 20, 999999)
    p.write_bytes(p.read_bytes()[:-64] + footer)
    assert inspect_image(p)["avb"]["status"] == "FAIL"


def test_avb_hash_descriptor_and_bad_bounds(tmp_path):
    header = vbmeta()
    descriptor = bytearray(136)
    struct.pack_into(">QQQ", descriptor, 0, 2, 120, 8192)
    descriptor[24:30] = b"sha256"
    struct.pack_into(">III", descriptor, 56, 4, 0, 0)
    descriptor[132:136] = b"boot"
    struct.pack_into(">Q", header, 20, 192)
    struct.pack_into(">QQ", header, 96, 0, 136)
    p = tmp_path / "vbmeta.img"
    p.write_bytes(header + descriptor + bytes(56))
    assert inspect_image(p)["avb"]["descriptors"][0]["partition"] == "boot"
    struct.pack_into(">Q", header, 104, 99999)
    p.write_bytes(header + descriptor + bytes(56))
    assert inspect_image(p)["avb"]["status"] == "FAIL"


def test_tree_dependency_graph_and_conditional_evidence(tmp_path):
    (tmp_path / "BoardConfig.mk").write_text(
        "TARGET_ARCH := arm64\ninclude $(LOCAL_DIR)/common.mk\nBOARD_AVB_ENABLE := true\nPRODUCT_VIRTUAL_AB_OTA := true\nTARGET_KERNEL_SOURCE := kernel/vendor/example\n"
    )
    (tmp_path / "common.mk").write_text(
        "include $(LOCAL_DIR)/BoardConfig.mk\nifeq ($(MODE),yes)\nTW_INCLUDE_CRYPTO_FBE := true\nendif\n"
    )
    (tmp_path / "AndroidProducts.mk").write_text(
        "PRODUCT_MAKEFILES := $(LOCAL_DIR)/twrp_example.mk\n"
    )
    (tmp_path / "twrp_example.mk").write_text("$(call inherit-product, $(LOCAL_DIR)/common.mk)\n")
    (tmp_path / "manifest.xml").write_text(
        '<manifest><project path="device/vendor/common" revision="pinned"/></manifest>'
    )
    value = audit_tree(tmp_path)
    g = value["dependency_graph"]
    assert any(e["state"] == "STATICALLY_RESOLVED" and e["kind"] == "product" for e in g["edges"])
    assert any(e["state"] == "EXTERNALLY_DEPENDENT" for e in g["edges"])
    assert g["cycles"] and not g["complete"]
    assert g["groups"]["encryption"][0]["state"] == "UNRESOLVED"
    assert value["hardware"] == "UNTESTED"


def test_tree_symlink_huge_file_and_xml_entities(tmp_path):
    (tmp_path / "BoardConfig.mk").write_text("TARGET_ARCH := arm64\n")
    (tmp_path / "huge.mk").write_bytes(b"x" * (1024 * 1024 + 1))
    (tmp_path / "linked.mk").symlink_to("/etc/passwd")
    (tmp_path / "manifest.xml").write_text(
        '<!DOCTYPE manifest [<!ENTITY x "boom">]><manifest>&x;</manifest>'
    )
    value = audit_tree(tmp_path)
    assert any(f["check"] == "symlink" for f in value["findings"])
    assert any(f["check"] == "oversize file" for f in value["findings"])
    assert value["dependency_graph"]["warnings"][0]["reason"] == "DTD/entities refused"
    assert "huge.mk" not in value["configuration_hashes"]


def test_combined_report_separates_evidence(tmp_path):
    from secripts.recovery.qualification import report, markdown

    p = boot(tmp_path / "boot.img", gzip.compress(newc()))
    value = report(p)
    assert value["evidence_states"]["build"] == "UNTESTED"
    assert value["evidence_states"]["image_structure"] == "PASS"
    assert value["evidence_states"]["device_qualified"] == "UNTESTED"
    assert value["blockers"] and value["device_evidence_origin"] == "NOT_COLLECTED"
    assert "Separate evidence states" in markdown(value)
    bad = tmp_path / "bad.json"
    bad.write_text("{}")
    with pytest.raises(SecError):
        report(p, device_evidence=bad)
