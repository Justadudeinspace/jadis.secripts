"""Independent bounded LZ4/XXH32 implementation from upstream format specifications."""

import struct
from secripts.images.common import Reader

CAP = 32 * 1024**2
MASK = 0xFFFFFFFF
P1, P2, P3, P4, P5 = 2654435761, 2246822519, 3266489917, 668265263, 374761393


def rot(value, bits):
    value &= MASK
    return ((value << bits) | (value >> (32 - bits))) & MASK


def xxh32(data, seed=0):
    r = Reader(data)
    cursor = 0
    if len(data) >= 16:
        accumulators = [
            (seed + P1 + P2) & MASK,
            (seed + P2) & MASK,
            seed & MASK,
            (seed - P1) & MASK,
        ]
        while cursor + 16 <= len(data):
            for index, word in enumerate(r.unpack("<4I", cursor)):
                accumulators[index] = rot(accumulators[index] + word * P2, 13) * P1 & MASK
            cursor += 16
        result = sum(rot(v, b) for v, b in zip(accumulators, (1, 7, 12, 18), strict=True)) & MASK
    else:
        result = (seed + P5) & MASK
    result = (result + len(data)) & MASK
    while cursor + 4 <= len(data):
        result = rot(result + r.unpack("<I", cursor)[0] * P3, 17) * P4 & MASK
        cursor += 4
    for byte in data[cursor:]:
        result = rot(result + byte * P5, 11) * P1 & MASK
    result ^= result >> 15
    result = result * P2 & MASK
    result ^= result >> 13
    result = result * P3 & MASK
    return (result ^ (result >> 16)) & MASK


class DictionaryRequired(ValueError):
    pass


def block_decode(data, limit=CAP, history=b""):
    if len(data) > CAP or not 0 <= limit <= CAP:
        raise ValueError("LZ4 input/output limit")
    r = Reader(data)
    out = bytearray()
    cursor = 0
    last_match = None
    last_literals = 0
    ended_with_literals = False

    def extended(base):
        nonlocal cursor
        length = base
        if base == 15:
            while True:
                extra = r.region(cursor, 1)[0]
                cursor += 1
                length += extra
                if length > limit:
                    raise ValueError("LZ4 output limit")
                if extra != 255:
                    break
        return length

    while cursor < len(data):
        control = r.region(cursor, 1)[0]
        cursor += 1
        literal_size = extended(control >> 4)
        if len(out) + literal_size > limit:
            raise ValueError("LZ4 output limit")
        out.extend(r.region(cursor, literal_size))
        cursor += literal_size
        if cursor == len(data):
            last_literals = literal_size
            ended_with_literals = True
            break
        distance = r.unpack("<H", cursor)[0]
        cursor += 2
        size = extended(control & 15) + 4
        if distance == 0 or distance > len(history) + len(out):
            raise ValueError("LZ4 invalid match distance")
        if len(out) + size > limit:
            raise ValueError("LZ4 output limit")
        last_match = len(out)
        begin = len(history) + len(out) - distance
        take = min(distance, size)
        prior = history[begin : min(len(history), begin + take)] if begin < len(history) else b""
        out_begin = max(0, begin - len(history))
        prior += bytes(out[out_begin : out_begin + take - len(prior)])
        out.extend((prior * ((size + len(prior) - 1) // len(prior)))[:size])
    if not ended_with_literals:
        raise ValueError("LZ4 block must end in a literal sequence")
    if last_match is not None and (last_literals < 5 or last_match > len(out) - 12):
        raise ValueError("LZ4 final literal/match constraints")
    return bytes(out)


def decode(data, limit=CAP):
    if len(data) > CAP or not 0 <= limit <= CAP:
        raise ValueError("LZ4 input/output limit")
    r = Reader(data)
    cursor = 0
    out = bytearray()
    evidence = []
    while cursor < len(data):
        if len(evidence) >= 256:
            raise ValueError("LZ4 frame count limit")
        start = cursor
        magic = r.unpack("<I", cursor)[0]
        cursor += 4
        if 0x184D2A50 <= magic <= 0x184D2A5F:
            length = r.unpack("<I", cursor)[0]
            cursor += 4
            r.region(cursor, length)
            cursor += length
            evidence.append({"kind": "skippable", "offset": start, "bytes": cursor - start})
            continue
        if magic == 0x184C2102:
            blocks = 0
            while cursor < len(data):
                length = r.unpack("<I", cursor)[0]
                cursor += 4
                if not 0 < length <= 8 * 1024**2 + 65536:
                    raise ValueError("LZ4 legacy block size")
                chunk = r.region(cursor, length)
                cursor += length
                out.extend(block_decode(chunk, min(8 * 1024**2, limit - len(out))))
                blocks += 1
                if blocks > 20000:
                    raise ValueError("LZ4 block count limit")
            evidence.append({"kind": "legacy", "checksums": "CHECKSUM_ABSENT", "blocks": blocks})
            break
        if magic != 0x184D2204:
            raise ValueError("Unknown concatenated LZ4 magic")
        descriptor = cursor
        flags, bd = r.unpack("BB", cursor)
        cursor += 2
        maximum = {4: 65536, 5: 262144, 6: 1048576, 7: 4194304}.get((bd >> 4) & 7)
        if flags >> 6 != 1 or flags & 2 or bd & 0x8F or maximum is None:
            raise ValueError("Invalid LZ4 frame descriptor")
        content_size = None
        if flags & 8:
            content_size = r.unpack("<Q", cursor)[0]
            cursor += 8
            if content_size > limit - len(out):
                raise ValueError("LZ4 declared output exceeds limit")
        dictionary = None
        if flags & 1:
            dictionary = r.unpack("<I", cursor)[0]
            cursor += 4
        expected = (xxh32(data[descriptor:cursor]) >> 8) & 255
        if r.region(cursor, 1)[0] != expected:
            raise ValueError("CHECKSUM_FAILED: LZ4 header")
        cursor += 1
        if dictionary is not None:
            raise DictionaryRequired("BLOCKED_MISSING_DICTIONARY")
        frame_start = len(out)
        count = 0
        while True:
            encoded = r.unpack("<I", cursor)[0]
            cursor += 4
            if encoded == 0:
                break
            length = encoded & 0x7FFFFFFF
            if not 0 < length <= maximum or count >= 20000:
                raise ValueError("LZ4 block bounds/count")
            chunk = r.region(cursor, length)
            cursor += length
            if flags & 16:
                if xxh32(chunk) != r.unpack("<I", cursor)[0]:
                    raise ValueError("CHECKSUM_FAILED: LZ4 block")
                cursor += 4
            remaining = min(maximum, limit - len(out))
            if encoded & 0x80000000:
                if len(chunk) > remaining:
                    raise ValueError("LZ4 output limit")
                decoded = chunk
            else:
                history = b"" if flags & 32 else bytes(out[max(frame_start, len(out) - 65536) :])
                decoded = block_decode(chunk, remaining, history)
            out.extend(decoded)
            count += 1
        if content_size is not None and len(out) - frame_start != content_size:
            raise ValueError("LZ4 content size mismatch")
        if flags & 4:
            if xxh32(out[frame_start:]) != r.unpack("<I", cursor)[0]:
                raise ValueError("CHECKSUM_FAILED: LZ4 content")
            cursor += 4
        evidence.append(
            {
                "kind": "frame",
                "offset": start,
                "bytes": cursor - start,
                "blocks": count,
                "header": "HEADER_CHECKSUM_VERIFIED",
                "block": "BLOCK_CHECKSUM_VERIFIED" if flags & 16 else "CHECKSUM_ABSENT",
                "content": "CONTENT_CHECKSUM_VERIFIED" if flags & 4 else "CHECKSUM_ABSENT",
                "output_bytes": len(out) - frame_start,
            }
        )
    if not evidence:
        raise ValueError("Missing LZ4 frame")
    return bytes(out), {"schema": 1, "codec": "lz4", "status": "PASS", "frames": evidence}


def encode(data):
    """Deterministic interoperable frame, uncompressed blocks, all checksums enabled."""
    if len(data) > CAP:
        raise ValueError("LZ4 output limit")
    descriptor = bytes([0x7C, 0x40]) + struct.pack("<Q", len(data))
    out = bytearray(b"\x04\x22\x4d\x18" + descriptor + bytes([(xxh32(descriptor) >> 8) & 255]))
    for cursor in range(0, len(data), 65536):
        chunk = data[cursor : cursor + 65536]
        out.extend(
            struct.pack("<I", len(chunk) | 0x80000000) + chunk + struct.pack("<I", xxh32(chunk))
        )
    out.extend(bytes(4) + struct.pack("<I", xxh32(data)))
    return bytes(out)
