"""Evidence-backed candidate derivation and build planning; no sync, build or device action."""

from pathlib import Path
import os
import platform
import re
import shutil
import tempfile
from secripts.context import host
from secripts.receipts import write_json, save
from secripts.safety import SecError
from secripts.recovery import model


def target_for(device, configuration=None):
    from secripts.recovery.architecture import graph

    outputs = graph(device, configuration)
    targets = outputs["targets"]
    return {
        "target": targets[0] if len(targets) == 1 and not outputs["blockers"] else "UNKNOWN",
        "targets": targets,
        "state": "CONFLICT" if device.get("conflicts") else "DERIVED" if targets else "UNKNOWN",
        "graph": outputs,
        "reason": "Compatibility single-target view only; authoritative targets come from independent output relationships",
    }


def diagnose(path):
    from secripts.recovery.inspection import audit_tree

    audit = audit_tree(Path(path))
    g = audit["dependency_graph"]
    direct = [
        d
        for d in g["declarations"]
        if d["state"] in ("DIRECTLY_DECLARED", "STATICALLY_RESOLVED") and not d["conditional"]
    ]
    products = [d for d in direct if d["name"] == "PRODUCT_NAME"]
    conventions = sorted(
        {
            "twrp"
            if d["value"].startswith("twrp_")
            else "omni"
            if d["value"].startswith("omni_")
            else "other"
            for d in products
        }
    )
    unresolved = [e for e in g["edges"] if e["state"] != "STATICALLY_RESOLVED"]
    blockers = []
    if not g["groups"]["architecture"]:
        blockers.append("Architecture is not declared locally")
    if not products:
        blockers.append("Product identity requires external or unresolved Make configuration")
    if not g["groups"]["kernel_dtb"]:
        blockers.append("Kernel/prebuilt/DTB relationship is unresolved")
    if unresolved:
        blockers.append(f"{len(unresolved)} dependency references need resolution")
    if not any("fstab" in name for name in audit["files"]):
        blockers.append("No local recovery fstab evidence")
    if g["cycles"]:
        blockers.append("Static dependency graph contains cycles")
    return {
        "schema": 1,
        "audit": audit,
        "generation": {
            "conventions": conventions,
            "state": "DECLARED" if products else "UNKNOWN",
            "android_base": "UNKNOWN",
            "note": "omni/twrp prefixes alone do not prove source/Android generation",
        },
        "identity": products,
        "readiness": "BLOCKED" if blockers else "REVIEW_REQUIRED",
        "blockers": blockers,
        "next_actions": [
            "Resolve external dependencies and kernel provenance",
            "Review fstab/encryption and source generation",
            "Compilation and hardware qualification remain separate",
        ],
    }


def derive(name, output, dry_run=False):
    device = model.report(name)
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise SecError("Candidate output must not exist; no overwrite", 4)
    if not output.parent.is_dir():
        raise SecError("Candidate parent directory must already exist", 3)
    architecture = device["fields"]["architecture"]
    codename = device["fields"]["codename"]
    if architecture["state"] in ("UNKNOWN", "CONFLICT") or architecture["value"] not in {
        "arm",
        "arm64",
        "x86",
        "x86_64",
    }:
        raise SecError(
            "Candidate derivation requires unambiguous supported architecture evidence", 3
        )
    code = codename["value"] if codename["state"] not in ("UNKNOWN", "CONFLICT") else name
    if not isinstance(code, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", code):
        raise SecError("Unsafe codename; Make syntax injection refused", 4)
    from secripts.recovery import flags as build_flags
    from secripts.recovery.fstab import generate as generate_fstab

    configuration = build_flags.view(name)
    target = target_for(device, configuration)
    provenance = []
    files = {}

    def generated(filename, lines):
        text = ["# JADIS // SECRIPTS — CANDIDATE ONLY; NOT BUILD READY"]
        for line, evidence, reason in lines:
            text.append(line)
            provenance.append(
                {
                    "file": filename,
                    "line": len(text),
                    "text": line,
                    "evidence": evidence,
                    "state": "CANDIDATE",
                    "requires_review": True,
                    "reason": reason,
                }
            )
        files[filename] = "\n".join(text) + "\n"

    board_text, board_provenance = build_flags.make(configuration)
    files["BoardConfig.mk"] = board_text
    for row in board_provenance:
        row.update(
            file="BoardConfig.mk",
            text=board_text.splitlines()[row["line"] - 1],
            evidence=row.get("observed", {}).get("evidence", [])
            or row.get("derived", {}).get("evidence", []),
            state=row["source"],
            requires_review=True,
            reason="Source-linked effective configuration; an override is not evidence",
        )
        provenance.append(row)
    generated(
        "AndroidProducts.mk",
        [
            (
                f"PRODUCT_MAKEFILES := $(LOCAL_DIR)/twrp_{code}.mk",
                [],
                "Local generated product relationship",
            )
        ],
    )
    generated(
        f"twrp_{code}.mk",
        [
            (
                "$(call inherit-product, $(LOCAL_DIR)/device.mk)",
                [],
                "Candidate local device makefile",
            ),
            (
                f"PRODUCT_NAME := twrp_{code}",
                codename["evidence"],
                "Candidate product convention; not a source-generation claim",
            ),
            (
                f"PRODUCT_DEVICE := {code}",
                codename["evidence"],
                "Codename evidence or explicit model-name fallback",
            ),
        ],
    )
    generated(
        "device.mk",
        [
            (
                "# TODO: review common tree, kernel, vendor and recovery root dependencies",
                [],
                "No dependencies guessed",
            )
        ],
    )
    fstab_text, fstab_review = generate_fstab(device)
    if fstab_text:
        files["recovery.fstab"] = fstab_text
        for number, entry in enumerate(fstab_review["entries"], 1):
            provenance.append(
                {
                    "file": "recovery.fstab",
                    "line": number,
                    "state": entry["state"],
                    "evidence": [entry],
                    "requires_review": True,
                    "reason": "Preserved mount declaration; no block paths guessed",
                }
            )
    else:
        files["recovery.fstab"] = "# UNRESOLVED: no unambiguous source fstab; no paths guessed\n"
    from secripts.recovery.dependencies import graph as dependency_graph

    dependencies = dependency_graph(name)
    files["dependencies.json"] = (
        __import__("json").dumps(
            {"schema": 1, "reviewed": dependencies["nodes"], "unresolved": dependencies["edges"]},
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    files["manifest-snippet.xml"] = (
        "<!-- REVIEW REQUIRED: pinned dependency declarations; select explicit upstream remotes -->\n<manifest>\n"
        + "".join(
            f'  <project name="{node["repository"].removeprefix("https://github.com/")}" path="{node["path"]}" revision="{node["revision"]}" remote="github" />\n'
            for node in dependencies["nodes"]
        )
        + "</manifest>\n"
    )
    manifest = {
        "schema": 1,
        "status": "CANDIDATE",
        "model": name,
        "sources": device["sources"],
        "generated_lines": provenance,
        "configuration_sha256": configuration["configuration_sha256"],
        "flag_validation": build_flags.validate(name, configuration),
        "recovery_architecture": device["recovery_architecture"],
        "build_graph": target["graph"],
        "fstab_review": fstab_review,
        "dependency_graph": dependencies,
        "build_target_candidate": target,
        "unresolved": [
            "Kernel source/prebuilt",
            "Partition sizes and fstab",
            "Common/vendor trees",
            "Source generation/JDK",
            "AVB/encryption behavior",
            "Hardware qualification",
        ],
        "conflicts": device["conflicts"],
        "review_states": {
            "RESOLVED": ["Generated local file relationships"],
            "INFERRED": ["Candidate product naming; source generation requires review"],
            "CONFLICT": device["conflicts"],
            "UNKNOWN": ["Kernel, fstab, vendor and source compatibility"],
            "BLOCKED": ["Build readiness not established"],
            "REQUIRES_REVIEW": ["Every generated configuration line"],
        },
        "review_required": True,
    }
    if dry_run:
        return {"result": "DRY_RUN", "files": sorted(files), "manifest": manifest}
    # Assemble privately, then atomically rename without overwriting an existing destination.
    with tempfile.TemporaryDirectory(prefix=".secripts-candidate-", dir=output.parent) as directory:
        staging = Path(directory) / "candidate"
        staging.mkdir(mode=0o700)
        for filename, text in files.items():
            (staging / filename).write_text(text)
        write_json(staging / "candidate.json", manifest)
        (staging / "REVIEW.md").write_text(
            "# CANDIDATE — NOT BUILD READY\n\n"
            + "\n".join("- [ ] " + item for item in manifest["unresolved"])
            + "\n"
        )
        # mkdir reserves the destination exclusively; only our newly created empty directory is replaced.
        output.mkdir(mode=0o700)
        try:
            os.replace(staging, output)
        except OSError:
            output.rmdir()
            raise
    receipt = save(
        "recovery.tree.derive",
        "MUTATING",
        [],
        result="CANDIDATE",
        artifacts=[{"path": str(output.resolve())}],
        model=name,
    )
    return {
        "result": "CANDIDATE",
        "output": str(output.resolve()),
        "receipt_id": receipt["receipt_id"],
        "manifest": manifest,
    }


def host_qualification():
    from secripts.recovery.workspace import recovery_doctor

    checks = recovery_doctor()
    memory = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                memory = int(line.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    constraints = []
    if host()["architecture"] != "x86_64":
        constraints.append("Current backend has no qualified non-x86_64 build path")
    if shutil.disk_usage(Path.cwd()).free < 40 * 1024**3:
        constraints.append("Free disk below 40 GiB floor")
    if memory is None:
        constraints.append("Memory capacity unknown")
    elif memory < 8 * 1024**3:
        constraints.append("RAM below conservative 8 GiB planning floor")
    if host()["termux"]:
        constraints.append("Native Termux build environment is unqualified")
    if not shutil.which("repo"):
        constraints.append("repo launcher missing")
    return {
        "state": "HOST_BLOCKED" if constraints else "HOST_UNTESTED",
        "constraints": constraints,
        "memory_bytes": memory,
        "architecture": platform.machine(),
        "prerequisites": checks,
        "filesystem_semantics": "UNKNOWN: no implicit write probe",
        "proot": host()["proot"],
        "note": "Presence of prerequisites is not host build qualification",
        "external_host_reference": {
            "source": "host",
            "platform": "x86_64 glibc Linux",
            "full_aosp_disk_gb": 400,
            "full_aosp_ram_gb": 64,
            "scope": "Current full AOSP guidance; reduced recovery requirements must be measured per checkout",
            "tools": [
                "git",
                "repo",
                "Python",
                "branch-selected JDK",
                "make",
                "C/C++ build packages",
            ],
            "early_rejection_floor_only": "40 GiB disk / 8 GiB RAM are not readiness qualification",
        },
    }


def plan(name):
    from secripts.recovery.workspace import load_workspace

    device = model.report(name)
    from secripts.recovery import flags as build_flags
    from secripts.recovery.dependencies import validate as dependency_validation

    configuration = build_flags.view(name)
    validation = build_flags.validate(name, configuration)
    target = target_for(device, configuration)
    host_state = host_qualification()
    try:
        workspace = load_workspace()
    except SecError as exc:
        workspace = {"state": "UNKNOWN", "reason": str(exc)}
    tree = (
        diagnose(workspace["tree"])
        if workspace.get("tree") and Path(workspace["tree"]).is_dir()
        else None
    )
    blockers = list(host_state["constraints"])
    blockers.extend(target["graph"]["blockers"])
    if validation["status"] == "FAIL":
        blockers.extend(
            f["reason"]
            for f in validation["findings"]
            if f["state"]
            in {"INVALID_COMBINATION", "MISSING_DEPENDENCY", "UNSUPPORTED_FOR_SOURCE_GENERATION"}
        )
    deps = dependency_validation(name)
    blockers.extend(deps["blockers"])
    blockers.extend("Conflicting model field: " + key for key in device["conflicts"])
    if not workspace.get("manifest"):
        blockers.append("Source manifest/checkout not configured")
    if not tree:
        blockers.append("Device tree not available in configured workspace")
    else:
        blockers.extend(tree["blockers"])
    value = {
        "schema": 1,
        "model": name,
        "status": "BLOCKED" if blockers else "REVIEW_REQUIRED",
        "host": host_state,
        "source": workspace,
        "source_generation": source_intelligence(workspace),
        "expected_java": "See source_generation.toolchains; declared prebuilts do not prove active selection",
        "device": device,
        "tree": tree,
        "build_target": target,
        "build_graph": target["graph"],
        "required_build_targets": target["targets"],
        "configuration": configuration,
        "flag_validation": validation,
        "dependencies": deps,
        "blockers": blockers,
        "next_actions": [
            "Resolve every unknown/conflict with source evidence",
            "Select/pin upstream source and complete kernel/common/vendor dependencies",
            "Review candidate tree; qualify a suitable host",
            "Only then compile; hardware tests remain separate",
        ],
        "actual_build": "BLOCKED",
        "hardware_qualification": "UNTESTED",
    }
    receipt = save(
        "recovery.plan",
        "READ_ONLY",
        [],
        result="PASS",
        evidence_status=value["status"],
        model=name,
        unresolved=blockers,
    )
    value["receipt_id"] = receipt["receipt_id"]
    return value


def source_intelligence(workspace):
    import xml.etree.ElementTree as ET

    result = {
        "manifest_selection": workspace.get("manifest"),
        "revision_selection": workspace.get("revision"),
        "android_base": "UNKNOWN",
        "product_convention": "UNKNOWN",
        "java_requirement": "UNKNOWN",
        "state": "UNKNOWN",
        "evidence": [],
    }
    manifest = None
    root = Path(workspace.get("root", "/nonexistent"))
    path = root / ".repo/manifests/default.xml"
    if not path.is_file():
        path = root / "default.xml"
    if path.is_file() and not path.is_symlink() and path.stat().st_size <= 1024 * 1024:
        from secripts.images.artifacts import read

        text = read(path, 1024 * 1024).decode("utf-8", errors="replace")
        if any(marker in text for marker in ("<!DOCTYPE", "<!ENTITY", "\0")):
            return {**result, "state": "BLOCKED", "reason": "Unsafe XML constructs"}
        try:
            manifest = ET.fromstring(text)  # noqa: S314 -- bounded text with DTD/entities/NUL refused
        except ET.ParseError:
            return {**result, "state": "UNKNOWN", "reason": "Malformed manifest"}
        default = manifest.find("default")
        revision = default.get("revision") if default is not None else None
        result["evidence"].append(
            {
                "path": str(path),
                "sha256": __import__(
                    "secripts.images.common", fromlist=["artifact_hash"]
                ).artifact_hash(path),
                "default_revision": revision,
            }
        )
        if revision and "android-" in revision:
            result["android_base"] = {"value": revision, "state": "DECLARED"}
        result["state"] = "DECLARED"
    selection = workspace.get("manifest", "")
    if "twrp_aosp" in selection:
        result["product_convention"] = {
            "value": "twrp_",
            "state": "INFERRED",
            "reason": "Selected manifest family, not filename-only device compatibility",
        }
    elif "twrp_omni" in selection:
        result["product_convention"] = {
            "value": "omni_ or branch-specific",
            "state": "INFERRED",
            "reason": "Historical manifest family; review actual product definitions",
        }
    result["toolchains"] = []
    result["requirements_state"] = "UNKNOWN"
    if manifest is not None:
        for project in manifest.findall("project")[:4096]:
            location = project.get("path", "")
            if re.fullmatch(r"prebuilts/(?:jdk/[A-Za-z0-9_-]+|python/[A-Za-z0-9_/-]+)", location):
                result["toolchains"].append(
                    {
                        "path": location,
                        "revision": project.get("revision"),
                        "state": "DECLARED",
                        "source": str(path),
                        "active_selection": "UNKNOWN",
                    }
                )
    result["research_options"] = [
        {
            "family": "TWRP AOSP",
            "branch": "twrp-12.1",
            "source": "twrp-12",
            "product_hint": "twrp_",
            "target": "Arrangement-dependent: recoveryimage/bootimage/vendorbootimage",
            "encryption": "Branch README excludes FDE; FBE requires device evidence",
            "compatibility": "UNTESTED",
        },
        {
            "family": "TWRP AOSP",
            "branch": "twrp-11",
            "source": "twrp-11",
            "compatibility": "UNTESTED",
        },
        {
            "family": "TWRP Omni",
            "branch": "twrp-9.0",
            "source": "twrp-omni",
            "product_hint": "omni_",
            "compatibility": "UNTESTED",
        },
    ]
    result["selection_policy"] = (
        "Research options are review candidates, never automatic source selection from Android version. Check local build configuration for active JDK/Python."
    )
    return result
