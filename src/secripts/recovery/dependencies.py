"""Reviewed pinned dependencies; no implicit repository guessing or recursive source sync."""

import json
from pathlib import Path
import re
import shutil
from secripts.images.artifacts import read
from secripts.recovery import projects
from secripts.runner import run_command
from secripts.safety import SecError
from secripts.receipts import save


def validate_lock(lock):
    if (
        not isinstance(lock, dict)
        or lock.get("schema") != 1
        or not isinstance(lock.get("dependencies"), list)
        or len(lock["dependencies"]) > 64
    ):
        raise SecError("Invalid reviewed dependency lock", 2)
    seen = set()
    for row in lock["dependencies"]:
        if (
            not isinstance(row, dict)
            or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", row.get("id", ""))
            or row["id"] in seen
        ):
            raise SecError("Duplicate/unsafe dependency identity", 2)
        seen.add(row["id"])
        if not re.fullmatch(
            r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?",
            row.get("repository", ""),
        ):
            raise SecError("Dependency requires reviewed credential-free GitHub HTTPS URL", 4)
        if not re.fullmatch(r"[a-f0-9]{40}", row.get("revision", "")):
            raise SecError("Every dependency requires a full pinned commit", 3)
        path = Path(row.get("path", ""))
        if (
            not re.fullmatch(r"[A-Za-z0-9_/-]+", row.get("path", ""))
            or path.is_absolute()
            or ".." in path.parts
            or any(p.startswith(".") for p in path.parts)
        ):
            raise SecError("Unsafe dependency destination", 4)
        if row.get("role") not in {
            "device",
            "common",
            "kernel",
            "vendor",
            "manifest",
            "source-component",
        }:
            raise SecError("Unknown dependency role", 2)
    paths = [Path(r["path"]) for r in lock["dependencies"]]
    if any(
        a == b or a.is_relative_to(b) or b.is_relative_to(a)
        for i, a in enumerate(paths)
        for b in paths[:i]
    ):
        raise SecError("Overlapping dependency destinations", 4)
    source = lock.get("source", {})
    if source:
        if source.get("generation") not in {"twrp-12.1", "aosp-main", "aosp-13+"}:
            raise SecError("Source generation support is not established", 3)
        if not re.fullmatch(
            r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?",
            source.get("manifest", ""),
        ) or not re.fullmatch(r"[a-f0-9]{40}", source.get("revision", "")):
            raise SecError("Source manifest requires reviewed URL and full commit", 4)
        if not re.fullmatch(r"[A-Za-z0-9_]+-(?:eng|userdebug)", source.get("lunch", "")):
            raise SecError("Unsafe source lunch target", 4)
    return lock


def select(name, path, dry_run=False):
    from secripts.recovery import model

    model.load(name)
    lock = validate_lock(json.loads(read(Path(path), 256 * 1024)))
    result = {
        "schema": 1,
        "model": name,
        "lock": lock,
        "lock_sha256": projects.digest(lock),
        "updated": projects.now(),
        "acquired_root": None,
    }
    if dry_run:
        return {**result, "result": "DRY_RUN"}
    with projects.locked(name):
        projects.store(name, "dependencies", result)
    save(
        "recovery.dependencies.select",
        "MUTATING",
        [],
        result="PASS",
        model=name,
        lock_sha256=result["lock_sha256"],
    )
    return result


def outside_git(path):
    path = Path(path).absolute()
    if path.resolve() != path:
        raise SecError("Symlink/ambiguous acquisition root refused", 4)
    if any((p / ".git").exists() for p in (path, *path.parents)):
        raise SecError("Dependency acquisition must be outside any project Git worktree", 4)
    return path


def graph(name):
    from secripts.recovery import model

    device = model.report(name)
    state = projects.load(name, "dependencies", {}) or {}
    lock = state.get("lock", {"schema": 1, "dependencies": []})
    nodes = [{"id": r["id"], **r} for r in lock["dependencies"]]
    edges = []
    for row in device.get("evidence", []):
        if row["field"] == "dependencies" and isinstance(row["value"], list):
            for edge in row["value"]:
                edges.append(
                    {
                        **edge,
                        "provenance": {"source": row["source"], "location": row["location"]},
                        "resolved_by": [
                            r["id"]
                            for r in lock["dependencies"]
                            if r["path"] == edge.get("reference")
                        ],
                    }
                )
    return {
        "schema": 1,
        "nodes": nodes,
        "edges": edges,
        "complete": False,
        "note": "Literal/source-declared dependencies; dynamic Make expansion and transitive source projects remain separate",
    }


def validate(name):
    state = projects.load(name, "dependencies", {}) or {}
    if not state:
        return {
            "schema": 1,
            "status": "BLOCKED",
            "checks": [],
            "blockers": ["No reviewed pinned dependency/source lock selected"],
        }
    lock = validate_lock(state["lock"])
    root = Path(state["acquired_root"]) if state.get("acquired_root") else None
    checks = []
    for row in lock["dependencies"]:
        path = root / row["path"] if root else None
        status = "MISSING"
        actual = None
        if path and path.is_dir() and not path.is_symlink():
            r = run_command(["git", "-C", str(path), "rev-parse", "HEAD"], timeout=10)
            actual = r["stdout"].strip()
            status = "PASS" if r["result"] == "PASS" and actual == row["revision"] else "FAIL"
            clean = run_command(
                ["git", "-C", str(path), "status", "--porcelain", "--untracked-files=all"],
                timeout=10,
            )
            if clean["result"] != "PASS" or clean["stdout"].strip():
                status = "FAIL"
        checks.append(
            {
                "id": row["id"],
                "path": str(path) if path else None,
                "status": status,
                "expected": row["revision"],
                "actual": actual,
            }
        )
    edges = graph(name)["edges"]
    unresolved = [
        e for e in edges if e.get("state") != "STATICALLY_RESOLVED" and not e["resolved_by"]
    ]
    blockers = [r["id"] + " not pinned/clean/present" for r in checks if r["status"] != "PASS"]
    if unresolved:
        blockers.append(
            f"{len(unresolved)} external/static references require review (source-base files may resolve after full sync)"
        )
    return {
        "schema": 1,
        "status": "PASS" if checks and not blockers else "BLOCKED",
        "checks": checks,
        "blockers": blockers,
        "unresolved": unresolved,
        "source_lock_scope": "Reviewed selected repositories, not a resolved complete repo manifest",
    }


def resolve(name, *, root=None, fetch=False, dry_run=False):
    state = projects.load(name, "dependencies", {}) or {}
    if not state:
        raise SecError("Select a reviewed lock first with deps resolve --lock FILE", 3)
    lock = validate_lock(state["lock"])
    destination = outside_git(root or projects.directory(name) / "checkout")
    commands = []
    for row in lock["dependencies"]:
        target = destination / row["path"]
        commands += [
            ["git", "-c", "init.templateDir=", "init", str(target)],
            ["git", "-C", str(target), "remote", "add", "origin", row["repository"]],
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "protocol.file.allow=never",
                "-C",
                str(target),
                "fetch",
                "--depth=1",
                "--no-tags",
                "origin",
                row["revision"],
            ],
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-C",
                str(target),
                "checkout",
                "--detach",
                row["revision"],
            ],
        ]
    if not fetch or dry_run:
        return {
            "schema": 1,
            "result": "DRY_RUN",
            "root": str(destination),
            "commands": commands,
            "network": "NOT_USED",
            "note": "Use --fetch only after reviewing URL/commit/path; no recursive submodules, hooks or source scripts execute",
        }
    if not shutil.which("git"):
        raise SecError("Git missing", 3)
    ancestor = destination
    while not ancestor.exists():
        ancestor = ancestor.parent
    if shutil.disk_usage(ancestor).free < 2 * 1024**3:
        raise SecError("Below 2 GiB acquisition safety floor; no download started", 3)
    for row in lock["dependencies"]:
        target = destination / row["path"]
        if target.resolve() != target.absolute():
            raise SecError("Symlink in dependency destination refused", 4)
    with projects.locked(name):
        # Never overwrite an existing checkout; failed attempts remain available for inspection.
        if any((destination / r["path"]).exists() for r in lock["dependencies"]):
            raise SecError(
                "Dependency destination already exists; validate/review instead of overwriting", 4
            )
        destination.mkdir(parents=True, exist_ok=True, mode=0o700)
        results = []
        for argv in commands:
            argv = [
                "env",
                "GIT_CONFIG_GLOBAL=/dev/null",
                "GIT_CONFIG_NOSYSTEM=1",
                "GIT_LFS_SKIP_SMUDGE=1",
                *argv,
            ]
            r = run_command(argv, timeout=600)
            results.append(r)
            if r["result"] != "PASS":
                receipt = save(
                    "recovery.dependencies.resolve", "MUTATING", results, result="FAIL", model=name
                )
                return {
                    "result": "FAIL",
                    "exit_code": 1,
                    "receipt_id": receipt["receipt_id"],
                    "failed_command": r,
                    "root": str(destination),
                }
        state["acquired_root"] = str(destination)
        state["updated"] = projects.now()
        projects.store(name, "dependencies", state)
    receipt = save(
        "recovery.dependencies.resolve",
        "MUTATING",
        results,
        result="PASS",
        model=name,
        lock_sha256=state["lock_sha256"],
    )
    return {
        "result": "PASS",
        "receipt_id": receipt["receipt_id"],
        "root": str(destination),
        "validation": validate(name),
    }


def source(name, action="inspect", path=None):
    if action == "resolve":
        if path is None:
            raise SecError("Source resolution requires reviewed --lock FILE", 2)
        select(name, path)
    state = projects.load(name, "dependencies", {}) or {}
    selected = state.get("lock", {}).get("source")
    return {
        "schema": 1,
        "model": name,
        "status": "PARTIAL" if selected else "BLOCKED",
        "selection": selected,
        "dependency_validation": validate(name),
        "resolved_repo_manifest": "UNACQUIRED: requires qualified-host source sync and repo manifest -r",
        "compatibility": "REVIEW_REQUIRED",
        "hardware_qualification": "UNTESTED",
    }
