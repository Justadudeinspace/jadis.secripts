"""Diagnostic evidence, not installation or hardware qualification."""

import os
from pathlib import Path
import shutil
from secripts.context import host

TOOLS = {
    "git": "Install Git using your distribution package manager.",
    "ssh": "Install the OpenSSH client.",
    "java": "Install the JDK required by your source branch.",
    "python3": "Install Python 3.11 or newer.",
    "pip": "Use pipx or a Python virtual environment.",
    "pipx": "Optional: install pipx for isolated CLI installation.",
    "node": "Install Node only if your workflow needs it.",
    "npm": "Install npm only if your workflow needs it.",
    "docker": "Optional: install Docker; binary presence does not verify daemon access.",
    "adb": "Install Android platform-tools.",
    "fastboot": "Install Android platform-tools.",
    "repo": "Install Google's repo launcher for Android source workflows.",
}


def sdk() -> dict:
    roots = {k: os.environ.get(k) for k in ("ANDROID_HOME", "ANDROID_SDK_ROOT")}
    root = roots["ANDROID_HOME"] or roots["ANDROID_SDK_ROOT"]
    components = {}
    if root:
        for name in ("platform-tools", "platforms", "build-tools", "cmdline-tools", "licenses"):
            p = Path(root) / name
            components[name] = "PRESENT" if p.is_dir() else "MISSING"
    return {
        "status": "PASS" if root and Path(root).is_dir() else "WARN",
        "roots": roots,
        "components": components,
        "warning": "License directory presence does not prove license acceptance.",
        "conflict": bool(
            all(roots.values()) and roots["ANDROID_HOME"] != roots["ANDROID_SDK_ROOT"]
        ),
    }


def path_analysis() -> list:
    seen, result = set(), []
    for part in os.environ.get("PATH", "").split(os.pathsep):
        path = Path(part or ".")
        result.append(
            {
                "path": part,
                "exists": path.is_dir(),
                "duplicate": part in seen,
                "current_directory": part in ("", "."),
                "world_writable": bool(path.stat().st_mode & 0o002) if path.exists() else None,
            }
        )
        seen.add(part)
    return result


def doctor() -> dict:
    checks = [
        {
            "name": name,
            "status": "PASS" if shutil.which(name) else "WARN",
            "evidence": shutil.which(name),
            "remediation": advice,
        }
        for name, advice in TOOLS.items()
    ]
    checks += [
        {"name": "adb device", "status": "UNTESTED", "evidence": "Not probed"},
        {"name": "fastboot device", "status": "UNTESTED", "evidence": "Not probed"},
    ]
    disk = shutil.disk_usage(Path.cwd())
    return {
        "host": host(),
        "shell": os.environ.get("SHELL", "UNKNOWN"),
        "checks": checks,
        "sdk": sdk(),
        "disk_free_bytes": disk.free,
        "path": path_analysis(),
        "hardware_qualification": "UNTESTED",
    }
