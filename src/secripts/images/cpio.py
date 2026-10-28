"""Bounded newc/CRC canonical model. Archive names never become host write paths."""

import hashlib
import stat
from pathlib import PurePosixPath

CAP = 32 * 1024**2
FIELDS = (
    "ino",
    "mode",
    "uid",
    "gid",
    "nlink",
    "mtime",
    "size",
    "devmajor",
    "devminor",
    "rdevmajor",
    "rdevminor",
    "namesize",
    "check",
)
TYPES = {
    stat.S_IFREG: "file",
    stat.S_IFDIR: "directory",
    stat.S_IFLNK: "symlink",
    stat.S_IFCHR: "character",
    stat.S_IFBLK: "block",
    stat.S_IFIFO: "fifo",
    stat.S_IFSOCK: "socket",
}


def path_state(name):
    path = PurePosixPath(name)
    return (
        "UNSAFE"
        if (
            not name
            or path.is_absolute()
            or ".." in path.parts
            or "\\" in name
            or "\0" in name
            or bool(path.parts and ":" in path.parts[0])
            or len(name.encode()) > 4096
        )
        else "VIRTUAL_ONLY"
    )


def parse(data):
    if len(data) > CAP:
        raise ValueError("CPIO input limit")
    cursor = 0
    entries = []
    archive_index = 0
    trailers = []
    while cursor < len(data):
        if data[cursor : cursor + 1] == b"\0":
            end = cursor
            while end < len(data) and data[end] == 0:
                end += 1
            cursor = end
            if cursor == len(data):
                break
        if len(entries) >= 20000 or archive_index >= 256 or cursor + 110 > len(data):
            raise ValueError("CPIO bounds/count/header limit")
        start = cursor
        header = data[cursor : cursor + 110]
        if header[:6] not in (b"070701", b"070702"):
            raise ValueError("Invalid CPIO magic")
        if any(byte not in b"0123456789abcdefABCDEF" for byte in header[6:]):
            raise ValueError("Invalid CPIO hexadecimal field")
        values = dict(
            zip(FIELDS, (int(header[6 + i * 8 : 14 + i * 8], 16) for i in range(13)), strict=True)
        )
        size = values["size"]
        namesize = values["namesize"]
        if not 1 <= namesize <= 4096 or cursor + 110 + namesize > len(data):
            raise ValueError("CPIO name bounds")
        raw = data[cursor + 110 : cursor + 110 + namesize]
        if raw[-1:] != b"\0" or b"\0" in raw[:-1]:
            raise ValueError("Invalid CPIO name termination")
        try:
            name = raw[:-1].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Non-UTF8 CPIO name unsupported") from exc
        if any(ord(c) < 32 or ord(c) == 127 for c in name):
            raise ValueError("CPIO control-character names unsupported")
        body = (cursor + 110 + namesize + 3) // 4 * 4
        if body + size > len(data):
            raise ValueError("CPIO payload bounds")
        payload = data[body : body + size]
        if header[:6] == b"070702" and sum(payload) & 0xFFFFFFFF != values["check"]:
            raise ValueError("CHECKSUM_FAILED: CPIO CRC sum")
        cursor = (body + size + 3) // 4 * 4
        if cursor > len(data):
            raise ValueError("CPIO alignment extends past input")
        if name == "TRAILER!!!":
            if size:
                raise ValueError("CPIO trailer contains payload")
            trailers.append(
                {"archive": archive_index, "offset": start, "format": header[:6].decode()}
            )
            archive_index += 1
            continue
        kind = TYPES.get(stat.S_IFMT(values["mode"]), "unknown")
        if kind not in {"file", "symlink"} and size:
            raise ValueError("CPIO special entry has payload")
        entry = {
            **values,
            "path": name,
            "type": kind,
            "format": header[:6].decode(),
            "archive": archive_index,
            "index": len(entries),
            "offset": start,
            "payload_offset": body,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "extraction_safety": path_state(name),
            "payload": payload,
        }
        if kind == "symlink":
            entry["symlink_target"] = payload.decode("utf-8", errors="strict")
        entries.append(entry)
    if not entries and not trailers:
        raise ValueError("Empty/non-CPIO input")
    return {
        "schema": 1,
        "model": "ramdisk-cpio",
        "entries": entries,
        "trailers": trailers,
        "archives": max(archive_index, 1),
        "order": "ORIGINAL",
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "trailer_policy": "Optional per Linux initramfs specification; canonical pack emits trailers",
    }


def metadata(model):
    return {
        **model,
        "entries": [
            {k: v for k, v in entry.items() if k != "payload"} for entry in model["entries"]
        ],
    }


def pack(model):
    if model.get("schema") != 1 or model.get("model") != "ramdisk-cpio":
        raise ValueError("Unsupported CPIO model version")
    entries = model["entries"]
    if len(entries) > 20000:
        raise ValueError("CPIO entry count")
    output = bytearray()
    current = 0

    def emit(name, values, payload, variant):
        if variant not in {"070701", "070702"} or len(name.encode()) > 4095 or "\0" in name:
            raise ValueError("Invalid CPIO model name/format")
        if path_state(name) == "UNSAFE":
            raise ValueError("Unsafe CPIO path refused")
        raw = name.encode() + b"\0"
        numbers = {
            **values,
            "size": len(payload),
            "namesize": len(raw),
            "check": sum(payload) & 0xFFFFFFFF if variant == "070702" else 0,
        }
        if any(
            type(numbers.get(key)) is not int or not 0 <= numbers[key] <= 0xFFFFFFFF
            for key in FIELDS
        ):
            raise ValueError("Invalid CPIO field")
        output.extend(
            variant.encode() + "".join(f"{numbers[key]:08x}" for key in FIELDS).encode() + raw
        )
        output.extend(bytes((-len(output)) % 4))
        output.extend(payload)
        output.extend(bytes((-len(output)) % 4))
        if len(output) > CAP:
            raise ValueError("CPIO output limit")

    def trailer(variant):
        emit("TRAILER!!!", dict.fromkeys(FIELDS, 0), b"", variant)

    last = "070701"
    for entry in entries:
        group = entry.get("archive", 0)
        if type(group) is not int or not current <= group < 256:
            raise ValueError("CPIO archive ordering")
        while current < group:
            trailer(last)
            current += 1
        last = entry["format"]
        payload = entry["payload"]
        if TYPES.get(stat.S_IFMT(entry["mode"]), "unknown") != entry["type"]:
            raise ValueError("CPIO type/mode mismatch")
        if (
            entry["type"] == "symlink"
            and "symlink_target" in entry
            and entry["symlink_target"].encode() != payload
        ):
            raise ValueError("CPIO derived symlink target disagrees with payload")
        if entry["type"] not in {"file", "symlink"} and payload:
            raise ValueError("Special CPIO payload refused")
        emit(entry["path"], entry, payload, last)
    trailer(last)
    return bytes(output)
