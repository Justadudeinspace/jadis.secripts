"""Run the real local validation gate and retain sanitized evidence outside Git."""

import re
import sys
from secripts import __version__
from secripts.context import data_dir
from secripts.runner import run_command
from secripts.receipts import write_json

commands = [
    [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
    [sys.executable, "-m", "ruff", "check", "."],
    [sys.executable, "-m", "ruff", "format", "--check", "."],
    [sys.executable, "-m", "pytest", "-q"],
    [sys.executable, "tools/secret_scan.py"],
    [sys.executable, "tools/audit_docs.py"],
    [sys.executable, "-m", "build"],
]
checks = []
for argv in commands:
    result = run_command(argv, timeout=240)
    checks.append(result)
    print(" ".join(argv[1:]), result["result"], flush=True)
    if result["result"] != "PASS":
        print(result["stdout"] + result["stderr"])
        break
passed = len(checks) == len(commands) and all(c["result"] == "PASS" for c in checks)
tests = next((c for c in checks if "pytest" in c["arguments"]), {})
match = re.search(r"(\d+) passed", tests.get("stdout", ""))
write_json(
    data_dir() / "validation/phase2-quality.json",
    {
        "release": __version__,
        "result": "PASS" if passed else "FAIL",
        "tests_passed": int(match.group(1)) if match else None,
        "checks": checks,
    },
)
raise SystemExit(0 if passed else 1)
