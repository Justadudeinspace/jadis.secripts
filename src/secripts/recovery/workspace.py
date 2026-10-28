"""Explicit source selection, bounded jobs, locks and collected build evidence."""

from datetime import datetime, timezone
from functools import wraps
import fcntl
import json
from pathlib import Path
import re
import shutil
from secripts.context import data_dir, host
from secripts.doctor import doctor
from secripts.receipts import save, write_json
from secripts.runner import run_command
from secripts.safety import Risk, SecError, authorize
from secripts.recovery.backend import TWRP
from secripts.recovery.inspection import audit_tree, artifact_hash

CONFIG = "workspace.json"


def exclusive_workspace(function):
    """Refuse concurrent source mutations, including invocations from another state directory."""

    @wraps(function)
    def locked(*args, **kwargs):
        if kwargs.get("dry_run", args[0] if args else False):
            return function(*args, **kwargs)
        root = Path(load_workspace()["root"])
        with (root / ".secripts-workspace.lock").open("a") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise SecError("Workspace busy; another sync/build holds the lock", 4) from exc
            try:
                return function(*args, **kwargs)
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    return locked


def config_path() -> Path:
    return data_dir() / "recovery" / CONFIG


def load_workspace() -> dict:
    try:
        value = json.loads(config_path().read_text())
        validate_workspace(value)
        if not Path(value["root"]).is_dir():
            raise SecError("Configured workspace root no longer exists", 3)
        return value
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise SecError(
            "Recovery workspace missing or malformed. Use sec recovery init --help.", 3
        ) from exc


def validate_workspace(value: dict) -> None:
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise SecError("Malformed workspace schema", 2)
    if value.get("backend") != "twrp":
        raise SecError("Unsupported recovery backend", 5)
    for key in ("device", "lunch", "revision"):
        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", value.get(key, ""))
            or ".." in value[key]
        ):
            raise SecError(f"Invalid workspace {key}", 2)
    if "/" in value["device"] or value.get("target") not in TWRP.targets:
        raise SecError("Explicit device name and supported build target required", 2)
    if not re.fullmatch(r"https://[A-Za-z0-9.-]+/[A-Za-z0-9_./-]+", value.get("manifest", "")):
        raise SecError("Manifest must be an explicit HTTPS URL without credentials", 2)
    for key in ("root", "tree"):
        if not Path(value[key]).is_absolute():
            raise SecError("Workspace and tree paths must be absolute", 2)
    root = Path(value["root"]).resolve()
    tree = Path(value["tree"]).resolve()
    if root == Path("/") or not tree.is_relative_to(root / "device"):
        raise SecError("Device tree must be inside workspace/device; root cannot be /", 4)


def initialize(
    root: Path, device: str, tree: Path, manifest: str, revision: str, lunch: str, target: str
) -> dict:
    value = {
        "schema": 1,
        "backend": "twrp",
        "root": str(root.resolve()),
        "device": device,
        "tree": str(tree.resolve()),
        "manifest": manifest,
        "revision": revision,
        "lunch": lunch,
        "target": target,
        "common_trees": "UNRESOLVED",
        "kernel": "UNRESOLVED",
    }
    validate_workspace(value)
    if config_path().exists():
        raise SecError(
            "Workspace already configured; inspect workspace.json before replacing it.", 4
        )
    root.mkdir(parents=True, exist_ok=True)
    write_json(config_path(), value)
    save(
        "recovery.init",
        Risk.MUTATING,
        [],
        result="PASS",
        configuration=value,
        effect="Created local workspace configuration; no sources downloaded",
    )
    return value


def recovery_doctor() -> dict:
    general = doctor()
    checks = [
        c
        for c in general["checks"]
        if c["name"] in ("git", "java", "python3", "repo", "adb", "fastboot")
    ]
    for tool in ("bash", "make", "ninja", "clang", "gcc", "bison", "flex", "zip", "unzip"):
        checks.append(
            {
                "name": tool,
                "status": "PASS" if shutil.which(tool) else "WARN",
                "evidence": shutil.which(tool),
            }
        )
    checks += [
        {
            "name": "architecture",
            "status": "PASS" if host()["architecture"] == "x86_64" else "WARN",
            "evidence": host()["architecture"],
            "note": "Upstream Android build hosts generally require x86_64 Linux",
        },
        {
            "name": "disk",
            "status": "PASS" if general["disk_free_bytes"] >= 40 * 1024**3 else "WARN",
            "evidence": general["disk_free_bytes"],
            "note": "40 GiB floor only; actual source/build needs vary",
        },
        {
            "name": "filesystem suitability",
            "status": "UNKNOWN",
            "evidence": "Case sensitivity and executable permissions not qualified",
        },
        {"name": "hardware", "status": "UNKNOWN", "evidence": "Not probed"},
    ]
    try:
        value = load_workspace()
        for name, path in (
            ("source", Path(value["root"]) / "build/envsetup.sh"),
            ("tree", Path(value["tree"])),
        ):
            checks.append(
                {"name": name, "status": "PASS" if path.exists() else "FAIL", "evidence": str(path)}
            )
        checks.append(
            {
                "name": "kernel/common dependencies",
                "status": "UNKNOWN",
                "evidence": "Review tree audit in complete source checkout",
            }
        )
    except SecError as exc:
        value = None
        checks.append({"name": "workspace", "status": "WARN", "evidence": str(exc)})
    return {
        "backend": "twrp",
        "checks": checks,
        "workspace": value,
        "device_qualification": "UNTESTED",
    }


def disk_check(root: Path) -> None:
    if shutil.disk_usage(root).free < 40 * 1024**3:
        raise SecError(
            "Insufficient disk space: source/build requires at least 40 GiB free (may need more).",
            3,
        )


@exclusive_workspace
def sync(dry_run=False) -> dict:
    value = load_workspace()
    root = Path(value["root"])
    plan = [
        ["repo", "init", "-u", value["manifest"], "-b", value["revision"]],
        ["repo", "sync", "-j2", "--fail-fast"],
        ["repo", "manifest", "-r"],
    ]
    if not dry_run:
        disk_check(root)
        if not shutil.which("repo"):
            raise SecError("Missing prerequisite: repo", 3)
    commands = []
    for argv in plan:
        command = run_command(argv, cwd=root, dry_run=dry_run, timeout=7200)
        commands.append(command)
        if command["result"] not in ("PASS", "DRY_RUN"):
            break
    ok = all(c["result"] == "PASS" for c in commands)
    # The runner caps stdout. Never mislabel truncated manifests as reproducibility locks.
    if ok and "[TRUNCATED]" not in commands[-1]["stdout"]:
        (root / "sources.lock.xml").write_text(commands[-1]["stdout"])
    receipt = save(
        "recovery.sync",
        Risk.MUTATING,
        commands,
        result="DRY_RUN" if dry_run else "PASS" if ok else "FAIL",
        configuration=value,
        warnings=["Source branch may move; review sources.lock.xml before builds."],
    )
    return {"receipt": receipt, "exit_code": 0 if dry_run or ok else 1}


@exclusive_workspace
def build(dry_run=False) -> dict:
    value = load_workspace()
    root, tree = Path(value["root"]), Path(value["tree"])
    argv = TWRP().build_command(value["lunch"], value["target"])
    if dry_run:
        return {
            "result": "DRY_RUN",
            "configuration": value,
            "command": argv,
            "warning": "Executes trusted source checkout; compilation does not qualify hardware",
        }
    if host()["architecture"] != "x86_64":
        raise SecError(
            "TWRP build host architecture not qualified; x86_64 required by this backend", 5
        )
    disk_check(root)
    if not (root / "build/envsetup.sh").is_file():
        raise SecError("Source checkout missing build/envsetup.sh", 3)
    audit = audit_tree(tree)
    if audit["result"] == "FAIL":
        raise SecError("Device tree audit failed", 3)
    # Avoid stale artifact collection: record existing hashes and require a changed artifact.
    expected = root / "out/target/product" / value["device"] / TWRP.targets[value["target"]]
    if not expected.resolve().is_relative_to(root.resolve()):
        raise SecError("Artifact output escapes workspace through a symlink", 4)
    old = (expected.stat().st_mtime_ns, artifact_hash(expected)) if expected.is_file() else None
    authorize(Risk.MUTATING, "Execute trusted source makefiles and write build output")
    commands = []
    for args in (["repo", "manifest", "-r"], ["git", "-C", str(tree), "rev-parse", "HEAD"]):
        commands.append(run_command(args, cwd=root))
    if any(c["result"] != "PASS" or "[TRUNCATED]" in c["stdout"] for c in commands):
        raise SecError("Cannot capture source/tree revisions; build refused", 3)
    command = run_command(argv, cwd=root, timeout=14400)
    commands.append(command)
    build_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = data_dir() / "builds" / value["device"] / build_id
    output.mkdir(parents=True)
    (output / "build.log").write_text(command["stdout"] + "\n" + command["stderr"])
    (output / "sources.lock.xml").write_text(commands[0]["stdout"])
    write_json(output / "tree-audit.json", audit)
    artifacts = []
    changed = expected.is_file() and (expected.stat().st_mtime_ns, artifact_hash(expected)) != old
    if command["result"] == "PASS" and changed and not expected.is_symlink():
        dest = output / expected.name
        shutil.copyfile(expected, dest)
        artifacts.append(
            {"path": str(dest), "sha256": artifact_hash(dest), "bytes": dest.stat().st_size}
        )
        (output / "sha256sums.txt").write_text(f"{artifacts[0]['sha256']}  {dest.name}\n")
    success = command["result"] == "PASS" and bool(artifacts)
    receipt = save(
        "recovery.build",
        Risk.MUTATING,
        commands,
        configuration=value,
        result="BUILD_SUCCESS" if success else "FAIL",
        artifacts=artifacts,
        tree_revision=commands[1]["stdout"].strip(),
        device_qualification="UNTESTED",
        warnings=["Log is bounded to 128 KiB per output stream; hardware untested."],
    )
    write_json(output / "build.json", receipt)
    write_json(data_dir() / "recovery/latest-build.json", receipt)
    return {"build": receipt, "output": str(output), "exit_code": 0 if success else 1}
