"""Installed product smoke: synthetic contexts, no paid calls or device modifications."""

import json
import os
from pathlib import Path
import tempfile
from secripts import __version__
from secripts.runner import run_command
from secripts.receipts import write_json
from secripts.context import data_dir

output = data_dir() / "validation/phase5-installed.json"
checks = []
with tempfile.TemporaryDirectory(prefix="js-phase5-product-") as directory:
    root = Path(directory)
    # Isolate state and explicitly prohibit accidental paid authentication during smoke.
    prior = os.environ.get("SECRIPTS_DATA_HOME")
    os.environ["SECRIPTS_DATA_HOME"] = str(root / "state")
    path = root / "report.json"
    path.write_text('{"status":"BLOCKED","reason":"SYNTHETIC build fixture"}')
    log = root / "build.log"
    log.write_text("SYNTHETIC: No space left on device\n")
    commands = [
        ["--version"],
        ["--help"],
        [],
        ["guide"],
        ["help", "recovery"],
        ["help", "image"],
        ["help", "device"],
        ["help", "evidence"],
        ["doc", "--json"],
        ["dos", "--json"],
        ["fd", "recovery", "--json"],
        ["rcps", "--json"],
        ["1337"],
        ["1337", "--json"],
        ["img"],
        ["ram"],
        ["avb"],
        ["ry", "--json"],
        ["ry", "acquire", "--json"],
        ["recovery", "acquire", "--have", "images", "--json"],
        ["ry", "source", "--json"],
        ["ry", "failure", str(log), "--json"],
        ["ai", "--help"],
        ["ai", "setup", "--json"],
        ["ai", "providers", "--json"],
        ["ai", "models", "--provider", "openai", "--json"],
        ["ai", "context", "--context", str(path), "--json"],
        ["ai", "ask", "Explain fixture", "--provider", "openai", "--context", str(path), "--json"],
        ["ai", "tools", "registry.search", "recovery", "--json"],
        ["rcp", "sh", "recovery-onramp", "--json"],
        ["rcp", "run", "recovery-onramp", "--dry-run", "--json"],
        ["hist", "--summary", "--limit", "2", "--json"],
        ["rcpt", "latest", "--json"],
        ["comp", "candidates", "ai"],
        ["comp", "bash"],
    ]
    try:
        for args in commands:
            r = run_command(["js", *args], timeout=45)
            checks.append(r)
            print("js " + " ".join(args[:3]), r["exit_code"], flush=True)
            if r["exit_code"] != 0:
                raise ValueError(r["stdout"] + r["stderr"])
            if "--json" in args:
                json.loads(r["stdout"])
            if args == ["--version"]:
                assert r["stdout"].strip() == "js " + __version__
        r = run_command(
            [
                "js",
                "ai",
                "ask",
                "fixture",
                "--provider",
                "openai",
                "--send",
                "--approve",
                "incorrect",
                "--json",
            ]
        )
        assert r["exit_code"] == 4
        checks.append(r)
    finally:
        if prior is None:
            os.environ.pop("SECRIPTS_DATA_HOME", None)
        else:
            os.environ["SECRIPTS_DATA_HOME"] = prior
write_json(
    output,
    {
        "schema": 1,
        "release": __version__,
        "result": "PASS",
        "checks": checks,
        "evidence_kind": "INSTALLED_PRODUCT_SYNTHETIC_AND_REAL_HOST",
        "paid_inference": "NOT_RUN",
        "device_qualification": "UNTESTED",
    },
)
