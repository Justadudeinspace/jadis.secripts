"""Exercise installed js against explicitly synthetic evidence in isolated runtime state."""

import json
import os
from pathlib import Path
import struct
import tempfile
from secripts import __version__
from secripts.context import data_dir
from secripts.receipts import write_json
from secripts.runner import run_command

output = data_dir() / "validation/phase3-images.json"
previous = os.environ.get("SECRIPTS_DATA_HOME")
checks = []
try:
    with tempfile.TemporaryDirectory(prefix="secripts-image-smoke-") as directory:
        root = Path(directory)
        os.environ["SECRIPTS_DATA_HOME"] = str(root / "state")
        image = root / "boot.img"
        header = bytearray(4096)
        header[:8] = b"ANDROID!"
        struct.pack_into("<I", header, 40, 4)
        struct.pack_into("<I", header, 20, 1584)
        image.write_bytes(header)
        tree = root / "tree"
        tree.mkdir()
        (tree / "BoardConfig.mk").write_text(
            "TARGET_ARCH := arm64\nPRODUCT_DEVICE := fixture\nPRODUCT_NAME := twrp_fixture\n"
            "BOARD_USES_RECOVERY_AS_BOOT := true\n"
        )
        commands = [
            ["inspect", str(image), "--json"],
            ["inspect", str(image), "--providers", "--json"],
            ["find", "image", "--json"],
            ["find", "recovery", "--json"],
            ["run", "image.providers", "--json"],
            ["recovery", "device", "create", "fixture", "--json"],
            ["recovery", "device", "add-image", "fixture", "boot", str(image), "--json"],
            ["recovery", "device", "add-tree", "fixture", str(tree), "--json"],
            ["recovery", "device", "report", "fixture", "--json"],
            ["recovery", "tree", "diagnose", str(tree), "--json"],
            [
                "recovery",
                "tree",
                "derive",
                "--device",
                "fixture",
                "--output",
                str(root / "candidate"),
                "--json",
            ],
            ["recovery", "plan", "fixture", "--json"],
            ["recipe", "run", "image-analysis", "--artifact", str(image), "--json"],
            ["recovery", "report", str(image), "--tree", str(tree), "--json"],
            ["1337", "--json"],
        ]
        for args in commands:
            result = run_command(["js", *args], timeout=30)
            result["evidence_kind"] = "SYNTHETIC_FIXTURE"
            try:
                json.loads(result["stdout"])
                result["json"] = "PASS"
            except ValueError:
                result["json"] = "FAIL"
            checks.append(result)
            print(" ".join(args[:3]), result["result"], result["json"], flush=True)
finally:
    if previous is None:
        os.environ.pop("SECRIPTS_DATA_HOME", None)
    else:
        os.environ["SECRIPTS_DATA_HOME"] = previous
passed = all(c["result"] == "PASS" and c["json"] == "PASS" for c in checks)
write_json(
    output, {"release": __version__, "result": "PASS" if passed else "FAIL", "checks": checks}
)
raise SystemExit(0 if passed else 1)
