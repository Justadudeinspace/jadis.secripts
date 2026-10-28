"""Local atomic sanitized execution evidence; never a hardware certification."""

import json
import os
import re
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path
from secripts.context import data_dir, host
from secripts.secrets import redact
from secripts.safety import SecError


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("x", encoding="utf-8") as stream:
            os.chmod(temp, 0o600)
            json.dump(redact(value), stream, indent=2, ensure_ascii=True)
            stream.write("\n")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def save(operation: str, risk: str, commands: list, **extra) -> dict:
    value = {
        "receipt_id": uuid.uuid4().hex,
        "operation": operation,
        "operation_version": 1,
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
    value = redact(value)
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
        ):
            raise ValueError()
        return redact(value)
    except (OSError, ValueError) as exc:
        raise SecError("Receipt missing or corrupted", 1) from exc


def history() -> list:
    root = data_dir() / "receipts"
    records = []
    for path in sorted(root.glob("*.json"), reverse=True):
        try:
            records.append(load(path.stem))
        except SecError:
            records.append({"receipt_id": path.stem, "result": "CORRUPTED"})
    return sorted(records, key=lambda r: r.get("timestamp", ""), reverse=True)
