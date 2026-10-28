"""Bounded, non-extracting compression and newc CPIO metadata inspection."""

import bz2
import lzma
from pathlib import PurePosixPath
import zlib
import re
import stat

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
    directories = symlinks = executables = files = 0
    paths = []
    links = []
    fstabs = []
    crc_failures = 0
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
                "files": files,
                "directories": directories,
                "symlinks": symlinks,
                "executables": executables,
                "paths": paths,
                "links": links,
                "fstabs": fstabs,
                "crc_failures": crc_failures,
                "paths_truncated": count > len(paths),
                "note": "Metadata only; no extraction, symlink following or device qualification",
            }
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            unsafe += 1
        mode = int(header[14:22], 16)
        if stat.S_ISDIR(mode):
            directories += 1
        elif stat.S_ISLNK(mode):
            symlinks += 1
        else:
            files += 1
        if mode & 0o111:
            executables += 1
        sensitive = bool(re.search(r"(?i)(?:\.(?:pem|key|pk8|crt|cer)$|serial|credential)", name))
        if len(paths) < 256:
            paths.append("[SENSITIVE_PATH_OMITTED]" if sensitive else name)
        if stat.S_ISLNK(mode) and size <= 4096 and len(links) < 128:
            target = data[body : body + size].decode(errors="replace")
            links.append(
                {
                    "path": name,
                    "target": target,
                    "unsafe": PurePosixPath(target).is_absolute()
                    or ".." in PurePosixPath(target).parts,
                    "followed": False,
                }
            )
        if header[:6] == b"070702" and sum(data[body : body + size]) & 0xFFFFFFFF != int(
            header[102:110], 16
        ):
            crc_failures += 1
        if "fstab" in path.name and size <= 65536 and len(fstabs) < 8 and not sensitive:
            text = data[body : body + size].decode(errors="replace")
            rows = []
            for line in text.splitlines()[:512]:
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
        if kind == "gzip":
            decoder = zlib.decompressobj(31)
            decoded = decoder.decompress(data, cap + 1)
        elif kind == "xz":
            decoder = lzma.LZMADecompressor(memlimit=64 * 1024 * 1024)
            decoded = decoder.decompress(data, max_length=cap + 1)
        elif kind == "lzma-alone":
            decoder = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE, memlimit=64 * 1024 * 1024)
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
            "status": "PARTIAL" if metadata["unsafe_paths"] or metadata["crc_failures"] else "PASS",
            "decompressed_bytes": len(decoded),
            "cpio": metadata,
            "trailing_compressed_data": bool(decoder and decoder.unused_data),
        }
    except (ValueError, OSError, EOFError, zlib.error, lzma.LZMAError) as exc:
        return {**result, "status": "FAIL", "reason": str(exc)}
