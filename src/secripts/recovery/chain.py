"""Bind build inputs to configuration actually declared in the selected tree."""

from pathlib import Path
from secripts.recovery import model, flags, projects, dependencies
from secripts.recovery.architecture import graph
from secripts.recovery.inspection import audit_tree
from secripts.recovery.planner import host_qualification
from secripts.images.engine import inspect as inspect_artifact
from secripts.safety import SecError


def fingerprint(name):
    device = model.report(name)
    configuration = flags.view(name)
    source = projects.load(name, "dependencies", {}) or {}
    return projects.digest(
        {
            "model": device,
            "configuration": configuration["configuration_sha256"],
            "lock": source.get("lock_sha256"),
        }
    )


def prepare(name, workspace):
    device = model.report(name)
    configuration = flags.view(name)
    validation = flags.validate(name, configuration)
    outputs = graph(device, configuration)
    deps = dependencies.validate(name)
    host = host_qualification()
    blockers = list(outputs["blockers"])
    if validation["status"] != "PASS":
        blockers.append("Flag configuration requires review: " + validation["status"])
    if deps["status"] != "PASS":
        blockers.extend(deps["blockers"])
    if host["state"] == "HOST_BLOCKED":
        blockers.extend(host["constraints"])
    if sorted(workspace["targets"]) != sorted(outputs["targets"]):
        blockers.append("Workspace targets differ from the evidence-backed output graph")
    actual = audit_tree(Path(workspace["tree"]))
    declarations = actual["dependency_graph"]["declarations"]
    # Stored choices do not change a checkout. Only literal matching declarations are accepted.
    for key, row in configuration["flags"].items():
        if row["user_override"] is None:
            continue
        found = []
        for declaration in declarations:
            if (
                declaration.get("name") != key
                or declaration.get("conditional")
                or declaration.get("state") not in {"DIRECTLY_DECLARED", "STATICALLY_RESOLVED"}
            ):
                continue
            try:
                found.append(
                    flags.normalize(
                        flags.spec(key), declaration.get("resolved_value", declaration.get("value"))
                    )
                )
            except (SecError, TypeError, ValueError):
                continue
        if not found or any(value != row["effective"]["value"] for value in found):
            blockers.append("Override not proven applied in build tree: " + key)
    lock = projects.load(name, "dependencies", {}) or {}
    source = lock.get("lock", {}).get("source", {})
    from secripts.runner import run_command

    tree_revision = run_command(["git", "-C", workspace["tree"], "rev-parse", "HEAD"], timeout=10)
    tree_clean = run_command(
        ["git", "-C", workspace["tree"], "status", "--porcelain", "--untracked-files=all"],
        timeout=10,
    )
    expected = [
        r["revision"] for r in lock.get("lock", {}).get("dependencies", []) if r["role"] == "device"
    ]
    if tree_revision["result"] != "PASS" or tree_revision["stdout"].strip() not in expected:
        blockers.append("Actual build tree revision not matched to reviewed device pin")
    if tree_clean["result"] != "PASS" or tree_clean["stdout"].strip():
        blockers.append(
            "Actual build tree has unreviewed/uncommitted changes; pin reviewed modifications"
        )
    if workspace.get("revision") != source.get("revision") or workspace.get(
        "manifest"
    ) != source.get("manifest"):
        blockers.append("Workspace source does not match pinned source contract")
    return {
        "schema": 1,
        "model": name,
        "input_sha256": fingerprint(name),
        "architecture": device["recovery_architecture"],
        "build_graph": outputs,
        "configuration_sha256": configuration["configuration_sha256"],
        "dependencies": deps,
        "source": source,
        "actual_tree_revision": tree_revision["stdout"].strip(),
        "actual_tree_configuration_hashes": actual["configuration_hashes"],
        "host": host,
        "blockers": sorted(set(blockers)),
        "hardware_qualification": "UNTESTED",
    }


def complete(name, chain, receipt, artifacts, output):
    inspections = []
    for artifact in artifacts:
        inspections.append(inspect_artifact(Path(artifact["path"])))
    result = {
        "schema": 1,
        "model": name,
        "input_sha256": chain["input_sha256"],
        "status": "PASS" if receipt["result"] == "BUILD_SUCCESS" else "FAIL",
        "receipt_id": receipt["receipt_id"],
        "chain": chain,
        "artifacts": artifacts,
        "inspections": inspections,
        "hardware_qualification": "UNTESTED",
        "updated": projects.now(),
    }
    with projects.locked(name):
        projects.store(name, "build", result)
    from secripts.receipts import write_json

    write_json(output / "evidence-chain.json", result)
    return result
