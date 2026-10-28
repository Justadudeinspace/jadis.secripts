"""Bounded, non-extracting compression and newc CPIO metadata inspection."""

from pathlib import PurePosixPath
import re

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
    from secripts.images.cpio import parse

    model = parse(data)
    entries = model["entries"]
    markers = set()
    fstabs = []
    links = []
    paths = []
    unsafe = directories = symlinks = executables = files = 0
    for entry in entries:
        name = entry["path"]
        path = PurePosixPath(name)
        payload = entry["payload"]
        unsafe += entry["extraction_safety"] == "UNSAFE"
        directories += entry["type"] == "directory"
        symlinks += entry["type"] == "symlink"
        files += entry["type"] == "file"
        executables += bool(entry["mode"] & 0o111)
        sensitive = bool(re.search(r"(?i)(?:\.(?:pem|key|pk8|crt|cer)$|serial|credential)", name))
        if len(paths) < 256:
            paths.append("[SENSITIVE_PATH_OMITTED]" if sensitive else name)
        if entry["type"] == "symlink" and len(links) < 128:
            target = entry["symlink_target"]
            links.append(
                {
                    "path": "[SENSITIVE_PATH_OMITTED]" if sensitive else name,
                    "target": "[SENSITIVE_PATH_OMITTED]" if sensitive else target,
                    "unsafe": PurePosixPath(target).is_absolute()
                    or ".." in PurePosixPath(target).parts,
                    "followed": False,
                }
            )
        if "fstab" in path.name and len(payload) <= 65536 and len(fstabs) < 8 and not sensitive:
            rows = []
            for line in payload.decode(errors="replace").splitlines()[:512]:
                fields = line.split("#", 1)[0].split()
                if len(fields) >= 3:
                    rows.append(
                        {
                            "fields": fields[:6],
                            "indicators": [
                                flag
                                for flag in (
                                    "logical",
                                    "slotselect",
                                    "fileencryption",
                                    "metadata_encryption",
                                    "encryptable",
                                    "avb",
                                )
                                if flag in line
                            ],
                        }
                    )
            fstabs.append({"path": name, "entries": rows})
        if name.startswith("first_stage_ramdisk"):
            markers.add("first_stage_ramdisk")
        if "vintf" in path.parts:
            markers.add("vintf")
        if path.name.startswith("init.recovery."):
            markers.add("init.recovery.*")
        if "selinux" in name or path.name in ("sepolicy", "file_contexts"):
            markers.add("selinux")
        if path.name in {"init", "recovery", "twrp", "prop.default"} or path.name.startswith(
            "fstab."
        ):
            markers.add("fstab.*" if path.name.startswith("fstab.") else path.name)
    return {
        "status": "PASS",
        "entries": len(entries),
        "markers": sorted(markers),
        "unsafe_paths": unsafe,
        "files": files,
        "directories": directories,
        "symlinks": symlinks,
        "executables": executables,
        "paths": paths,
        "links": links,
        "fstabs": fstabs,
        "crc_failures": 0,
        "archives": model["archives"],
        "paths_truncated": len(entries) > len(paths),
        "note": "Metadata only; shared canonical CPIO parser; no extraction",
    }


def inspect_ramdisk(data, declared_size, *, output_limit=None):
    cap = min(LIMIT, output_limit if output_limit is not None else LIMIT)
    from secripts.images.compression import identify

    kind = identify(data)
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
        from secripts.images.codecs import decode
        from secripts.images.lz4codec import DictionaryRequired

        try:
            decoded, verification = decode(data, limit=cap)
        except DictionaryRequired:
            return {**result, "status": "UNRESOLVED", "reason": "BLOCKED_MISSING_DICTIONARY"}
        if len(decoded) > cap:
            raise ValueError("Decompressed ramdisk exceeds output limit")
        metadata = cpio_metadata(decoded)
        return {
            **result,
            "status": "PARTIAL" if metadata["unsafe_paths"] else "PASS",
            "decompressed_bytes": len(decoded),
            "cpio": metadata,
            "verification": verification,
            "trailing_compressed_data": len(verification.get("members", [])) > 1,
        }
    except (ValueError, OSError, EOFError) as exc:
        if str(exc) == "UNSUPPORTED_COMPRESSION":
            return {
                **result,
                "reason": "Native decompressor unavailable; no external tools executed",
            }
        return {**result, "status": "FAIL", "reason": str(exc)}
