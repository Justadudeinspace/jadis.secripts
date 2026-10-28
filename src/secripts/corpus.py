"""Read-only recursive research inventory. Archive paths are metadata, never extraction targets."""

from collections import Counter
from dataclasses import dataclass
import hashlib
import io
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import tarfile
import tempfile
import zipfile
from secripts.secrets import contains_secret, redact
from secripts.safety import SecError


@dataclass(frozen=True)
class CorpusLimits:
    members: int = 100000
    depth: int = 6
    member_bytes: int = 512 * 1024**2
    total_bytes: int = 4 * 1024**3


FAMILIES = {
    "android-image-kitchen": ("aik", "image-kitchen", "image_kitchen"),
    "boot-tools": ("mkbootimg", "unpackboot", "bootsignature", "verifiedbootsigner", "bootimg"),
    "avb": ("avb", "verifiedboot"),
    "compression": ("lz4", "lzma", "gzip", "bzip", "xz", "cpio"),
    "device-tree": ("dtb", "dtbo", "boardconfig", "fstab", "androidproducts", "vintf"),
    "twrp": ("twrp", "omni", "recovery", "manifest"),
    "mediatek": ("mtk", "mediatek"),
    "rockchip": ("rockchip", "rkcrc", "rkflashtool"),
    "sony": ("sony", "sin_", "elf"),
    "legacy-signing": ("loki", "chromeos", "futility", "signblob"),
    "uboot": ("uboot", "u-boot", "mkimage"),
}
KEY = re.compile(r"(?i)(?:\.(?:pem|pk8|p12|pfx|key|crt|cer|x509)$|private.?key|id_rsa|keystore)")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unsafe_path(name):
    p = PurePosixPath(name)
    return (
        p.is_absolute()
        or ".." in p.parts
        or "\\" in name
        or bool(re.match(r"^[A-Za-z]:", name))
        or "\0" in name
    )


DEFAULT_LIMITS = CorpusLimits()


def inventory(paths, limits=DEFAULT_LIMITS):
    rows = []
    seen = {}
    consumed = 0
    blockers = []
    archives = []

    def inspect_member(name, size, compressed, mode, opener, chain, depth, date=None):
        nonlocal consumed
        if len(rows) >= limits.members:
            raise SecError("Corpus member limit reached", 4)
        identifier = f"corpus-{len(rows):06d}"
        unsafe = unsafe_path(name) or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
        key = bool(KEY.search(name))
        suffix = PurePosixPath(name).suffix.lower()
        row = {
            "id": identifier,
            "archive": chain[0],
            "container_chain": chain[1:],
            "path": redact(name),
            "bytes": size,
            "compressed_bytes": compressed,
            "sha256": None,
            "duplicate_of": None,
            "classification": "UNSAFE" if unsafe else "SECRET" if key else "UNKNOWN",
            "possible_key_material": key,
            "possible_secrets": False,
            "unsafe_path_or_type": unsafe,
            "language": {
                ".py": "python",
                ".sh": "shell",
                ".c": "c",
                ".h": "c",
                ".cpp": "c++",
                ".java": "java",
                ".pl": "perl",
                ".mk": "make",
            }.get(suffix),
            "family": next(
                (f for f, words in FAMILIES.items() if any(w in name.lower() for w in words)),
                "other",
            ),
            "date": date,
            "license": "UNKNOWN",
            "version_hint": None,
            "kind": "data",
            "nested": False,
            "architecture": "UNKNOWN",
            "recommendation": "Static review only; no code imported",
            "review": "AUTOMATED_HEURISTIC",
        }
        rows.append(row)
        if unsafe or key:
            row["path"] = identifier + suffix
        if size > limits.member_bytes or consumed + size > limits.total_bytes:
            row.update(
                classification="UNKNOWN" if not unsafe and not key else row["classification"],
                reason="Byte budget exceeded; not read",
            )
            blockers.append({"id": identifier, "reason": row["reason"]})
            return
        digest = hashlib.sha256()
        prefix = bytearray()
        overlap = ""
        sensitive = False
        try:
            with tempfile.SpooledTemporaryFile(max_size=8 * 1024**2) as spool:
                with opener() as stream:
                    actual = 0
                    while True:
                        chunk = stream.read(min(1024 * 1024, limits.member_bytes - actual + 1))
                        if not chunk:
                            break
                        actual += len(chunk)
                        consumed += len(chunk)
                        if actual > limits.member_bytes or consumed > limits.total_bytes:
                            raise ValueError("Streaming byte limit")
                        digest.update(chunk)
                        spool.write(chunk)
                        if len(prefix) < 65536:
                            prefix.extend(chunk[: 65536 - len(prefix)])
                        text = overlap + chunk.decode("utf-8", errors="replace")
                        sensitive = sensitive or contains_secret(text)
                        overlap = text[-4096:]
                if actual != size:
                    raise ValueError("Declared member size mismatch")
                row["sha256"] = digest.hexdigest()
                row["duplicate_of"] = seen.get(row["sha256"])
                seen.setdefault(row["sha256"], identifier)
                row["possible_secrets"] = sensitive
                head = bytes(prefix)
                text = head.decode("utf-8", errors="replace")
                binary = head.startswith((b"\x7fELF", b"MZ")) or suffix in {
                    ".exe",
                    ".dll",
                    ".so",
                    ".jar",
                }
                source = suffix in {
                    ".c",
                    ".h",
                    ".cpp",
                    ".py",
                    ".sh",
                    ".pl",
                    ".java",
                    ".mk",
                    ".bat",
                    ".cmd",
                }
                row["kind"] = (
                    "executable"
                    if binary or head.startswith(b"#!")
                    else "source"
                    if source
                    else "document"
                    if suffix in {".md", ".txt", ".rst"}
                    else "data"
                )
                if head.startswith(b"\x7fELF") and len(head) > 20:
                    row["architecture"] = str(
                        int.from_bytes(head[18:20], "little" if head[5] == 1 else "big")
                    )
                if PurePosixPath(name).name.lower().startswith(("license", "copying")):
                    row["license"] = next(
                        (
                            label
                            for marker, label in [
                                ("Apache License", "Apache"),
                                ("GNU GENERAL PUBLIC LICENSE", "GPL"),
                                ("MIT License", "MIT"),
                                ("Redistribution and use", "BSD-family"),
                            ]
                            if marker in text
                        ),
                        "UNKNOWN",
                    )
                hint = re.search(r"(?:[vV]|[-_])(\d+\.\d+(?:\.\d+)?)", PurePosixPath(name).name)
                row["version_hint"] = hint.group(1) if hint else None
                if not unsafe and not key:
                    row["classification"] = (
                        "SECRET"
                        if sensitive
                        else "ARCHIVE_ONLY"
                        if row["duplicate_of"]
                        else "OPTIONAL_PROVIDER"
                        if binary
                        else "REIMPLEMENT"
                        if source and row["family"] != "other"
                        else "EXTRACT_KNOWLEDGE"
                        if row["kind"] == "document"
                        else "REFERENCE"
                    )
                if sensitive:
                    row["path"] = identifier + suffix
                is_zip = head.startswith(b"PK\x03\x04") or head.startswith(b"PK\x05\x06")
                is_tar = suffix in {".gz", ".tgz", ".tar", ".xz", ".bz2"}
                row["nested"] = is_zip or is_tar or suffix in {".rar", ".7z"}
                if row["nested"] and not unsafe:
                    if depth >= limits.depth:
                        blockers.append({"id": identifier, "reason": "Nested depth limit"})
                        return
                    spool.seek(0)
                    nested_chain = chain + [row["path"]]
                    if is_zip:
                        walk_zip(spool, nested_chain, depth + 1)
                    elif is_tar:
                        try:
                            walk_tar(spool, nested_chain, depth + 1)
                        except tarfile.ReadError:
                            blockers.append(
                                {
                                    "id": identifier,
                                    "reason": "Compression/container is not supported tar; metadata only",
                                }
                            )
                    else:
                        blockers.append(
                            {
                                "id": identifier,
                                "reason": "RAR/7z unsupported; no external corpus tool executed",
                            }
                        )
        except (
            OSError,
            ValueError,
            RuntimeError,
            zipfile.BadZipFile,
            EOFError,
            tarfile.TarError,
        ) as exc:
            row["reason"] = "Read/container error: " + type(exc).__name__
            blockers.append({"id": identifier, "reason": row["reason"]})

    def walk_zip(source, chain, depth):
        # Bound central-directory allocation before ZipFile builds its member list.
        owned = isinstance(source, (str, Path))
        stream = Path(source).open("rb") if owned else source
        try:
            stream.seek(0, 2)
            length = stream.tell()
            stream.seek(max(0, length - 65557))
            tail = stream.read(65557)
            offset = tail.rfind(b"PK\x05\x06")
            if offset < 0 or len(tail) - offset < 22:
                raise ValueError("Missing ZIP end record")
            entries = struct.unpack_from("<H", tail, offset + 10)[0]
            central_bytes = struct.unpack_from("<I", tail, offset + 12)[0]
            if entries == 65535 or central_bytes == 0xFFFFFFFF:
                raise ValueError("ZIP64 inventory unsupported; bounded refusal")
            if entries > limits.members - len(rows) or central_bytes > 64 * 1024**2:
                raise ValueError("ZIP central directory limit")
            stream.seek(0)
        finally:
            if owned:
                stream.close()
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            if len(infos) > limits.members - len(rows):
                raise SecError("ZIP entry limit reached", 4)
            for info in infos:
                if info.is_dir():
                    continue
                if info.flag_bits & 1:
                    blockers.append({"archive": chain[0], "reason": "Encrypted member excluded"})
                    continue
                inspect_member(
                    info.filename,
                    info.file_size,
                    info.compress_size,
                    info.external_attr >> 16,
                    lambda i=info: archive.open(i),
                    chain,
                    depth,
                    list(info.date_time),
                )

    def walk_tar(source, chain, depth):
        with tarfile.open(fileobj=source, mode="r|*") as archive:
            for member in archive:
                if member.isdir():
                    continue
                mode = stat.S_IFREG if member.isfile() else stat.S_IFLNK
                inspect_member(
                    member.name,
                    member.size,
                    None,
                    mode,
                    lambda m=member: archive.extractfile(m) if m.isfile() else io.BytesIO(),
                    chain,
                    depth,
                )

    for path in map(Path, paths):
        archives.append({"source": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
        try:
            walk_zip(path, [path.name], 0)
        except (ValueError, zipfile.BadZipFile, OSError, SecError) as exc:
            blockers.append(
                {"archive": path.name, "reason": "Archive refused: " + type(exc).__name__}
            )
    return {
        "schema": 1,
        "archives": archives,
        "members": len(rows),
        "bytes_streamed": consumed,
        "classifications": dict(Counter(r["classification"] for r in rows)),
        "families": dict(Counter(r["family"] for r in rows)),
        "duplicates": sum(bool(r["duplicate_of"]) for r in rows),
        "nested_containers": sum(r["nested"] for r in rows),
        "complete_within_supported_formats": not blockers,
        "limits": vars(limits),
        "blockers": blockers,
        "components": rows,
        "security": "No extraction paths or payload execution; secret/key paths opaque; all source archives read-only",
    }
