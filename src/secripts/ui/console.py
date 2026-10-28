"""1337 mode derives operation context directly from the registry."""

import sys
import os
import shlex
from secripts.registry import registry
from secripts.doctor import doctor
from secripts.operations import execute
from secripts.provenance import packaged
from secripts.recipes import RECIPES, run

CATEGORIES = [
    ("1", "Android", "android", "Inspect SDK configuration and installed Android components."),
    ("2", "ADB / Fastboot", "transports", "Inspect Android debug and bootloader transports."),
    (
        "3",
        "Recovery Lab",
        "recovery",
        "Audit trees, inspect images and orchestrate explicit TWRP workspaces.",
    ),
    ("4", "Git / GitHub", "vcs", "Review repository state, history, remotes and authentication."),
    ("5", "Linux / Debian", "debian", "Inspect development packages before changing the system."),
    ("6", "Termux", "termux", "Inspect Android, Termux and PRoot environment boundaries."),
    ("7", "Environment", "environment", "Analyze PATH and installed developer runtimes."),
    ("8", "Models / AI", "models", "Inspect local model tooling without provider credentials."),
    ("9", "Diagnostics", "diagnostics", "Inspect host context, disk, SSH and network interfaces."),
]


def recovery_console():
    from secripts.cli import main

    print(
        "\nRECOVERY LAB // TWRP\n"
        "doctor                   Inspect prerequisites and workspace evidence.\n"
        "inspect IMAGE / --device Inspect headers or one authorized ADB device.\n"
        "tree audit PATH          Parse declarations without executing makefiles.\n"
        "configure                Show explicit source and target configuration.\n"
        "init --help              Configure an isolated workspace without downloading.\n"
        "sync --dry-run           Preview explicit source acquisition.\n"
        "build --dry-run          Preview compilation; no hardware qualification.\n"
        "test --help              Record manual observations against an artifact hash.\n"
        "report --help            Render JSON or Markdown qualification evidence.\n"
        "boot IMAGE               Refuse unresolved temporary-boot support.\n"
        "B                        Return to the master console."
    )
    while True:
        command = input("recovery > ").strip()
        if command.upper() in ("", "B"):
            return
        try:
            main(["recovery", *shlex.split(command)])
        except (SystemExit, ValueError) as exc:
            if isinstance(exc, ValueError):
                print("Invalid quoting; enter a recovery subcommand or B.")


def console(emit) -> int:
    banner = "J A D I S // S E C R I P T S\n1337 MODE // OPERATOR CONSOLE"
    if (
        sys.stdout.isatty()
        and os.environ.get("TERM", "dumb") != "dumb"
        and "NO_COLOR" not in os.environ
    ):
        banner = "\033[1;36m" + banner + "\033[0m"
    print(banner + "\n")
    for key, title, _, description in CATEGORIES:
        print(f"[{key}] {title}\n    {description}")
    for key, title, desc in [
        ("R", "Recipes", "Guided workflows with normal operation safety."),
        ("A", "Archaeology", "Sanitized lineage, classifications and modern replacements."),
        ("S", "Search Everything", "Search operation metadata and recipes."),
        ("D", "Doctor", "Inspect host tools; device functionality remains untested."),
        ("H", "Help", "Explain commands and risk labels."),
        ("Q", "Exit", "Leave the console."),
    ]:
        print(f"[{key}] {title}\n    {desc}")
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("\nNoninteractive preview. Use sec list, sec doctor or sec recovery --help.")
        return 0
    print("\nHOST STATUS (binary presence only)")
    value = doctor()
    emit(value["host"])
    for check in value["checks"]:
        print(f"{check['name']:18} {check['status']}")
    reg = registry()
    while True:
        try:
            choice = input("\n1337 > ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if choice in ("Q", "QUIT"):
            return 0
        if choice == "D":
            emit(doctor())
        elif choice == "A":
            value = packaged()
            emit({"counts": value["counts"], "duplicates": value["duplicates"]})
            query = input("Lineage category/name filter (blank for all): ").strip().lower()
            for row in value["artifacts"]:
                if query in str((row["source"], row["category"], row["classification"])).lower():
                    emit(
                        {
                            key: row[key]
                            for key in (
                                "id",
                                "source",
                                "category",
                                "classification",
                                "contained_secrets",
                                "modern_replacement",
                                "reason",
                            )
                        }
                    )
        elif choice == "H":
            print(
                "sec show/explain ID: inspect contract. sec run ID --dry-run: preview.\nREAD_ONLY inspects; MUTATING writes; PRIVILEGED never elevates; DESTRUCTIVE requires identity confirmation."
            )
        elif choice == "R":
            emit(RECIPES)
            name = input("Recipe name (blank to return): ").strip()
            if name in RECIPES:
                emit(run(name, dry_run=input("[P]review or [R]un? ").strip().upper() != "R"))
        elif choice == "3":
            recovery_console()
        else:
            if choice == "S":
                query = input("Search > ")
                ops = reg.search(query)
                emit({k: v for k, v in RECIPES.items() if query.lower() in str(v).lower()})
            else:
                category = next((v for k, _, v, _ in CATEGORIES if k == choice), None)
                if category is None:
                    print("Choose 1-9, R, A, S, D, H or Q. Each category is described above.")
                    continue
                groups = {
                    "transports": {"adb", "fastboot"},
                    "vcs": {"git", "github"},
                    "diagnostics": {"diagnostics", "repo", "network", "ssh"},
                }
                ops = [op for op in reg.search() if op.category in groups.get(category, {category})]
            for op in ops:
                print(f"{op.id}: {op.title}\n    {op.summary}")
            name = input("Operation ID (blank to return): ").strip()
            if name not in reg.operations:
                continue
            op = reg.get(name)
            emit(
                {
                    "operation": op.id,
                    "title": op.title,
                    "summary": op.summary,
                    "risk": op.risk,
                    "requires": op.requires,
                    "output": op.output,
                    "receipt": op.receipt,
                    "device_required": op.device_required,
                    "network": op.network,
                    "effect": op.effect,
                }
            )
            action = (
                input("[ENTER] Run · [E] Explain · [P] Prerequisites · [D] Dry-run · [B] Back > ")
                .strip()
                .upper()
            )
            if action in ("", "D"):
                emit(execute(name, action == "D"))
            elif action == "E":
                emit(op.metadata())
            elif action == "P":
                emit(
                    {
                        "requires": op.requires,
                        "platforms": op.platforms,
                        "device_required": op.device_required,
                    }
                )
