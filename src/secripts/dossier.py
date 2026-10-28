"""Fast cohesive local snapshot; network and device interrogation are never implicit."""

from datetime import datetime, timezone
from pathlib import Path
import shutil
from secripts.context import data_dir, host
from secripts.evidence import Collector, observation
from secripts import inspectors


def state():
    from secripts.receipts import history, summary
    from secripts.recipes import RECIPES
    from secripts.registry import registry

    records = history()
    failed = next(
        (
            r
            for r in records
            if r.get("result") in {"FAIL", "TIMEOUT", "MISSING", "REFUSED", "CORRUPTED"}
        ),
        None,
    )
    return {
        "operations": len(registry().operations),
        "recipes": len(RECIPES),
        "receipts": len(records),
        "latest": summary(records[0]) if records else None,
        "last_failure": summary(failed) if failed else None,
        "data_directory": str(data_dir()),
    }


def recovery_state():
    # No compiler launch or source scan in a dashboard snapshot.
    from secripts.recovery.workspace import load_workspace
    from secripts.safety import SecError

    try:
        workspace = load_workspace()
    except SecError as exc:
        workspace = {"status": "BLOCKED", "reason": str(exc)}
    reasons = []
    if host()["architecture"] != "x86_64":
        reasons.append("Backend requires x86_64 for qualified build orchestration")
    if shutil.disk_usage(Path.cwd()).free < 40 * 1024**3:
        reasons.append("Below 40 GiB free-space floor")
    if not shutil.which("repo"):
        reasons.append("repo launcher missing")
    if workspace.get("status") == "BLOCKED":
        reasons.append("Workspace not configured/usable")
    return {
        "backend": "TWRP",
        "workspace": workspace,
        "build_host": observation(
            "BLOCKED" if reasons else "UNKNOWN",
            reasons,
            "No source/build/hardware qualification inferred from prerequisites",
        ),
        "hardware": "UNTESTED",
    }


def dossier(*, devices=False):
    c = Collector()
    sections = {
        "host": host(),
        "filesystem": inspectors.filesystem(),
        "termux": inspectors.termux(),
        "linux": inspectors.linux(),
        "development": inspectors.tools(("git", "python3", "java", "adb", "fastboot", "repo")),
        "repository": inspectors.git_health(c),
        "github": observation(
            "UNTESTED",
            shutil.which("gh"),
            "No network/auth probe; invoke github operations explicitly",
        ),
        "python": inspectors.python_environment(),
        "java": {
            "tools": inspectors.tools(("java", "javac", "gradle", "mvn")),
            "version": "UNTESTED: use java.environment",
        },
        "android_sdk": inspectors.sdk(),
        "models": inspectors.models(),
        "network": inspectors.network(),
        "secripts": state(),
        "recovery": recovery_state(),
        "image_lab": laboratory_state(),
    }
    if devices:
        from secripts.devices import transport_summary

        sections["devices"] = {name: transport_summary(c, name) for name in ("adb", "fastboot")}
    else:
        sections["devices"] = {
            name: observation("UNTESTED", None, "Not enumerated; use --devices")
            for name in ("adb", "fastboot")
        }
    return {
        "schema": 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "EVIDENCE_COLLECTED",
        "sections": sections,
        "network_probes": "NOT_RUN",
        "hardware_qualification": "UNTESTED",
    }


def laboratory_state():
    from secripts.images.engine import FORMATS
    from secripts.images.providers import availability
    from secripts.recovery.model import catalog
    from secripts.receipts import history

    return {
        "formats": list(FORMATS),
        "providers": availability(),
        "device_models": catalog(),
        "recent_inspections": len(history(operation="image.inspect", limit=10)),
        "candidate_trees": len(history(operation="recovery.tree.derive")),
        "build_plans": len(history(operation="recovery.plan")),
        "hardware_qualification": "UNTESTED",
    }
