import hashlib
import random
import stat
import struct
import pytest

from secripts.images import codecs, cpio, lz4codec, dtbo_model
from secripts.images.devicetree import dtbo, fdt
from secripts.images.artifacts import NewWorkspace, exclusive
from secripts.cli import main
from secripts.safety import SecError
from tests.fixtures import images
from tests.unit.test_phase4_codecs import cpio_model


@pytest.mark.parametrize("code,kind", [(1, "zlib"), (2, "gzip")])
def test_dtbo_v1_compressed_roundtrip(code, kind, tmp_path):
    value = dtbo_model.model(images.dtbo())
    value["version"] = 1
    value["entries"][0]["custom"] = [code, 7, 8, 9]
    value["entries"][0]["payload"] = codecs.encode(images.fdt(), kind)
    raw = dtbo_model.pack(value)
    parsed = dtbo(raw)
    assert parsed["structure_status"] == "PASS"
    assert parsed["entries"][0]["flags"] == code
    assert parsed["entries"][0]["compression_status"] == "CHECKSUM_VERIFIED_BY_STDLIB"
    assert parsed["entries"][0]["device_tree"]["format"] == "FDT"
    assert dtbo_model.pack(dtbo_model.model(raw)) == raw
    bad = bytearray(raw)
    bad[-1] ^= 255
    with pytest.raises(ValueError):
        dtbo(bytes(bad))


def test_unknown_dtbo_compression_and_extended_model_refusal():
    value = bytearray(images.dtbo())
    struct.pack_into(">I", value, 28, 1)
    struct.pack_into(">I", value, 48, 3)
    parsed = dtbo(bytes(value))
    assert parsed["structure_status"] == "PARTIAL"
    assert parsed["entries"][0]["device_tree"]["format"] == "COMPRESSED_ENTRY_UNSUPPORTED"
    model = dtbo_model.model(images.dtbo())
    model["entry_size"] = 64
    with pytest.raises(ValueError, match="Extended"):
        dtbo_model.pack(model)


def test_shared_dtbo_blob_no_extraction_amplification(tmp_path):
    value = dtbo_model.model(images.dtbo())
    value["entries"] = [{**value["entries"][0], "index": i} for i in range(100)]
    raw = dtbo_model.pack(value)
    source = tmp_path / "dtbo.img"
    source.write_bytes(raw)
    output = tmp_path / "workspace"
    dtbo_model.extract(source, output)
    assert len(list((output / "extracted").glob("*"))) == 1
    rebuilt = tmp_path / "rebuilt.img"
    dtbo_model.rebuild(output, rebuilt)
    assert raw == rebuilt.read_bytes()


def test_lz4_dependent_blocks_and_long_matches():
    # Dependent second block references previous uncompressed block history.
    descriptor = bytes([0x40, 0x40])
    header = b"\x04\x22\x4d\x18" + descriptor + bytes([(lz4codec.xxh32(descriptor) >> 8) & 255])
    first = b"abcd"
    second = b"\x08\x04\0\x50TAIL!"
    raw = (
        header
        + struct.pack("<I", 0x80000004)
        + first
        + struct.pack("<I", len(second))
        + second
        + bytes(4)
    )
    assert lz4codec.decode(raw)[0] == b"abcd" * 4 + b"TAIL!"
    # A zero distance is forbidden even when output space remains.
    with pytest.raises(ValueError, match="distance"):
        lz4codec.block_decode(b"\x10a\0\0")
    block = b"\x1fA\x01\0\xff\xff\xff\xff\x00"
    with pytest.raises(ValueError, match="limit"):
        lz4codec.block_decode(block, limit=16)


@pytest.mark.parametrize(
    "magic",
    [
        b"ANDROID!",
        b"VNDRBOOT",
        b"\xd7\xb7\xab\x1e",
        b"\xd0\x0d\xfe\xed",
        b"AVB0",
        b"070701",
        b"\x04\x22\x4d\x18",
    ],
)
def test_deterministic_malformed_cli_no_traceback(magic, tmp_path, capsys):
    rng = random.Random(404)  # noqa: S311 -- deterministic malformed fixtures, no security randomness
    path = tmp_path / "artifact"
    for size in (0, 1, 8, 64, 256):
        path.write_bytes(magic + rng.randbytes(size))
        code = main(["insp", str(path), "--json"])
        output = capsys.readouterr()
        assert code in (0, 1, 3, 4, 5)
        assert "Traceback" not in output.out + output.err


def test_corrupt_lz4_reports_failure_not_verified(tmp_path, capsys):
    data = bytearray(lz4codec.encode(b"hello"))
    data[-1] ^= 1
    path = tmp_path / "ramdisk.lz4"
    path.write_bytes(data)
    assert main(["insp", str(path), "--json"]) == 1
    output = capsys.readouterr().out
    assert "CHECKSUM_OR_DECODE_FAILED" in output and "CHECKSUM_FAILED" in output


def test_workspace_creation_is_exclusive_and_cleanup(tmp_path):
    target = tmp_path / "workspace"
    with pytest.raises(ValueError):
        with NewWorkspace(target):
            raise ValueError("deliberate failure")
    assert not target.exists()
    with NewWorkspace(target) as root:
        exclusive(root / "extracted/part.bin", b"fixture")
    with pytest.raises(SecError):
        with NewWorkspace(target):
            pass
    with pytest.raises(SecError):
        exclusive(target / "extracted/part.bin", b"overwrite")


def test_ramdisk_owner_mode_symlink_order_comparison():
    from secripts.images.comparison import ramdisks

    first = cpio_model(payload=b"first")
    second = cpio_model(payload=b"second")
    second["entries"][0].update(uid=99, gid=98, mode=stat.S_IFREG | 0o600)
    value = ramdisks(cpio.pack(first), cpio.pack(second))
    changes = {d["interpretation"] for d in value["differences"]}
    assert {"OWNER_CHANGED", "MODE_CHANGED", "CONTENT_CHANGED"} <= changes
    assert value["semantic_equivalence"] == "DIFFERENT"


def test_aosp_oracle_refuses_unreviewed_source(tmp_path):
    from secripts.images.oracles import PINNED, aosp

    root = tmp_path / "provider"
    root.mkdir()
    for filename in PINNED:
        path = root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"not reviewed upstream code")
    with pytest.raises(SecError, match="hash mismatch"):
        aosp(tmp_path / "image", root)


def test_fit_embedded_hash_and_signature_metadata():
    # Minimal synthetic FIT assembled independently from FDT wire tokens.
    payload = b"synthetic kernel"
    expected = hashlib.sha256(payload).digest()
    names = ["data", "algo", "value", "kernel"]
    strings = b"".join(n.encode() + b"\0" for n in names)
    indexes = {name: strings.index(name.encode() + b"\0") for name in names}

    def node(name):
        value = struct.pack(">I", 1) + name.encode() + b"\0"
        return value + bytes((-len(value)) % 4)

    def prop(name, value):
        raw = struct.pack(">III", 3, len(value), indexes[name]) + value
        return raw + bytes((-len(raw)) % 4)

    end = struct.pack(">I", 2)
    structure = (
        node("")
        + node("images")
        + node("kernel")
        + prop("data", payload)
        + node("hash-1")
        + prop("algo", b"sha256\0")
        + prop("value", expected)
        + end
        + node("signature-1")
        + prop("algo", b"sha256,rsa2048\0")
        + end
        + end
        + end
    )
    structure += (
        node("configurations")
        + node("default")
        + prop("kernel", b"kernel\0")
        + end
        + end
        + end
        + struct.pack(">I", 9)
    )
    start = 56
    string_start = start + len(structure)
    total = string_start + len(strings)
    raw = (
        struct.pack(
            ">10I",
            0xD00DFEED,
            total,
            start,
            string_start,
            40,
            17,
            16,
            0,
            len(strings),
            len(structure),
        )
        + bytes(16)
        + structure
        + strings
    )
    value = fdt(raw)
    assert value["format"] == "UBOOT_FIT"
    assert value["fit"]["images"][0]["hashes"][0]["state"] == "HASH_MATCHED"
    assert value["fit"]["images"][0]["signatures"][0]["state"] == "SIGNATURE_UNVERIFIED"
    assert value["fit"]["configurations"][0]["missing_references"] == []


def test_bounded_receipt_evidence_preserves_identity(tmp_path):
    from secripts.receipts import save, load

    receipt = save(
        "image.compare",
        "READ_ONLY",
        [],
        result="PASS",
        data={
            "status": "PARTIAL",
            "original_sha256": "a" * 64,
            "rebuilt_sha256": "b" * 64,
            "rows": [{"long": "x" * 4096} for _ in range(1000)],
        },
    )
    restored = load(receipt["receipt_id"])
    assert restored["operation"] == "image.compare"
    assert restored["data"]["status"] == "PARTIAL"
    assert restored["data"]["original_sha256"] == "a" * 64
    assert restored["warnings"] and len(str(restored)) < 180000


def test_fdt_path_budget_and_uimage_crc_failure(tmp_path, capsys):
    from secripts.images.common import Reader

    with pytest.raises(ValueError):
        Reader(b"\xff\0").string(0, 2)

    def node(name):
        value = struct.pack(">I", 1) + name + b"\0"
        return value + bytes((-len(value)) % 4)

    structure = (
        node(b"")
        + node(b"a" * 2000)
        + node(b"b" * 2000)
        + node(b"c" * 2000)
        + struct.pack(">5I", 2, 2, 2, 2, 9)
    )
    total = 56 + len(structure)
    raw = (
        struct.pack(">10I", 0xD00DFEED, total, 56, total, 40, 17, 16, 0, 0, len(structure))
        + bytes(16)
        + structure
    )
    with pytest.raises(ValueError, match="path length"):
        fdt(raw)
    bad = bytearray(images.uimage())
    bad[-1] ^= 1
    path = tmp_path / "image"
    path.write_bytes(bad)
    assert main(["insp", str(path), "--json"]) == 1
    assert '"data_crc": "FAIL"' in capsys.readouterr().out


def test_image_compressed_representation_can_be_semantically_equal(tmp_path):
    import gzip
    from tests.unit.test_image_phase2 import boot, newc
    from secripts.images.bootmodel import compare

    first = boot(tmp_path / "a.img", gzip.compress(newc(), mtime=0), b"kernel")
    second = boot(tmp_path / "b.img", gzip.compress(newc(), mtime=42), b"kernel")
    value = compare(first, second)
    assert value["byte_identity"] == "DIFFERENT"
    assert value["semantic_equivalence"] == "SEMANTICALLY_EQUIVALENT"
    assert any(d["classification"] == "COMPRESSION" for d in value["differences"])
