"""Local atomic sanitized execution evidence; never a hardware certification."""

import json
import os
import re
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path
from secripts.context import data_dir, host
from secripts.secrets import sanitize_evidence
from secripts.safety import SecError


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("x", encoding="utf-8") as stream:
            os.chmod(temp, 0o600)
            json.dump(sanitize_evidence(value), stream, indent=2, ensure_ascii=True)
            stream.write("\n")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def save(operation: str, risk: str, commands: list, **extra) -> dict:
    value = {
        "receipt_id": uuid.uuid4().hex,
        "operation": operation,
        "operation_version": 1,
        "secripts_version": __import__("secripts").__version__,
        "association": {
            "cwd": str(Path.cwd()),
            "environment": {"python": host()["python"], "architecture": host()["architecture"]},
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": socket.gethostname(),
        "platform": host(),
        "risk": risk,
        "arguments": [],
        "preconditions": [],
        "commands": commands,
        "exit_codes": [c.get("exit_code") for c in commands],
        "duration": sum(c.get("duration", 0) for c in commands),
        "result": "PASS" if all(c.get("result") == "PASS" for c in commands) else "FAIL",
        "artifacts": [],
        "warnings": [],
        **extra,
    }
    value = sanitize_evidence(value)
    for key in ("data", "transformation", "evidence", "analysis"):
        if key in value:
            value[key], truncated = bounded_evidence(value[key])
            if truncated:
                value["warnings"].append(
                    f"{key} evidence truncated to local receipt budget; inspect explicit workspace/report for detail"
                )
    write_json(data_dir() / "receipts" / f"{value['receipt_id']}.json", value)
    return value


def load(receipt_id: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{32}", receipt_id):
        raise SecError("Invalid receipt ID", 2)
    try:
        value = json.loads((data_dir() / "receipts" / f"{receipt_id}.json").read_text())
        if (
            not isinstance(value, dict)
            or value.get("receipt_id") != receipt_id
            or not isinstance(value.get("operation"), str)
            or not isinstance(value.get("commands"), list)
            or not isinstance(value.get("result"), str)
            or not all(isinstance(command, dict) for command in value.get("commands", []))
            or not isinstance(value.get("artifacts", []), list)
            or not all(isinstance(artifact, dict) for artifact in value.get("artifacts", []))
        ):
            raise ValueError()
        return sanitize_evidence(value)
    except (OSError, ValueError) as exc:
        raise SecError("Receipt missing or corrupted", 1) from exc


def history(
    *, operation=None, failed=False, limit=None, since=None, result=None, artifact=None
) -> list:
    root = data_dir() / "receipts"
    records = []
    for path in sorted(root.glob("*.json"), reverse=True):
        try:
            records.append(load(path.stem))
        except SecError:
            records.append({"receipt_id": path.stem, "result": "CORRUPTED"})
    records = sorted(records, key=lambda r: (r.get("timestamp", ""), r["receipt_id"]), reverse=True)
    if since:
        try:
            cutoff = datetime.fromisoformat(since.replace("Z", "+00:00"))
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise SecError("--since requires an ISO date/time", 2) from exc
    filtered = []
    for row in records:
        if operation and row.get("operation") != operation:
            continue
        if result and row.get("result") != result:
            continue
        if failed and row.get("result") not in {
            "FAIL",
            "MISSING",
            "TIMEOUT",
            "REFUSED",
            "CORRUPTED",
        }:
            continue
        if artifact and not any(
            artifact in (a.get("path"), a.get("sha256"))
            for a in row.get("artifacts", [])
            if isinstance(a, dict)
        ):
            continue
        if since:
            try:
                stamp = datetime.fromisoformat(row.get("timestamp", "").replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=timezone.utc)
                if stamp < cutoff:
                    continue
            except ValueError:
                continue
        filtered.append(row)
    if limit is not None and limit < 0:
        raise SecError("--limit must be nonnegative", 2)
    return filtered if limit is None else filtered[:limit]


def latest(*, failed=False):
    records = history(failed=failed, limit=1)
    if not records:
        raise SecError("No matching receipt", 3)
    return records[0]


def summary(value):
    return {
        k: value.get(k)
        for k in (
            "receipt_id",
            "operation",
            "timestamp",
            "result",
            "duration",
            "artifacts",
            "association",
        )
    }


def compare(first, second):
    a = latest() if first == "latest" else load(first)
    b = latest() if second == "latest" else load(second)
    changes = []

    def walk(left, right, path=""):
        if isinstance(left, dict) and isinstance(right, dict):
            for key in sorted(set(left) | set(right)):
                walk(left.get(key), right.get(key), f"{path}/{key}")
        elif left != right:
            changes.append({"path": path, "before": left, "after": right})

    walk(a, b)
    return {
        "first": a["receipt_id"],
        "second": b["receipt_id"],
        "changes": changes,
        "note": "Evidence comparison only; commands are not replayed",
    }


def bounded_evidence(value, limit=128 * 1024):
    """Bound new nested evidence without altering historical receipts or required receipt identity."""
    remaining = limit
    truncated = False
    priority = {
        "status",
        "result",
        "exit_code",
        "sha256",
        "source_sha256",
        "original_sha256",
        "rebuilt_sha256",
        "byte_identity",
        "semantic_equivalence",
        "cryptographic_state",
        "root_of_trust",
        "device_compatibility",
        "signature",
        "expected_key_match",
        "hashtrees",
        "chains",
        "workspace",
        "receipt_id",
    }

    def visit(item, depth=0):
        nonlocal remaining, truncated
        if remaining <= 0 or depth > 12:
            truncated = True
            return "[EVIDENCE_TRUNCATED]"
        if isinstance(item, dict):
            result = {}
            keys = sorted(item, key=lambda key: (str(key) not in priority, str(key)))
            for key in keys[:128]:
                if remaining <= 0:
                    result["_truncated"] = True
                    truncated = True
                    break
                remaining -= len(str(key)) + 8
                result[key] = visit(item[key], depth + 1)
            if len(keys) > 128:
                result["_truncated"] = True
                truncated = True
            return result
        if isinstance(item, (list, tuple)):
            result = []
            for child in item[:256]:
                if remaining <= 0:
                    truncated = True
                    break
                result.append(visit(child, depth + 1))
            if len(result) < len(item):
                result.append({"_truncated_items": len(item) - len(result)})
                truncated = True
            return result
        if isinstance(item, str):
            bound = min(4096, max(0, remaining))
            payload = item.encode("utf-8")
            remaining -= min(len(payload), bound) + 4
            if len(payload) > bound:
                truncated = True
                return payload[:bound].decode("utf-8", errors="ignore") + "[TRUNCATED]"
            return item
        remaining -= 32
        return item

    result = visit(value)
    return result, truncated
