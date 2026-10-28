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


def report(artifact: Path, device: str | None = None, *, tree=None, device_evidence=None) -> dict:
    from secripts.recovery.inspection import audit_tree
    from secripts.recovery.workspace import load_workspace
    from secripts.receipts import history
    from secripts.secrets import sanitize_evidence

    image = inspect_image(artifact)
    digest = image["sha256"]
    qualification_path = data_dir() / "recovery/qualifications" / f"{digest}.json"
    if qualification_path.is_file():
        try:
            qualification = json.loads(qualification_path.read_text())
            if (
                not isinstance(qualification, dict)
                or qualification.get("artifact_sha256") != digest
                or set(qualification.get("areas", {})) != set(AREAS)
            ):
                raise ValueError("Invalid qualification shape")
            if device and qualification.get("device") != device:
                raise SecError("Qualification device does not match requested identity", 4)
        except (OSError, ValueError) as exc:
            raise SecError("Corrupted qualification record", 1) from exc
    else:
        qualification = {
            "artifact_sha256": digest,
            "device": device or "UNSPECIFIED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "areas": {
                key: {"severity": severity, "state": "UNTESTED", "note": ""}
                for key, severity in AREAS.items()
            },
            "method": "No hardware attestation recorded",
        }
    builds = history(operation="recovery.build", artifact=digest)
    build = next((entry for entry in builds if entry.get("result") == "BUILD_SUCCESS"), None)
    # Backwards-compatible latest-build evidence is still hash-bound.
    build_file = data_dir() / "recovery/latest-build.json"
    if build is None and build_file.is_file():
        try:
            candidate = json.loads(build_file.read_text())
            if candidate.get("result") == "BUILD_SUCCESS" and any(
                a.get("sha256") == digest for a in candidate.get("artifacts", [])
            ):
                build = candidate
        except (OSError, ValueError, AttributeError):
            pass
    try:
        workspace = load_workspace()
    except SecError as exc:
        workspace = {"status": "BLOCKED", "reason": str(exc)}
    tree_path = Path(tree) if tree else Path(workspace["tree"]) if workspace.get("tree") else None
    if tree and not tree_path.is_dir():
        raise SecError("Explicit report tree does not exist", 3)
    audit = audit_tree(tree_path) if tree_path and tree_path.is_dir() else None
    evidence = None
    if device_evidence:
        path = Path(device_evidence)
        if not path.is_file() or path.stat().st_size > 1024 * 1024:
            raise SecError("Device evidence must be a JSON file under 1 MiB", 2)
        try:
            evidence = json.loads(path.read_text())
            evidence = evidence.get("data", evidence)
            if (
                not isinstance(evidence, dict)
                or evidence.get("schema") != 1
                or evidence.get("transport") not in ("adb", "fastboot")
            ):
                raise ValueError()
        except (OSError, ValueError, AttributeError) as exc:
            raise SecError("Malformed explicit device dossier", 2) from exc
    untested = [k for k, v in qualification["areas"].items() if v.get("state") == "UNTESTED"]
    failures = [k for k, v in qualification["areas"].items() if v.get("state") == "FAIL"]
    states = {
        "source": "RECORDED_BUILD_LOCK" if build else "UNKNOWN",
        "tree": "STATIC_REVIEW_REQUIRED"
        if audit and audit["result"] != "FAIL"
        else "FAIL"
        if audit
        else "UNTESTED",
        "build": "BUILD_SUCCESS" if build else "UNTESTED",
        "image_structure": image["structure_status"],
        "avb_signature": "UNTESTED",
        "device_tested": "MANUAL_OBSERVATIONS"
        if any(v.get("state") in ("PASS", "FAIL") for v in qualification["areas"].values())
        else "UNTESTED",
        "device_qualified": "BLOCKED" if failures else "UNTESTED",
    }
    unresolved = [
        edge
        for edge in (audit or {}).get("dependency_graph", {}).get("edges", [])
        if edge["state"] != "STATICALLY_RESOLVED"
    ]
    return sanitize_evidence(
        {
            "schema": 2,
            "qualification": qualification,
            "image_evidence": image,
            "workspace": workspace,
            "tree_audit": audit,
            "tree_audit_origin": "EXPLICIT_CURRENT_PATH"
            if tree
            else "CURRENT_WORKSPACE"
            if audit
            else "UNAVAILABLE",
            "tree_audit_note": "Current snapshot; does not prove which files produced an existing artifact",
            "dependency_findings": unresolved,
            "build": build,
            "device_evidence": evidence,
            "device_evidence_origin": "EXPLICIT_USER_SUPPLIED" if evidence else "NOT_COLLECTED",
            "source_revisions": {
                "manifest": (build or {}).get("configuration", {}).get("revision", "UNKNOWN"),
                "tree": (build or {}).get("tree_revision", "UNKNOWN"),
            },
            "static_verification": "Structure and untrusted metadata only; no signature/compatibility validation",
            "evidence_states": states,
            "untested": untested,
            "failures": failures,
            "unresolved": unresolved,
            "blockers": ([workspace["reason"]] if workspace.get("status") == "BLOCKED" else [])
            + failures,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


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
    lines += ["", "## Separate evidence states", ""]
    for key, state in value["evidence_states"].items():
        lines.append(f"- {key}: {state}")
    lines += [
        "",
        f"Unresolved dependencies: {len(value['unresolved'])}",
        f"Blockers: {value['blockers']}",
        f"Workspace: {value['workspace']}",
        f"Image: {value['image_evidence']['type']} / {value['image_evidence']['structure_status']}",
        f"AVB declarations: {value['image_evidence']['avb']['status']}; signature UNTESTED",
        f"Explicit device evidence: {value['device_evidence_origin']}",
    ]
    lines += [
        "",
        f"Source revisions: {value['source_revisions']}",
        f"Static verification: {value['static_verification']}",
    ]
    return "\n".join(lines)
