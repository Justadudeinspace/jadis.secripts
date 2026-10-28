"""Bounded, non-extracting compression and newc CPIO metadata inspection."""

import bz2
import lzma
from pathlib import PurePosixPath
import zlib

LIMIT = 16 * 1024 * 1024


def compression(data):
    for magic, name in (
        (b"\x1f\x8b", "gzip"),
        (b"\xfd7zXZ\x00", "xz"),
        (b"BZh", "bzip2"),
        (b"\x04\x22\x4d\x18", "lz4"),
        (b"\x02\x21\x4c\x18", "lz4-legacy"),
        (b"\x28\xb5\x2f\xfd", "zstd"),
        (b"070701", "cpio-newc"),
        (b"070702", "cpio-crc"),
    ):
        if data.startswith(magic):
            return name
    return "UNKNOWN"


def cpio_metadata(data):
    offset, count = 0, 0
    markers = set()
    unsafe = 0
    while offset + 110 <= len(data) and count < 20000:
        header = data[offset : offset + 110]
        if header[:6] not in (b"070701", b"070702"):
            raise ValueError("Unsupported/malformed CPIO header")
        size = int(header[54:62], 16)
        namesize = int(header[94:102], 16)
        if not 1 <= namesize <= 4096 or offset + 110 + namesize > len(data):
            raise ValueError("CPIO name bounds")
        raw = data[offset + 110 : offset + 110 + namesize]
        if raw[-1] != 0:
            raise ValueError("CPIO name lacks terminator")
        name = raw[:-1].decode("utf-8", errors="replace")
        body = (offset + 110 + namesize + 3) // 4 * 4
        if body + size > len(data):
            raise ValueError("CPIO payload bounds")
        if name == "TRAILER!!!":
            return {
                "status": "PASS",
                "entries": count,
                "markers": sorted(markers),
                "unsafe_paths": unsafe,
                "note": "Metadata only; CRC, file contents and device behavior not verified",
            }
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            unsafe += 1
        basename = path.name
        if basename in {"init", "recovery", "twrp", "prop.default"} or basename.startswith(
            "fstab."
        ):
            markers.add(basename if not basename.startswith("fstab.") else "fstab.*")
        count += 1
        offset = (body + size + 3) // 4 * 4
    raise ValueError("CPIO missing trailer or entry limit exceeded")


def inspect_ramdisk(data, declared_size, *, output_limit=None):
    cap = min(LIMIT, output_limit if output_limit is not None else LIMIT)
    kind = compression(data)
    result = {
        "compression": kind,
        "status": "UNRESOLVED",
        "declared_size": declared_size,
        "limit_bytes": cap,
        "extracted": False,
    }
    if not declared_size:
        return {**result, "status": "EMPTY"}
    if declared_size > LIMIT:
        return {**result, "reason": "Compressed region exceeds inspection limit"}
    try:
        if kind == "gzip":
            decoder = zlib.decompressobj(31)
            decoded = decoder.decompress(data, cap + 1)
        elif kind == "xz":
            decoder = lzma.LZMADecompressor(memlimit=64 * 1024 * 1024)
            decoded = decoder.decompress(data, max_length=cap + 1)
        elif kind == "bzip2":
            decoder = bz2.BZ2Decompressor()
            decoded = decoder.decompress(data, max_length=cap + 1)
        elif kind in ("cpio-newc", "cpio-crc"):
            decoder = None
            decoded = data
        else:
            return {
                **result,
                "reason": "Native decompressor unavailable or format unknown; no external tools executed",
            }
        if len(decoded) > cap:
            raise ValueError("Decompressed ramdisk exceeds output limit")
        if decoder is not None and not decoder.eof:
            raise ValueError("Truncated compressed ramdisk")
        metadata = cpio_metadata(decoded)
        return {
            **result,
            "status": "PASS",
            "decompressed_bytes": len(decoded),
            "cpio": metadata,
            "trailing_compressed_data": bool(decoder and decoder.unused_data),
        }
    except (ValueError, OSError, EOFError, zlib.error, lzma.LZMAError) as exc:
        return {**result, "status": "FAIL", "reason": str(exc)}
