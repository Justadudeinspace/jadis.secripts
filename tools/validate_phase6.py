"""Installed CLI smoke using synthetic project evidence, never a claimed compilation."""

import json
import os
from pathlib import Path
import tempfile
from secripts.context import data_dir
from secripts.receipts import write_json
from secripts.runner import run_command
from secripts import __version__

output = data_dir() / "validation/phase6-installed.json"
checks = []
prior = os.environ.get("SECRIPTS_DATA_HOME")
with tempfile.TemporaryDirectory(prefix="js-phase6-") as directory:
    root = Path(directory)
    os.environ["SECRIPTS_DATA_HOME"] = str(root / "state")
    tree = root / "tree"
    tree.mkdir()
    (tree / "BoardConfig.mk").write_text(
        "TARGET_ARCH := arm64\nBOARD_RECOVERYIMAGE_PARTITION_SIZE := 67108864\nBOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true\nBOARD_USES_GENERIC_KERNEL_IMAGE := true\n"
    )
    (tree / "twrp_sample.mk").write_text("PRODUCT_NAME := twrp_sample\n")
    commands = [
        ["--version"],
        ["--help"],
        [],
        ["guide"],
        ["doc", "--json"],
        ["dos", "--json"],
        ["1337"],
        ["ry"],
        ["ry", "acquire", "--json"],
        ["ry", "status", "--help"],
        ["ry", "flags", "--help"],
        ["ry", "plan", "--help"],
        ["ry", "build", "--help"],
        ["img", "--help"],
        ["avb", "--help"],
        ["ai", "--help"],
        ["ry", "dce", "create", "sample", "--json"],
        ["ry", "dce", "add-tree", "sample", str(tree), "--json"],
        ["ry", "graph", "sample", "--json"],
        ["recovery", "graph", "sample", "--json"],
        ["ry", "flags", "sample", "--json"],
        ["ry", "flags", "set", "sample", "BOARD_KERNEL_PAGESIZE", "4096", "--json"],
        ["ry", "flags", "sh", "sample", "BOARD_KERNEL_PAGESIZE", "--json"],
        ["recovery", "flags", "show", "sample", "BOARD_KERNEL_PAGESIZE", "--json"],
        ["ry", "flags", "diff", "sample", "--json"],
        ["ry", "flags", "validate", "sample", "--json"],
        ["ry", "flags", "profile", "save", "sample", "reviewed", "--json"],
        ["ry", "flags", "profile", "ls", "--json"],
        ["ry", "flags", "profile", "apply", "sample", "reviewed", "--json"],
        ["ry", "deps", "validate", "sample", "--json"],
        ["ry", "source", "sample", "--json"],
        ["ry", "fstab", "sample", "--json"],
        ["ry", "status", "sample", "--json"],
        ["ry", "plan", "sample", "--json"],
        ["rcp", "run", "recovery-configuration-review", "--model", "sample", "--json"],
        ["run", "recovery.architecture", "--model", "sample", "--json"],
        ["run", "recovery.flags.validate", "--model", "sample", "--json"],
        ["comp", "candidates", "--", "ry", "flags"],
    ]
    values = []
    try:
        for args in commands:
            result = run_command(["js", *args], cwd=root, timeout=45)
            checks.append(result)
            if result["exit_code"]:
                raise ValueError(result["stdout"] + result["stderr"])
            values.append(json.loads(result["stdout"]) if "--json" in args else None)
            print("js " + " ".join(args[:3]), "PASS", flush=True)
        assert values[18]["targets"] == ["recoveryimage", "vendorbootimage"]
        assert values[18] == values[19]
        assert values[22] == values[23]
        assert values[32]["areas"]["HARDWARE"] == "UNTESTED"
        bash = run_command(["js", "comp", "bash"], cwd=root)
        script = root / "js.bash"
        script.write_text(bash["stdout"])
        syntax = run_command(["bash", "-n", str(script)])
        assert syntax["exit_code"] == 0
        checks.append(syntax)
    finally:
        if prior is None:
            os.environ.pop("SECRIPTS_DATA_HOME", None)
        else:
            os.environ["SECRIPTS_DATA_HOME"] = prior
write_json(
    output,
    {
        "schema": 1,
        "version": __version__,
        "result": "PASS",
        "checks": checks,
        "evidence_class": "INSTALLED_WHEEL_SYNTHETIC_PROJECT_AND_REAL_HOST",
        "live_compilation": "NOT_RUN",
        "hardware_qualification": "UNTESTED",
    },
)
