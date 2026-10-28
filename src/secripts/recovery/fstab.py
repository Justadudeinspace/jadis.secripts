"""Structured fstab evidence and conservative generation, never guessed block paths."""

import re
from secripts.secrets import contains_secret

FILESYSTEMS = {"ext4", "f2fs", "vfat", "emmc", "auto", "squashfs", "erofs", "swap"}


def parse(fields, source, location):
    if len(fields) < 3:
        return None
    if fields[0].startswith("/") and fields[1] in FILESYSTEMS:
        mount, fs, partition = fields[:3]
        options = fields[3:]
        style = "recovery"
    else:
        partition, mount, fs = fields[:3]
        options = fields[3:]
        style = "android"
    if not mount.startswith("/") or ".." in mount.split("/") or fs not in FILESYSTEMS:
        return None
    if any(contains_secret(s) or any(c in s for c in "\n\r\0`$;") for s in fields):
        return None
    if not (
        partition.startswith("/dev/block/") or re.fullmatch(r"[A-Za-z0-9_.-]+", partition)
    ) or ".." in partition.split("/"):
        return None
    flags = ",".join(options)
    return {
        "mount_point": mount,
        "partition_source": partition,
        "filesystem": fs,
        "options": options,
        "style": style,
        "logical": "logical" in flags.split(","),
        "slot_behavior": "slotselect" if "slotselect" in flags else "UNKNOWN",
        "encryption_indicators": [
            v
            for v in ("fileencryption", "metadata_encryption", "encryptable", "forceencrypt")
            if v in flags
        ],
        "metadata_relevance": mount == "/metadata" or "metadata_encryption" in flags,
        "source": source,
        "location": location,
        "state": "DECLARED",
        "confidence": "STATIC_DECLARATION_NOT_DEVICE_QUALIFICATION",
    }


def report(record):
    rows = record.get("fstab_evidence", [])
    by_mount = {}
    for row in rows:
        by_mount.setdefault(row["mount_point"], []).append(row)
    conflicts = [
        mount
        for mount, items in by_mount.items()
        if len(
            {
                (r["partition_source"], r["filesystem"], tuple(r["options"]), r["style"])
                for r in items
            }
        )
        > 1
    ]
    return {
        "schema": 1,
        "entries": rows,
        "conflicts": conflicts,
        "status": "CONFLICT" if conflicts else "PARTIAL" if not rows else "REVIEW_REQUIRED",
        "note": "Mount declarations are evidence; no live partition probing or block-device guessing",
    }


def generate(record):
    r = report(record)
    if r["conflicts"]:
        return "", r
    lines = []
    seen = set()
    for row in r["entries"]:
        if row["mount_point"] in seen:
            continue
        seen.add(row["mount_point"])
        head = (
            [row["mount_point"], row["filesystem"], row["partition_source"]]
            if row["style"] == "recovery"
            else [row["partition_source"], row["mount_point"], row["filesystem"]]
        )
        lines.append(" ".join(head + row["options"]))
    return "\n".join(lines) + ("\n" if lines else ""), r
