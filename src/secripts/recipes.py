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


def get(name: str) -> dict:
    if name not in RECIPES:
        raise SecError("Unknown recipe", 2)
    return RECIPES[name]


def run(name: str, dry_run: bool = False) -> dict:
    results = []
    for op in get(name)["operations"]:
        result = execute(op, dry_run)
        results.append(result)
        if result["exit_code"]:
            break
    return {
        "recipe": name,
        "steps": results,
        "exit_code": next((r["exit_code"] for r in results if r["exit_code"]), 0),
    }
