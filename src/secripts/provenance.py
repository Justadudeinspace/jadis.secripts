"""Bounded ZIP archaeology: inspect in memory, never extract historical content."""

import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
import re
import zipfile
from secripts.secrets import contains_secret, redact
from secripts.safety import SecError
from secripts.receipts import write_json

CLASSIFICATIONS = {"PROMOTE", "EXTRACT", "ARCHIVE", "REJECT", "SECRET"}
FAMILIES = {
    "recovery": ("twrp", "recovery", "boardconfig"),
    "android": ("android", "adb", "fastboot", "sdk"),
    "termux": ("termux", "proot"),
    "debian": ("debian", "apt install", "linux", "docker"),
    "git": ("github", "git clone", "git remote", "ssh-keygen"),
    "models": ("ollama", "hugging", "llama", "model"),
    "unrelated": ("blux", "axiom", "outer-void", "voidforge"),
}


def inventory(archive: Path) -> dict:
    records, hashes = [], {}
    with zipfile.ZipFile(archive) as source:
        entries = [i for i in source.infolist() if not i.is_dir()]
        if len(entries) > 10000 or sum(i.file_size for i in entries) > 256 * 1024 * 1024:
            raise SecError("Archive exceeds bounded ingestion limits", 4)
        for index, info in enumerate(entries):
            path = PurePosixPath(info.filename)
            unsafe = path.is_absolute() or ".." in path.parts or "\\" in info.filename
            if info.file_size > 8 * 1024 * 1024 or info.flag_bits & 1:
                raise SecError("Oversized or encrypted archive member refused", 4)
            raw = source.read(info)
            digest = hashlib.sha256(raw).hexdigest()
            text = raw.decode("utf-8", errors="replace")
            sensitive_found = contains_secret(text) or contains_secret(info.filename)
            duplicate = hashes.get(digest)
            hashes.setdefault(digest, f"legacy-{index:04d}")
            family = next(
                (
                    k
                    for k, words in FAMILIES.items()
                    if any(w in (info.filename + "\n" + text).lower() for w in words)
                ),
                "other",
            )
            unrelated = any(w in info.filename.lower() for w in FAMILIES["unrelated"])
            executable = path.suffix in {".sh", ".py"} or text.startswith("#!")
            classification, reason = "ARCHIVE", "Historical context; no production import"
            if family != "other" and not unrelated:
                classification, reason = (
                    "EXTRACT",
                    "Candidate technical knowledge; rewrite and validate",
                )
            if duplicate or unsafe or unrelated or path.suffix.lower() in {".png", ".gif", ".svg"}:
                classification, reason = (
                    "REJECT",
                    "Duplicate, unsafe path, unrelated project or binary asset",
                )
            if sensitive_found:
                classification, reason = (
                    "SECRET",
                    "Sensitive authentication pattern; content excluded",
                )
            # Basename only: do not publish personal directory names.
            name = re.sub(r"[\x00-\x1f\x7f]", "?", path.name)
            if sensitive_found:
                name = f"excluded-{index:04d}{path.suffix if len(path.suffix) < 10 else ''}"
            records.append(
                {
                    "id": f"legacy-{index:04d}",
                    "source": redact(name),
                    "source_sha256": digest,
                    "bytes": info.file_size,
                    "extension": path.suffix.lower(),
                    "category": family,
                    "classification": classification,
                    "reason": reason,
                    "duplicate_group": duplicate,
                    "contained_secrets": sensitive_found,
                    "executable_candidate": executable,
                    "technical_document": path.suffix in {".md", ".txt"},
                    "modern_replacement": [],
                    "review": "UNREVIEWED",
                }
            )
    return {
        "schema": 1,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "file_count": len(records),
        "counts": dict(Counter(r["classification"] for r in records)),
        "duplicates": sum(r["duplicate_group"] is not None for r in records),
        "artifacts": records,
    }


def validate(value: dict) -> None:
    if (
        not isinstance(value, dict)
        or value.get("schema") != 1
        or not isinstance(value.get("artifacts"), list)
    ):
        raise SecError("Malformed provenance", 2)
    ids = set()
    for entry in value["artifacts"]:
        if not isinstance(entry, dict):
            raise SecError("Malformed provenance artifact", 2)
        if (
            entry.get("classification") not in CLASSIFICATIONS
            or not re.fullmatch(r"[a-f0-9]{64}", entry.get("source_sha256", ""))
            or not entry.get("id")
            or entry["id"] in ids
        ):
            raise SecError("Malformed provenance artifact", 2)
        if entry.get("contained_secrets") and entry["classification"] != "SECRET":
            raise SecError("Secret artifact cannot be promoted", 4)
        ids.add(entry["id"])


def packaged() -> dict:
    from importlib.resources import files

    value = json.loads(files("secripts").joinpath("data/legacy.json").read_text())
    validate(value)
    return value


def ingest(archive: Path, output: Path) -> dict:
    value = inventory(archive)
    validate(value)
    write_json(output, value)
    return value
