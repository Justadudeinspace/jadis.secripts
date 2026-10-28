import gzip
import io
import json
from pathlib import Path
import stat
import struct
import zlib

import pytest

from secripts.images import lz4codec, codecs, cpio, ramdisk_model
from secripts.images.comparison import ramdisks
from secripts.safety import SecError


@pytest.mark.parametrize(
    "data,expected",
    [(b"", 0x02CC5D05), (b"a", 0x550D7456), (b"abc", 0x32D153FF), (b"hello", 0xFB0077F9)],
)
def test_xxh32_reference_vectors(data, expected):
    assert lz4codec.xxh32(data) == expected


@pytest.mark.parametrize("size", [0, 1, 15, 16, 255, 65535, 65536, 65537])
def test_lz4_deterministic_frame_roundtrip(size):
    data = (b"JADIS\0" * ((size + 5) // 6))[:size]
    encoded = lz4codec.encode(data)
    decoded, evidence = lz4codec.decode(encoded)
    assert decoded == data and lz4codec.encode(data) == encoded
    assert evidence["frames"][0]["content"] == "CONTENT_CHECKSUM_VERIFIED"
    assert evidence["frames"][0]["header"] == "HEADER_CHECKSUM_VERIFIED"


def compressed_frame(block, decoded, flags=0x7C, dictionary=None):
    descriptor = bytes([flags, 0x40]) + struct.pack("<Q", len(decoded))
    if dictionary is not None:
        descriptor += struct.pack("<I", dictionary)
    header = b"\x04\x22\x4d\x18" + descriptor + bytes([(lz4codec.xxh32(descriptor) >> 8) & 255])
    return (
        header
        + struct.pack("<I", len(block))
        + block
        + struct.pack("<I", lz4codec.xxh32(block))
        + bytes(4)
        + struct.pack("<I", lz4codec.xxh32(decoded))
    )


def test_lz4_compressed_match_overlap_and_checksums():
    block = b"\x48abcd\x04\0\x50TAIL!"
    content = b"abcd" * 4 + b"TAIL!"
    frame = compressed_frame(block, content)
    assert lz4codec.block_decode(block) == content
    assert lz4codec.decode(frame)[0] == content
    for offset in (14, 20, len(frame) - 1):
        bad = bytearray(frame)
        bad[offset] ^= 1
        with pytest.raises(ValueError):
            lz4codec.decode(bytes(bad))
    with pytest.raises(ValueError, match="distance"):
        lz4codec.block_decode(b"\x00\0\0")
    with pytest.raises(ValueError, match="literal"):
        lz4codec.block_decode(b"\x10a\x01\0")
    with pytest.raises(ValueError, match="limit"):
        lz4codec.block_decode(block, limit=8)
    with pytest.raises(lz4codec.DictionaryRequired, match="MISSING_DICTIONARY"):
        lz4codec.decode(compressed_frame(block, content, flags=0x7D, dictionary=99))
    with pytest.raises(ValueError):
        lz4codec.decode(frame[:-1])


def test_lz4_concatenation_skippable_legacy_and_limits():
    skipped = struct.pack("<II", 0x184D2A50, 3) + b"abc"
    assert lz4codec.decode(skipped + lz4codec.encode(b"a") + lz4codec.encode(b"b"))[0] == b"ab"
    block = b"\x30abc"
    legacy = struct.pack("<II", 0x184C2102, len(block)) + block
    assert lz4codec.decode(legacy)[0] == b"abc"
    with pytest.raises(ValueError, match="count"):
        lz4codec.decode(struct.pack("<II", 0x184D2A50, 0) * 257)
    with pytest.raises(ValueError, match="limit"):
        lz4codec.decode(lz4codec.encode(b"ab"), limit=1)


@pytest.mark.parametrize(
    "kind", ["gzip", "zlib", "raw-deflate", "xz", "lzma-alone", "bzip2", "lz4", "none"]
)
@pytest.mark.parametrize("data", [b"", b"init\0" * 32])
def test_codec_roundtrip(kind, data):
    encoded = codecs.encode(data, kind)
    decoded, _ = codecs.decode(encoded, kind)
    assert decoded == data
    assert encoded == codecs.encode(data, kind)


def test_gzip_concat_headers_crc_and_bombs():
    a = codecs.encode(b"one", "gzip")
    b = codecs.encode(b"two", "gzip")
    decoded, metadata = codecs.decode(a + bytes(4) + b)
    assert decoded == b"onetwo" and len(metadata["members"]) == 2
    stream = io.BytesIO()
    with gzip.GzipFile(filename="synthetic", mode="wb", fileobj=stream, mtime=123) as handle:
        handle.write(b"hello")
    assert codecs.decode(stream.getvalue())[1]["members"][0]["mtime"] == 123
    for raw in (a[:-1], a[:-8] + bytes(8), b"\x1f\x8b\x08\xe0" + bytes(10)):
        with pytest.raises(ValueError):
            codecs.decode(raw)
    with pytest.raises(ValueError, match="limit"):
        codecs.decode(codecs.encode(b"a" * 1024, "gzip"), limit=20)
    assert zlib.decompress(codecs.encode(b"a", "gzip"), 31) == b"a"


def cpio_model(variant="070701", path="init", payload=b"fixture"):
    entry = dict.fromkeys(cpio.FIELDS, 0)
    entry.update(
        ino=1,
        mode=stat.S_IFREG | 0o755,
        uid=12,
        gid=34,
        nlink=1,
        mtime=123,
        path=path,
        type="file",
        format=variant,
        archive=0,
        payload=payload,
    )
    return {"schema": 1, "model": "ramdisk-cpio", "entries": [entry]}


@pytest.mark.parametrize("variant", ["070701", "070702"])
def test_cpio_model_pack_invariant(variant):
    value = cpio_model(variant)
    packed = cpio.pack(value)
    parsed = cpio.parse(packed)
    assert cpio.pack(parsed) == packed
    entry = parsed["entries"][0]
    for field in ("mode", "uid", "gid", "mtime", "ino", "nlink", "path", "payload", "format"):
        assert entry[field] == value["entries"][0][field]
    assert parsed["entries"][0]["extraction_safety"] == "VIRTUAL_ONLY"
    if variant == "070702":
        bad = bytearray(packed)
        bad[entry["payload_offset"]] ^= 1
        with pytest.raises(ValueError, match="CHECKSUM_FAILED"):
            cpio.parse(bytes(bad))


@pytest.mark.parametrize("path", ["../escape", "/absolute", "a/../../b", "C:/windows", "bad\\path"])
def test_cpio_unsafe_pack_refused(path):
    with pytest.raises(ValueError, match="Unsafe"):
        cpio.pack(cpio_model(path=path))


def test_cpio_concatenation_symlinks_and_special_metadata(tmp_path):
    first = cpio.pack(cpio_model())
    second = cpio_model(path="link", payload=b"/etc/shadow")
    second["entries"][0].update(type="symlink", mode=stat.S_IFLNK | 0o777)
    data = first + bytes(4) + cpio.pack(second)
    parsed = cpio.parse(data)
    assert parsed["entries"][1]["archive"] == 1
    assert parsed["entries"][1]["symlink_target"] == "/etc/shadow"
    p = tmp_path / "ramdisk"
    p.write_bytes(data)
    target = tmp_path / "workspace"
    ramdisk_model.extract(p, target)
    assert not any(x.is_symlink() for x in target.rglob("*"))
    assert not (target / "etc/shadow").exists()
    output = tmp_path / "rebuilt"
    ramdisk_model.pack(target, output)
    assert ramdisks(data, output.read_bytes())["semantic_equivalence"] == "SEMANTICALLY_EQUIVALENT"


def test_ramdisk_workspace_source_immutability_and_symlink_attack(tmp_path):
    p = tmp_path / "input"
    p.write_bytes(codecs.encode(cpio.pack(cpio_model()), "lz4"))
    target = tmp_path / "workspace"
    ramdisk_model.extract(p, target)
    payload = target / "extracted/entry-00000.bin"
    payload.unlink()
    payload.symlink_to("/etc/passwd")
    with pytest.raises(SecError, match="Symlink"):
        ramdisk_model.pack(target, tmp_path / "output")
    payload.unlink()
    payload.write_bytes(b"fixture")
    source = target / "source/artifact.bin"
    source.chmod(0o600)
    source.write_bytes(b"changed")
    with pytest.raises(SecError, match="snapshot"):
        ramdisk_model.pack(target, tmp_path / "output")


def test_ramdisk_directory_pack_compare_changes(tmp_path):
    root = tmp_path / "files"
    root.mkdir()
    (root / "init").write_bytes(b"hello")
    p = tmp_path / "a"
    q = tmp_path / "b"
    ramdisk_model.pack(root, p, compression="gzip")
    (root / "init").write_bytes(b"changed")
    ramdisk_model.pack(root, q, compression="lz4")
    value = ramdisks(p.read_bytes(), q.read_bytes())
    assert value["semantic_equivalence"] == "DIFFERENT"
    assert {d["interpretation"] for d in value["differences"]} >= {
        "CONTENT_CHANGED",
        "COMPRESSION_CHANGED",
    }
    assert value["device_compatibility"] == "UNTESTED"


def test_cpio_expected_failure_shapes(tmp_path):
    good = cpio.pack(cpio_model())
    for raw in (b"", good[:10], good[:109], b"070701" + b"x" * 104, good[:90]):
        with pytest.raises(ValueError):
            cpio.parse(raw)
    invalid = cpio_model()
    invalid["entries"][0]["uid"] = -1
    with pytest.raises(ValueError):
        cpio.pack(invalid)
    with pytest.raises(ValueError):
        cpio.pack({"schema": 99, "model": "ramdisk-cpio", "entries": []})
    sensitive = tmp_path / "sensitive"
    sensitive.write_bytes(cpio.pack(cpio_model(path="private.key")))
    with pytest.raises(SecError, match="Sensitive"):
        ramdisk_model.extract(sensitive, tmp_path / "out")


def test_ramdisk_metadata_is_payload_free(tmp_path):
    p = tmp_path / "input"
    p.write_bytes(cpio.pack(cpio_model(payload=b"UNIQUE_SYNTHETIC_BODY")))
    value = ramdisk_model.inspect(p)
    assert "UNIQUE_SYNTHETIC_BODY" not in json.dumps(value)
    assert Path(p).read_bytes().startswith(b"070701")
