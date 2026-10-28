"""Compression structure and bounded native decoding are separate capabilities."""

from secripts.images.common import Reader
from secripts.images.ramdisk import compression as detect


def identify(data):
    kind = detect(data)
    if kind == "UNKNOWN" and len(data) >= 13 and data[:1] in (b"\x5d", b"\x6d"):
        dictionary = int.from_bytes(data[1:5], "little")
        if 4096 <= dictionary <= 64 * 1024**2:
            return "lzma-alone"
    if len(data) >= 4 and 0x184D2A50 <= int.from_bytes(data[:4], "little") <= 0x184D2A5F:
        return "lz4-skippable"
    return kind


def lz4(data):
    r = Reader(data)
    if len(data) < 4:
        raise ValueError("Truncated LZ4 magic")
    cursor = 0
    frames = []
    blocks = 0
    while cursor < len(data):
        if len(frames) >= 256:
            raise ValueError("LZ4 frame count limit")
        start = cursor
        magic = r.unpack("<I", cursor)[0]
        cursor += 4
        if 0x184D2A50 <= magic <= 0x184D2A5F:
            size = r.unpack("<I", cursor)[0]
            cursor += 4
            r.region(cursor, size)
            cursor += size
            frames.append({"kind": "skippable", "offset": start, "bytes": cursor - start})
            continue
        if magic == 0x184C2102:
            while cursor < len(data):
                size = r.unpack("<I", cursor)[0]
                cursor += 4
                if not size or size > 8 * 1024**2:
                    raise ValueError("Invalid legacy LZ4 block size")
                r.region(cursor, size)
                cursor += size
                blocks += 1
                if blocks > 20000:
                    raise ValueError("LZ4 block limit")
            frames.append({"kind": "legacy", "offset": start, "end_marker": "NOT_DEFINED"})
            break
        if magic != 0x184D2204:
            raise ValueError("Unexpected concatenated LZ4 magic")
        flags, bd = r.unpack("BB", cursor)
        cursor += 2
        if flags >> 6 != 1 or flags & 2 or bd & 0x8F:
            raise ValueError("Invalid LZ4 descriptor flags")
        maximum = {4: 65536, 5: 262144, 6: 1048576, 7: 4194304}.get((bd >> 4) & 7)
        if not maximum:
            raise ValueError("Invalid LZ4 block maximum")
        content = None
        dictionary = None
        if flags & 8:
            content = r.unpack("<Q", cursor)[0]
            cursor += 8
        if flags & 1:
            dictionary = r.unpack("<I", cursor)[0]
            cursor += 4
        header_checksum = r.region(cursor, 1).hex()
        cursor += 1
        sizes = []
        while True:
            size = r.unpack("<I", cursor)[0]
            cursor += 4
            if size == 0:
                break
            length = size & 0x7FFFFFFF
            if length == 0 or length > maximum:
                raise ValueError("Invalid LZ4 block bounds")
            r.region(cursor, length)
            cursor += length
            blocks += 1
            if blocks > 20000:
                raise ValueError("LZ4 block limit")
            sizes.append({"bytes": length, "uncompressed": bool(size & 0x80000000)})
            if flags & 16:
                r.region(cursor, 4)
                cursor += 4
        if flags & 4:
            r.region(cursor, 4)
            cursor += 4
        frames.append(
            {
                "kind": "frame",
                "offset": start,
                "bytes": cursor - start,
                "independent_blocks": bool(flags & 32),
                "block_checksum": bool(flags & 16),
                "content_checksum": bool(flags & 4),
                "content_size": content,
                "dictionary_id": dictionary,
                "header_checksum": header_checksum,
                "checksums_verified": "UNTESTED",
                "blocks": sizes[:256],
                "block_count": len(sizes),
                "end_marker": "OBSERVED",
            }
        )
        if len(frames) > 256:
            raise ValueError("LZ4 frame count limit")
    return {
        "format": identify(data),
        "structure_status": "PASS",
        "frames": frames,
        "block_count": blocks,
        "decompression": "UNSUPPORTED_NATIVE",
        "checksum_verification": "UNTESTED",
    }
