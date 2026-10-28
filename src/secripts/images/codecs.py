"""One bounded compression pipeline shared by inspection and reconstruction."""

import bz2
import lzma
import struct
import zlib
from secripts.images.common import Reader
from secripts.images.compression import identify
from secripts.images import lz4codec

CAP = 32 * 1024**2


def detect(data):
    kind = identify(data)
    if kind == "UNKNOWN" and len(data) >= 2:
        cmf, flg = data[:2]
        if cmf & 15 == 8 and cmf >> 4 <= 7 and (cmf * 256 + flg) % 31 == 0:
            return "zlib"
    return kind


def gzip_header(data):
    r = Reader(data)
    if r.region(0, 3) != b"\x1f\x8b\x08":
        raise ValueError("Invalid gzip header")
    flags = r.region(3, 1)[0]
    if flags & 0xE0:
        raise ValueError("Reserved gzip flags")
    cursor = 10
    r.region(0, cursor)
    if flags & 4:
        length = r.unpack("<H", cursor)[0]
        cursor += 2
        r.region(cursor, length)
        cursor += length
    for bit in (8, 16):
        if flags & bit:
            end = data.find(b"\0", cursor, min(len(data), cursor + 4097))
            if end < 0:
                raise ValueError("Unterminated/excessive gzip name/comment")
            cursor = end + 1
    if flags & 2:
        if zlib.crc32(data[:cursor]) & 0xFFFF != r.unpack("<H", cursor)[0]:
            raise ValueError("CHECKSUM_FAILED: gzip header")
        cursor += 2
    return {
        "flags": flags,
        "mtime": r.unpack("<I", 4)[0],
        "xfl": data[8],
        "os": data[9],
        "header_bytes": cursor,
        "optional_fields": "PRESENT" if flags else "ABSENT",
    }


def _decode(data, kind=None, limit=CAP):
    if len(data) > CAP or not 0 <= limit <= CAP:
        raise ValueError("Compression input/output limit")
    kind = kind or detect(data)
    if kind.startswith("lz4"):
        return lz4codec.decode(data, limit)
    if kind in {"cpio-newc", "cpio-crc", "none"}:
        if len(data) > limit:
            raise ValueError("Output limit")
        return data, {"schema": 1, "codec": "none", "status": "PASS", "checksum": "CHECKSUM_ABSENT"}
    if kind not in {"gzip", "zlib", "raw-deflate", "xz", "lzma-alone", "bzip2"}:
        raise ValueError("UNSUPPORTED_COMPRESSION")
    remaining = data
    output = bytearray()
    members = []
    while remaining:
        if len(members) >= 256:
            raise ValueError("Compressed member count limit")
        metadata = gzip_header(remaining) if kind == "gzip" else {}
        if kind in {"gzip", "zlib", "raw-deflate"}:
            if kind == "zlib" and len(remaining) < 2:
                raise ValueError("Truncated zlib header")
            if kind == "zlib" and remaining[1] & 32:
                raise lz4codec.DictionaryRequired("BLOCKED_MISSING_DICTIONARY")
            decoder = zlib.decompressobj({"gzip": 31, "zlib": 15, "raw-deflate": -15}[kind])
            decoded = decoder.decompress(remaining, limit - len(output) + 1)
        elif kind in {"xz", "lzma-alone"}:
            decoder = lzma.LZMADecompressor(
                format=lzma.FORMAT_XZ if kind == "xz" else lzma.FORMAT_ALONE, memlimit=64 * 1024**2
            )
            decoded = decoder.decompress(remaining, max_length=limit - len(output) + 1)
        else:
            decoder = bz2.BZ2Decompressor()
            decoded = decoder.decompress(remaining, max_length=limit - len(output) + 1)
        if len(decoded) + len(output) > limit:
            raise ValueError("Decompression output limit")
        if not decoder.eof:
            raise ValueError("Truncated compressed stream")
        consumed = len(remaining) - len(decoder.unused_data)
        if consumed <= 0:
            raise ValueError("Non-progressing decompression")
        members.append({"input_bytes": consumed, "output_bytes": len(decoded), **metadata})
        output.extend(decoded)
        remaining = decoder.unused_data
        if kind == "gzip":
            remaining = remaining.lstrip(b"\0")
        if remaining and kind in {"zlib", "raw-deflate", "lzma-alone"}:
            raise ValueError("Unexpected trailing compressed data")
    if not members:
        raise ValueError("Missing compressed stream")
    return bytes(output), {
        "schema": 1,
        "codec": kind,
        "status": "PASS",
        "members": members,
        "checksum": "CHECKSUM_ABSENT"
        if kind in {"raw-deflate", "lzma-alone"}
        else "CHECKSUM_VERIFIED_BY_STDLIB",
    }


def encode(data, kind="gzip"):
    if len(data) > CAP:
        raise ValueError("Compression input limit")
    if kind in {"none", "cpio-newc", "cpio-crc"}:
        return data
    if kind == "lz4":
        return lz4codec.encode(data)
    if kind == "gzip":
        compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
        payload = compressor.compress(data) + compressor.flush()
        return (
            b"\x1f\x8b\x08\0\0\0\0\0\x02\xff"
            + payload
            + struct.pack("<II", zlib.crc32(data), len(data))
        )
    if kind == "zlib":
        return zlib.compress(data, 9)
    if kind == "raw-deflate":
        compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
        return compressor.compress(data) + compressor.flush()
    if kind == "xz":
        return lzma.compress(data, format=lzma.FORMAT_XZ, preset=6)
    if kind == "lzma-alone":
        return lzma.compress(data, format=lzma.FORMAT_ALONE, preset=6)
    if kind == "bzip2":
        return bz2.compress(data)
    raise ValueError("Unsupported encoder")


def decode(data, kind=None, limit=CAP):
    try:
        return _decode(data, kind, limit)
    except (zlib.error, lzma.LZMAError, OSError, EOFError) as exc:
        raise ValueError("Compressed stream refused: " + str(exc)) from exc
