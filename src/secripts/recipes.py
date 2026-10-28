"""Guided read-only preparation workflows; execution uses the normal dispatcher."""

from secripts.operations import execute
from secripts.safety import SecError

RECIPES = {
    "android-dev": {
        "title": "Android development preparation",
        "summary": "Inspect SDK, runtimes and ADB before changing your environment.",
        "operations": ["environment.runtimes", "android.sdk.validate", "adb.version"],
    },
    "git-review": {
        "title": "Git repository review",
        "summary": "Inspect changes, branches, remotes and history before synchronization.",
        "operations": ["git.status", "git.branches", "git.remotes", "git.log"],
    },
    "termux-check": {
        "title": "Termux developer preparation",
        "summary": "Identify host boundaries and missing runtimes; no package upgrades.",
        "operations": ["termux.inspect", "environment.path", "environment.runtimes"],
    },
    "debian-check": {
        "title": "Debian developer preparation",
        "summary": "Inspect build packages and runtimes before installing anything.",
        "operations": ["debian.packages", "environment.runtimes"],
    },
    "device-diagnostic": {
        "title": "Android transport diagnostic",
        "summary": "Enumerate ADB and Fastboot transports without device modification.",
        "operations": ["adb.devices", "fastboot.devices"],
    },
}


def _recipe(title, summary, operations):
    return {"title": title, "summary": summary, "operations": operations}


RECIPES.update(
    {
        "developer-environment": _recipe(
            "Developer environment dossier",
            "Inspect host, runtimes, filesystem and PATH before making changes.",
            [
                "diagnostics.system",
                "filesystem.capacity",
                "python.environment",
                "java.environment",
                "environment.path",
            ],
        ),
        "repository-health": _recipe(
            "Repository health",
            "Inspect worktree, divergence, object storage and submodules.",
            ["git.health", "git.objects", "git.submodules"],
        ),
        "repository-release-readiness": _recipe(
            "Release preparation",
            "Review tracked changes, untracked files, tags and Python build metadata. This does not authorize publishing.",
            ["git.health", "git.changed", "git.untracked", "git.tags", "python.project"],
        ),
        "github-readiness": _recipe(
            "GitHub readiness",
            "Explicit network checks for authentication, repository permissions and workflows.",
            ["github.auth", "github.repository", "github.workflows"],
        ),
        "python-dev": _recipe(
            "Python development health",
            "Inspect interpreter isolation, project metadata, editables and dependency consistency.",
            ["python.environment", "python.project", "python.editables", "python.dependencies"],
        ),
        "android-sdk-health": _recipe(
            "Android SDK health",
            "Inspect SDK components and Java, then platform-tool versions without license acceptance.",
            ["android.sdk.validate", "java.environment", "adb.version", "fastboot.version"],
        ),
        "adb-diagnostics": _recipe(
            "ADB diagnostics",
            "Inspect client and sanitized transports; no device shell commands.",
            ["adb.version", "adb.devices"],
        ),
        "fastboot-diagnostics": _recipe(
            "Fastboot diagnostics",
            "Inspect client and sanitized bootloader enumeration without modifying a device.",
            ["fastboot.version", "fastboot.devices"],
        ),
        "android-device-dossier": _recipe(
            "Android device dossier",
            "Enumerate transports and collect allowlisted observations from one authorized device.",
            ["adb.devices", "adb.inspect"],
        ),
        "proot-dev": _recipe(
            "PRoot development boundaries",
            "Inspect Linux and Termux context plus filesystem evidence without claiming native-host access.",
            ["linux.environment", "termux.inspect", "filesystem.capacity", "environment.path"],
        ),
        "recovery-readiness": _recipe(
            "Recovery readiness",
            "Inspect host/build prerequisites, SDK and JDK; no source synchronization.",
            ["recovery.doctor", "android.sdk.validate", "java.environment"],
        ),
        "twrp-tree-review": _recipe(
            "TWRP tree review",
            "Audit a supplied tree and inspect the host without running makefiles.",
            ["recovery.tree", "recovery.doctor"],
        ),
        "twrp-build-readiness": _recipe(
            "TWRP build preparation",
            "Combine supplied-tree audit, build prerequisites, Java and disk evidence.",
            ["recovery.tree", "recovery.doctor", "java.environment", "filesystem.capacity"],
        ),
        "post-build-verification": _recipe(
            "Post-build static verification",
            "Inspect an artifact and current workspace evidence; hardware qualification remains independent.",
            ["recovery.image", "recovery.doctor"],
        ),
    }
)

RECIPES.update(
    {
        "image-analysis": _recipe(
            "Image analysis",
            "Inspect image structures and optional-provider availability; no providers executed.",
            ["image.inspect", "image.providers"],
        ),
        "recovery-tree-diagnosis": _recipe(
            "Recovery tree diagnosis",
            "Audit and explain unresolved tree/source dependencies.",
            ["recovery.tree", "recovery.diagnose"],
        ),
        "recovery-build-plan": _recipe(
            "Recovery build planning",
            "Inspect model conflicts, host evidence and build blockers.",
            ["recovery.model", "recovery.host", "recovery.plan"],
        ),
        "recovery-tree-derivation": _recipe(
            "Candidate tree derivation",
            "Review model and generate a new traceable candidate, never a build-ready claim.",
            ["recovery.model", "recovery.derive"],
        ),
    }
)


RECIPES.update(
    {
        "artifact-roundtrip": _recipe(
            "Artifact round-trip evidence",
            "Model, reconstruct and compare offline artifacts; no compatibility claim.",
            ["image.model", "image.roundtrip"],
        ),
        "ramdisk-review": _recipe(
            "Ramdisk reconstruction review",
            "Inspect bounded CPIO/compression evidence alongside provider capability.",
            ["ramdisk.inspect", "image.providers"],
        ),
        "avb-evidence": _recipe(
            "AVB verification evidence",
            "Parse native metadata then explicitly verify with optional avbtool; device trust remains unknown.",
            ["avb.inspect", "avb.verify"],
        ),
    }
)


RECIPES.update(
    {
        "recovery-onramp": _recipe(
            "Recovery evidence onramp",
            "Plan acquisition, inspect source declarations and qualify host constraints without a source download.",
            ["recovery.acquire", "recovery.source", "recovery.host"],
        ),
        "build-failure-review": _recipe(
            "Build failure review",
            "Correlate a bounded build log with current source intelligence; symptoms remain hypotheses.",
            ["recovery.build.diagnose", "recovery.source"],
        ),
    }
)


def get(name: str) -> dict:
    from secripts.registry import registry

    if name not in RECIPES:
        raise SecError("Unknown recipe", 2)
    value = {**RECIPES[name]}
    ops = [registry().get(n) for n in value["operations"]]
    value["requires"] = sorted({tool for op in ops for tool in op.requires})
    value["network"] = any(op.network for op in ops)
    value["parameters"] = {
        p.name: {"description": p.description, "required": p.required}
        for op in ops
        for p in op.parameters
    }
    return value


def run(name: str, dry_run: bool = False, parameters=None, network=False) -> dict:
    from secripts.registry import registry
    from secripts.receipts import save
    from secripts.evidence import overall

    recipe = get(name)
    if recipe["network"] and not network and not dry_run:
        raise SecError(
            "Recipe includes network operations; pass --network explicitly or use --dry-run", 4
        )
    parameters = {k: v for k, v in (parameters or {}).items() if v is not None}
    if set(parameters) - set(recipe["parameters"]):
        raise SecError("Unsupported recipe parameter", 2)
    for key, value in recipe["parameters"].items():
        if value["required"] and not parameters.get(key):
            raise SecError(f"Recipe requires --{key}", 2)
    results = []
    for operation_id in recipe["operations"]:
        op = registry().get(operation_id)
        subset = {k: v for k, v in parameters.items() if k in {p.name for p in op.parameters}}
        result = execute(operation_id, dry_run, subset)
        results.append(result)
        if result["exit_code"]:
            break
    code = next((r["exit_code"] for r in results if r["exit_code"]), 0)
    evidence = overall(
        [
            {
                "status": r["data"].get("status", "UNKNOWN")
                if isinstance(r["data"], dict)
                else "UNKNOWN"
            }
            for r in results
        ]
    )
    risks = ["READ_ONLY", "MUTATING", "PRIVILEGED", "DESTRUCTIVE"]
    parent_risk = max(
        (registry().get(identifier).risk for identifier in recipe["operations"]), key=risks.index
    )
    receipt = save(
        "recipe." + name,
        parent_risk,
        [],
        result="FAIL" if code else "DRY_RUN" if dry_run else "PASS",
        step_receipts=[r["receipt_id"] for r in results],
        evidence_status=evidence,
        warnings=["Invocation success is not full environment or hardware qualification"],
    )
    return {
        "recipe": recipe["title"],
        "steps": results,
        "status": evidence,
        "receipt_id": receipt["receipt_id"],
        "exit_code": code,
    }
