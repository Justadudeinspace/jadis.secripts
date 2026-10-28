"""Private, bounded recovery project state; no database or AI dependency."""

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
from secripts.context import data_dir
from secripts.images.artifacts import read, exclusive
from secripts.receipts import write_json, save
from secripts.safety import SecError


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def directory(name):
    from secripts.recovery.model import name_valid

    return data_dir() / "recovery/projects" / name_valid(name)


def load(name, kind, default=None):
    path = directory(name) / (kind + ".json")
    if not path.exists():
        return default
    try:
        value = json.loads(read(path, 512 * 1024))
        if not isinstance(value, dict) or value.get("schema") != 1:
            raise ValueError()
        return value
    except (ValueError, TypeError, RecursionError) as exc:
        raise SecError("Malformed recovery project state: " + kind, 3) from exc


def store(name, kind, value):
    if len(json.dumps(value).encode()) > 512 * 1024:
        raise SecError("Project state budget exceeded; export/review history", 4)
    write_json(directory(name) / (kind + ".json"), value)


@contextmanager
def locked(name):
    root = directory(name)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(root / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SecError("Recovery project busy", 4) from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def export_file(output, payload):
    path = Path(output)
    if not path.parent.is_dir():
        raise SecError("Export parent must exist", 3)
    exclusive(path, payload.encode())
    return {"path": str(path), "sha256": hashlib.sha256(payload.encode()).hexdigest()}


def status(name):
    from secripts.recovery import model, flags, dependencies
    from secripts.recovery.architecture import graph
    from secripts.recovery.planner import host_qualification
    from secripts.recovery.fstab import report as fstab_report

    device = model.report(name)
    configuration = flags.view(name)
    validation = flags.validate(name, configuration)
    outputs = graph(device, configuration)
    deps = dependencies.validate(name)
    host = host_qualification()
    source = load(name, "dependencies", {}) or {}
    build = load(name, "build", {}) or {}
    fingerprint = digest(
        {
            "model": device,
            "configuration": configuration["configuration_sha256"],
            "lock": source.get("lock_sha256"),
        }
    )
    current = bool(build) and build.get("input_sha256") == fingerprint
    areas = {
        "DEVICE": "PARTIAL" if device["fields"]["codename"]["state"] == "UNKNOWN" else "PASS",
        "FIRMWARE": "PARTIAL" if device.get("artifact_observations") else "UNKNOWN",
        "PARTITION_MODEL": "CONFLICT" if device["conflicts"] else "PARTIAL",
        "RECOVERY_ARCHITECTURE": outputs["status"],
        "AVB_GRAPH": "PARTIAL"
        if device["recovery_architecture"]["avb_relationships"]
        else "UNKNOWN",
        "KERNEL": "PARTIAL"
        if any(
            r["name"] in {"TARGET_PREBUILT_KERNEL", "TARGET_KERNEL_SOURCE"}
            for r in device.get("configuration_evidence", [])
        )
        else "UNKNOWN",
        "FSTAB": fstab_report(device)["status"],
        "DEVICE_TREE": "PARTIAL"
        if any(s["kind"] == "tree" for s in device["sources"])
        else "UNKNOWN",
        "DEPENDENCIES": deps["status"],
        "FLAGS": validation["status"],
        "RECOVERY_SOURCE": "PARTIAL" if source.get("lock", {}).get("source") else "UNKNOWN",
        "BUILD_HOST": host["state"],
        "BUILD": build.get("status", "UNTESTED") if current else "STALE" if build else "UNTESTED",
        "ARTIFACT": "PARTIAL" if current and build.get("artifacts") else "UNTESTED",
        "HARDWARE": "UNTESTED",
    }
    next_command = ["js", "ry", "acquire", "--model", name]
    if not device["sources"]:
        reason = "Collect source/image evidence first"
    elif validation["status"] == "FAIL":
        next_command = ["js", "ry", "flags", "validate", name]
        reason = "Resolve configuration conflicts or invalid combinations"
    elif deps["status"] != "PASS":
        next_command = ["js", "ry", "deps", "validate", name]
        reason = "Resolve pinned dependency/source inputs"
    elif not outputs["targets"]:
        next_command = ["js", "ry", "plan", name]
        reason = "Resolve recovery output evidence"
    else:
        next_command = ["js", "ry", "plan", name]
        reason = "Review host/source/configuration blockers before build"
    result = {
        "schema": 1,
        "model": name,
        "areas": areas,
        "input_sha256": fingerprint,
        "next": {"command": next_command, "reason": reason},
        "hardware_qualification": "UNTESTED",
        "note": "PASS in an input area is limited to its stated check; no global device readiness is inferred",
    }
    store(name, "status", {**result, "updated": now()})
    receipt = save("recovery.status", "READ_ONLY", [], result="PASS", data=result)
    return {**result, "receipt_id": receipt["receipt_id"]}
