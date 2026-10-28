"""Canonical ramdisk workspace, virtual extraction, deterministic pack and semantic differences."""

import os
from pathlib import Path
import re
import stat
from secripts.images import codecs, cpio
from secripts.images.artifacts import (
    read,
    digest,
    canonical,
    exclusive,
    json_model,
    child,
    NewWorkspace,
    evidence,
)
from secripts.secrets import contains_secret
from secripts.safety import SecError


SENSITIVE_PATH = re.compile(
    r"(?i)(?:\.(?:pem|pk8|p12|key|keystore)$|id_rsa|private.?key|credential)"
)


def parse(data, kind=None):
    decoded, codec = codecs.decode(data, kind)
    model = cpio.parse(decoded)
    model["compression"] = codec
    model["encoded_sha256"] = digest(data)
    model["decoded_sha256"] = digest(decoded)
    return model


def inspect(path):
    value = parse(read(path, codecs.CAP))
    report = cpio.metadata(value)
    report["qualification"] = {"device_compatibility": "UNTESTED", "bootability": "UNTESTED"}
    receipt = evidence(
        "ramdisk.inspect",
        source=path,
        format=value["compression"]["codec"],
        entries=len(value["entries"]),
        verification=value["compression"],
    )
    return {**report, "receipt_id": receipt["receipt_id"]}


def extract(path, output):
    raw = read(path, codecs.CAP)
    model = parse(raw)
    for entry in model["entries"]:
        if entry["extraction_safety"] == "UNSAFE":
            raise SecError("Unsafe ramdisk path; extraction refused", 4)
        if SENSITIVE_PATH.search(entry["path"]) or contains_secret(
            entry["payload"].decode("utf-8", errors="replace")
        ):
            raise SecError("Sensitive ramdisk material excluded; extraction refused", 4)
    with NewWorkspace(output) as root:
        exclusive(root / "source/artifact.bin", raw)
        os.chmod(root / "source/artifact.bin", 0o400)
        manifest = cpio.metadata(model)
        manifest["source_size"] = len(raw)
        for entry, metadata in zip(model["entries"], manifest["entries"], strict=True):
            payload_name = f"extracted/entry-{entry['index']:05d}.bin"
            metadata["payload_file"] = payload_name
            exclusive(root / payload_name, entry["payload"])
        canonical(root / "model/ramdisk.json", manifest)
    receipt = evidence(
        "ramdisk.extract",
        source=path,
        format=model["compression"]["codec"],
        entries=len(model["entries"]),
        workspace=str(output),
        extraction="VIRTUAL_PAYLOADS_ONLY",
    )
    return {
        "status": "EXTRACTED",
        "workspace": str(output),
        "entries": len(model["entries"]),
        "receipt_id": receipt["receipt_id"],
        "symlinks": "METADATA_ONLY",
        "special_files": "METADATA_ONLY",
    }


def load_workspace(root):
    root = Path(root)
    if root.is_symlink():
        raise SecError("Symlink workspace refused", 4)
    model = json_model(child(root, "model/ramdisk.json"), "ramdisk-cpio")
    original = read(child(root, "source/artifact.bin"), codecs.CAP)
    if digest(original) != model["encoded_sha256"]:
        raise SecError("Immutable source snapshot changed", 4)
    baseline = parse(original)
    if len(model["entries"]) > 20000 or len(model["entries"]) != len(baseline["entries"]):
        raise SecError("Workspace entry model changed; unsupported editing contract", 4)
    total = 0
    for entry, baseline_entry in zip(model["entries"], baseline["entries"], strict=True):
        entry["payload"] = read(child(root, entry["payload_file"]), codecs.CAP)
        if entry["type"] == "symlink":
            if entry.get("symlink_target") != baseline_entry.get("symlink_target"):
                raise SecError("Edit symlink payload file, not derived target metadata", 4)
            entry["symlink_target"] = entry["payload"].decode("utf-8")
        total += len(entry["payload"])
        if total > codecs.CAP:
            raise SecError("Aggregate ramdisk workspace limit", 4)
    return model, original


def directory_model(path):
    path = Path(path)
    if path.is_symlink() or not path.is_dir():
        raise SecError("Ramdisk input must be a regular directory", 3)
    entries = []
    total = 0
    for current, dirs, files in os.walk(path, followlinks=False):
        dirs.sort()
        files.sort()
        if len(Path(current).relative_to(path).parts) > 64:
            raise SecError("Directory depth limit", 4)
        for name in sorted(dirs + files):
            target = Path(current) / name
            relative = target.relative_to(path).as_posix()
            if SENSITIVE_PATH.search(relative):
                raise SecError("Sensitive path excluded from ramdisk packing", 4)
            info = target.lstat()
            kind = cpio.TYPES.get(stat.S_IFMT(info.st_mode), "unknown")
            if kind not in {"file", "directory", "symlink"}:
                raise SecError("Special host file packing refused", 4)
            payload = (
                os.readlink(target).encode()
                if kind == "symlink"
                else read(target, codecs.CAP)
                if kind == "file"
                else b""
            )
            if contains_secret(payload.decode("utf-8", errors="replace")):
                raise SecError("Sensitive content excluded from packing", 4)
            total += len(payload)
            if total > codecs.CAP or len(entries) >= 20000:
                raise SecError("Ramdisk directory aggregate limit", 4)
            entry = dict.fromkeys(cpio.FIELDS, 0)
            entry.update(
                path=relative,
                type=kind,
                mode=info.st_mode & 0xFFFF,
                ino=len(entries) + 1,
                nlink=1,
                format="070701",
                archive=0,
                payload=payload,
            )
            entries.append(entry)
    entries.sort(key=lambda e: e["path"])
    return {"schema": 1, "model": "ramdisk-cpio", "entries": entries}


def pack(path, output, compression=None):
    path = Path(path)
    if (path / "model/ramdisk.json").exists():
        model, _ = load_workspace(path)
        compression = compression or model["compression"]["codec"]
    else:
        model = directory_model(path)
        compression = compression or "gzip"
    raw = cpio.pack(model)
    encoded = codecs.encode(raw, compression)
    exclusive(output, encoded)
    receipt = evidence(
        "ramdisk.pack",
        output=output,
        format=compression,
        entries=len(model["entries"]),
        source_workspace=str(path),
        determinism="Canonical CPIO; normalized gzip headers; compressor-version differences possible",
    )
    return {
        "status": "PACKED",
        "sha256": digest(encoded),
        "bytes": len(encoded),
        "receipt_id": receipt["receipt_id"],
    }
