"""Untrusted AVB declarations, independently parsed. No authentication or trust decision."""

import struct
import shutil

ALGORITHMS = {
    0: "NONE",
    1: "SHA256_RSA2048",
    2: "SHA256_RSA4096",
    3: "SHA256_RSA8192",
    4: "SHA512_RSA2048",
    5: "SHA512_RSA4096",
    6: "SHA512_RSA8192",
}


def inspect_avb(path):
    size = path.stat().st_size
    result = {
        "detected": False,
        "status": "UNKNOWN",
        "signature_verification": "UNTESTED",
        "trusted_key": "UNKNOWN",
        "rollback_enforcement": "UNTESTED",
        "avbtool": shutil.which("avbtool"),
        "note": "Parsed declarations are untrusted metadata, not verified claims",
    }
    with path.open("rb") as stream:
        first = stream.read(4)
        stream.seek(max(0, size - 64))
        footer = stream.read(64)
        offset = 0
        bound = size
        if footer[:4] == b"AVBf" and len(footer) == 64:
            major, minor, original, offset, length = struct.unpack_from(">IIQQQ", footer, 4)
            result.update(
                detected=True,
                footer={
                    "major": major,
                    "minor": minor,
                    "original_image_size": original,
                    "vbmeta_offset": offset,
                    "vbmeta_size": length,
                },
            )
            if (
                major != 1
                or original > offset
                or offset + length > size - 64
                or length < 256
                or any(footer[36:])
            ):
                return {
                    **result,
                    "status": "FAIL",
                    "reason": "Malformed/unsupported AVB footer bounds/version",
                }
            bound = offset + length
        elif first != b"AVB0":
            return {
                **result,
                "status": "NOT_DETECTED",
                "reason": "No standalone vbmeta magic or end-of-file AVB footer",
            }
        result["detected"] = True
        stream.seek(offset)
        header = stream.read(256)
        if len(header) != 256 or header[:4] != b"AVB0":
            return {**result, "status": "FAIL", "reason": "Truncated or missing vbmeta header"}
        major, minor = struct.unpack_from(">II", header, 4)
        auth, aux = struct.unpack_from(">QQ", header, 12)
        algorithm = struct.unpack_from(">I", header, 28)[0]
        desc_offset, desc_size, rollback = struct.unpack_from(">QQQ", header, 96)
        flags, rollback_location = struct.unpack_from(">II", header, 120)
        if (
            major != 1
            or auth % 64
            or aux % 64
            or offset + 256 + auth + aux > bound
            or desc_offset + desc_size > aux
            or desc_size > 1024 * 1024
        ):
            return {
                **result,
                "status": "FAIL",
                "reason": "Unsupported version or invalid vbmeta block/descriptor bounds",
            }
        # Validate all known authentication/auxiliary subranges before parsing descriptors.
        for where, limit in ((32, auth), (48, auth), (64, aux), (80, aux)):
            start, length = struct.unpack_from(">QQ", header, where)
            if start + length > limit:
                return {**result, "status": "FAIL", "reason": "Invalid vbmeta subrange"}
        stream.seek(offset + 256 + auth + desc_offset)
        data = stream.read(desc_size)
    descriptors = []
    cursor = 0
    while cursor < len(data):
        if cursor + 16 > len(data):
            return {**result, "status": "FAIL", "reason": "Truncated descriptor header"}
        tag, length = struct.unpack_from(">QQ", data, cursor)
        end = cursor + 16 + length
        if end > len(data) or length % 8 or len(descriptors) >= 4096:
            return {**result, "status": "FAIL", "reason": "Invalid descriptor bounds/alignment"}
        entry = {"tag": tag, "bytes": 16 + length, "state": "UNTRUSTED_DECLARATION"}
        if tag == 2:
            if length < 116:
                return {**result, "status": "FAIL", "reason": "Truncated hash descriptor"}
            name_len, salt_len, digest_len = struct.unpack_from(">III", data, cursor + 56)
            if 132 + name_len + salt_len + digest_len > 16 + length:
                return {
                    **result,
                    "status": "FAIL",
                    "reason": "Hash descriptor variable data bounds",
                }
            entry["partition"] = data[cursor + 132 : cursor + 132 + name_len].decode(
                "utf-8", errors="replace"
            )
            entry["image_size"] = struct.unpack_from(">Q", data, cursor + 16)[0]
            entry["hash_algorithm"] = (
                data[cursor + 24 : cursor + 56].split(b"\0")[0].decode("ascii", errors="replace")
            )
        descriptors.append(entry)
        cursor = end
    return {
        **result,
        "status": "OBSERVED",
        "required_version": f"{major}.{minor}",
        "algorithm": ALGORITHMS.get(algorithm, f"UNKNOWN({algorithm})"),
        "rollback_index": rollback,
        "rollback_index_location": rollback_location,
        "flags": flags,
        "descriptors": descriptors,
    }
