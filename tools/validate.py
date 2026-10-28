"""Reproducible safe installed-CLI smoke checks; full captures stay in local runtime state."""

from pathlib import Path
from secripts.runner import run_command
from secripts.receipts import write_json
from secripts.context import data_dir

commands = [
    ["sec", "--help"],
    ["sec", "--version"],
    ["sec", "list", "--json"],
    ["sec", "find", "android"],
    ["sec", "doctor", "--json"],
    ["sec", "1337"],
    ["sec", "recovery", "doctor", "--json"],
    ["sec", "run", "git.status", "--json"],
    ["sec", "run", "environment.path", "--json"],
    ["sec", "run", "android.sdk.validate", "--json"],
    ["sec", "run", "adb.version", "--json"],
    ["sec", "run", "fastboot.version", "--json"],
    ["sec", "run", "adb.devices", "--json"],
    ["sec", "run", "fastboot.devices", "--json"],
]
results = []
for argv in commands:
    result = run_command(argv, cwd=Path.cwd(), timeout=30)
    results.append(result)
    print(" ".join(argv), result["result"], result["exit_code"])
write_json(data_dir() / "validation/smoke.json", results)
raise SystemExit(0 if all(r["result"] == "PASS" for r in results[:7]) else 1)
