"""Manual attestation bound to an artifact hash and operator-supplied device identity."""

from datetime import datetime, timezone
import json
from pathlib import Path
from secripts.context import data_dir, host
from secripts.receipts import write_json
from secripts.recovery.inspection import artifact_hash, inspect_image
from secripts.safety import SecError

STATES = {"PASS", "FAIL", "SKIPPED", "BLOCKED", "UNTESTED"}
AREAS = {
    "boot": "BLOCKING",
    "display": "BLOCKING",
    "touch": "BLOCKING",
    "adb": "BLOCKING",
    "reboot-system": "BLOCKING",
    "reboot-bootloader": "MINOR",
    "reboot-recovery": "MINOR",
    "backup": "BLOCKING",
    "restore": "BLOCKING",
    "sideload": "MAJOR",
    "filesystem": "MAJOR",
    "data-decryption": "MAJOR",
    "mtp": "MINOR",
    "usb-otg": "MAJOR",
    "battery": "MINOR",
    "temperature": "MINOR",
    "brightness": "MINOR",
    "vibration": "MINOR",
    "stability": "MAJOR",
}


def record(
    artifact: Path, device: str, area: str | None = None, state: str | None = None, note: str = ""
) -> dict:
    if not artifact.is_file():
        raise SecError("Qualification requires an existing artifact", 3)
    if not device.strip():
        raise SecError("Explicit device identity required", 2)
    digest = artifact_hash(artifact)
    path = data_dir() / "recovery/qualifications" / f"{digest}.json"
    if path.exists():
        try:
            value = json.loads(path.read_text())
        except (ValueError, OSError) as exc:
            raise SecError("Corrupted qualification record", 1) from exc
        if value["device"] != device:
            raise SecError("Existing qualification belongs to a different device", 4)
    else:
        value = {
            "artifact_sha256": digest,
            "device": device,
            "environment": host(),
            "areas": {
                k: {"severity": v, "state": "UNTESTED", "note": ""} for k, v in AREAS.items()
            },
            "method": "Operator attestation; not automated hardware certification",
        }
    if area is not None:
        if area not in AREAS or state not in STATES:
            raise SecError("Unknown qualification area or state", 2)
        if not note.strip():
            raise SecError("An observation/evidence note is required for recorded states", 2)
        value["areas"][area].update(state=state, note=note)
    value["timestamp"] = datetime.now(timezone.utc).isoformat()
    write_json(path, value)
    return value


def report(artifact: Path, device: str) -> dict:
    qualification = record(artifact, device)
    build_file = data_dir() / "recovery/latest-build.json"
    build = None
    if build_file.exists():
        try:
            candidate = json.loads(build_file.read_text())
            if any(a["sha256"] == qualification["artifact_sha256"] for a in candidate["artifacts"]):
                build = candidate
        except (ValueError, KeyError):
            pass
    return {
        "qualification": qualification,
        "image_evidence": inspect_image(artifact),
        "build": build,
        "source_revisions": "See build commands and sources.lock.xml" if build else "UNKNOWN",
        "static_verification": "Not a signature/compatibility validation",
        "untested": [k for k, v in qualification["areas"].items() if v["state"] == "UNTESTED"],
        "failures": [k for k, v in qualification["areas"].items() if v["state"] == "FAIL"],
    }


def markdown(value: dict) -> str:
    q = value["qualification"]
    lines = [
        "# JADIS // Recovery qualification",
        "",
        f"Device: {q['device']}",
        f"Artifact SHA256: {q['artifact_sha256']}",
        f"Timestamp: {q['timestamp']}",
        "",
        q["method"],
        "",
        "| Area | Severity | State | Observation |",
        "|---|---|---|---|",
    ]
    for k, v in q["areas"].items():
        note = v["note"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {k} | {v['severity']} | {v['state']} | {note} |")
    lines += [
        "",
        f"Source revisions: {value['source_revisions']}",
        f"Static verification: {value['static_verification']}",
    ]
    return "\n".join(lines)
