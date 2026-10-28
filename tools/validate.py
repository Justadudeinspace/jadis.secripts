"""Installed-launcher smoke evidence; synthetic images/trees stay temporary and explicitly labeled."""

import argparse
import json
from pathlib import Path
import struct
import tempfile
from secripts import __version__
from secripts.runner import run_command
from secripts.receipts import write_json
from secripts.context import data_dir

parser = argparse.ArgumentParser()
parser.add_argument("--devices", action="store_true", help="Explicit safe transport enumeration")
parser.add_argument(
    "--network", action="store_true", help="Explicit GitHub metadata and workflow queries"
)
args = parser.parse_args()
commands = [
    ["js", "--help"],
    ["js", "--version"],
    ["js", "list", "--json"],
    ["js", "find", "android", "--json"],
    ["js", "show", "android.sdk.validate", "--json"],
    ["js", "explain", "python.environment", "--json"],
    ["js", "doctor", "--json"],
    ["js", "dossier", "--json"],
    ["js", "1337"],
    ["js", "1337", "--json"],
    ["js", "recovery", "doctor", "--json"],
    ["js", "run", "git.status", "--json"],
    ["js", "run", "git.health", "--json"],
    ["js", "run", "python.environment", "--json"],
    ["js", "run", "python.project", "--json"],
    ["js", "run", "java.environment", "--json"],
    ["js", "run", "environment.path", "--json"],
    ["js", "run", "android.sdk.validate", "--json"],
    ["js", "run", "adb.version", "--json"],
    ["js", "run", "fastboot.version", "--json"],
    ["js", "recipe", "run", "git-review", "--dry-run", "--json"],
    ["js", "recipes", "--json"],
    ["js", "history", "--operation", "git.status", "--limit", "2", "--summary", "--json"],
    ["js", "receipt", "latest", "--json"],
    ["js", "receipt", "latest", "--failed", "--json"],
    ["js", "completion", "bash"],
]
if args.devices:
    commands += [["js", "run", name, "--json"] for name in ("adb.devices", "fastboot.devices")]
if args.network:
    commands += [
        ["js", "run", name, "--json"] for name in ("github.repository", "github.workflows")
    ]
results = []
operations = {}
critical_ok = True
with tempfile.TemporaryDirectory(prefix="secripts-validation-") as directory:
    root = Path(directory)
    tree = root / "tree"
    tree.mkdir()
    (tree / "BoardConfig.mk").write_text("TARGET_ARCH := arm64\nBOARD_BOOT_HEADER_VERSION := 4\n")
    (tree / "AndroidProducts.mk").write_text("PRODUCT_MAKEFILES := $(LOCAL_DIR)/twrp_fixture.mk\n")
    (tree / "twrp_fixture.mk").write_text("PRODUCT_NAME := twrp_fixture\n")
    image = root / "fixture.img"
    header = bytearray(4096)
    header[:8] = b"ANDROID!"
    struct.pack_into("<I", header, 40, 4)
    struct.pack_into("<I", header, 20, 1584)
    image.write_bytes(header)
    commands += [
        ["js", "recovery", "tree", "audit", str(tree), "--json"],
        ["js", "recovery", "inspect", str(image), "--json"],
        ["js", "recovery", "report", str(image), "--json"],
        ["js", "recovery", "report", str(image), "--markdown"],
    ]
    failure = ["js", "recovery", "inspect", str(root / "does-not-exist.img"), "--json"]
    insert_at = next(
        i
        for i, command in enumerate(commands)
        if command == ["js", "receipt", "latest", "--failed", "--json"]
    )
    commands.insert(insert_at, failure)
    for index, argv in enumerate(commands):
        result = run_command(argv, cwd=Path.cwd(), timeout=40)
        result["expected_exit_code"] = 3 if argv == failure else 0
        result["evidence_kind"] = (
            "SYNTHETIC_FIXTURE" if directory in " ".join(argv) else "LOCAL_INVOCATION"
        )
        results.append(result)
        print(" ".join(argv), result["result"], result["exit_code"], flush=True)
        if index < 11 and result["result"] != "PASS":
            critical_ok = False
        if argv == ["js", "--version"] and result["stdout"].strip() != f"js {__version__}":
            critical_ok = False
        if argv[1:2] == ["run"]:
            try:
                value = json.loads(result["stdout"])
                operations[argv[2]] = {
                    "invocation": value["result"],
                    "exit_code": value["exit_code"],
                }
            except (ValueError, KeyError):
                critical_ok = False
        if "--json" in argv:
            try:
                json.loads(result["stdout"])
            except ValueError:
                critical_ok = False
write_json(
    data_dir() / "validation/phase2-smoke.json",
    {
        "release": __version__,
        "critical_result": "PASS" if critical_ok else "FAIL",
        "operations": operations,
        "checks": results,
        "hardware_qualification": "UNTESTED",
    },
)
raise SystemExit(0 if critical_ok else 1)
