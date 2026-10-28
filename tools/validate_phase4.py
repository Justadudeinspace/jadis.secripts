"""Installed-launcher Phase 4 smoke/alias evidence outside checkout, in isolated synthetic state."""

import argparse
import json
import os
from pathlib import Path
import struct
import tempfile
from secripts import __version__
from secripts.commands import inventory
from secripts.cli import parser as cli_parser
from secripts.images import cpio, codecs
from secripts.runner import run_command
from secripts.receipts import write_json
from secripts.context import data_dir

arguments = argparse.ArgumentParser()
arguments.add_argument(
    "--aosp-tools", type=Path, help="Optional explicit reviewed AOSP source directory"
)
args = arguments.parse_args()
output = data_dir() / "validation/phase4-installed.json"
prior = os.environ.get("SECRIPTS_DATA_HOME")
checks = []


def check(argv, expected=0):
    result = run_command(["js", *argv], timeout=45)
    result["expected_exit_code"] = expected
    result["evidence_kind"] = "SYNTHETIC_HARNESS_OR_REAL_HOST"
    checks.append(result)
    print("js " + " ".join(argv[:3]), result["exit_code"], flush=True)
    if result["exit_code"] != expected:
        raise ValueError(
            "Unexpected installed command result: " + result["stdout"] + result["stderr"]
        )
    if "--json" in argv:
        return json.loads(result["stdout"])
    return result["stdout"]


try:
    with tempfile.TemporaryDirectory(prefix="js-phase4-wheel-smoke-") as directory:
        root = Path(directory)
        os.environ["SECRIPTS_DATA_HOME"] = str(root / "state")
        assert check(["--version"]).strip() == f"js {__version__}"
        check(["--help"])
        for row in inventory(cli_parser()):
            if row["scope"]:
                continue
            check([row["canonical"], "--help"])
            for alias in row["aliases"]:
                check([alias, "--help"])
        for short, long in [
            ("ls", "list"),
            ("fd", "find"),
            ("doc", "doctor"),
            ("dos", "dossier"),
            ("hist", "history"),
        ]:
            check([short])
            check([long])
        assert check(["ls", "--json"]) == check(["list", "--json"])
        assert check(["fd", "android", "--json"]) == check(["find", "android", "--json"])
        check(["1337"])
        check(["1337", "--json"])
        entry = dict.fromkeys(cpio.FIELDS, 0)
        entry.update(
            path="init",
            type="file",
            format="070701",
            mode=0o100755,
            nlink=1,
            ino=1,
            archive=0,
            payload=b"SYNTHETIC INIT",
        )
        ramdisk = root / "ramdisk.lz4"
        ramdisk.write_bytes(
            codecs.encode(
                cpio.pack({"schema": 1, "model": "ramdisk-cpio", "entries": [entry]}), "lz4"
            )
        )
        kernel = b"SYNTHETIC KERNEL"
        rd = ramdisk.read_bytes()
        header = bytearray(4096)
        header[:8] = b"ANDROID!"
        struct.pack_into("<II", header, 8, len(kernel), len(rd))
        struct.pack_into("<I", header, 20, 1584)
        struct.pack_into("<I", header, 40, 4)
        image = root / "boot.img"
        image.write_bytes(
            header + kernel + bytes((-len(kernel)) % 4096) + rd + bytes((-len(rd)) % 4096)
        )
        versions = []
        for route in (["insp"], ["inspect"], ["img", "insp"], ["image", "inspect"]):
            value = check([*route, str(image), "--json"])
            value.pop("receipt_id")
            versions.append(value)
        assert all(value == versions[0] for value in versions)
        check(["img", "model", str(image), "--json"])
        workspace = root / "workspace"
        check(["img", "upk", str(image), "--output", str(workspace), "--json"])
        check(["image", "workspace", str(workspace), "--json"])
        rebuilt = root / "rebuilt.img"
        check(["img", "rb", str(workspace), "--output", str(rebuilt), "--json"])
        result = check(["img", "cmp", str(image), str(rebuilt), "--json"])
        assert result["data"]["byte_identity"] == "BYTE_IDENTICAL"
        check(["img", "rt", str(image), "--json"])
        check(["image", "roundtrip", str(image), "--json"])
        check(["ram", "insp", str(ramdisk), "--json"])
        ram_root = root / "ramdisk-workspace"
        check(["ramdisk", "extract", str(ramdisk), "--output", str(ram_root), "--json"])
        ram_rebuilt = root / "ramdisk.gz"
        check(
            [
                "ram",
                "pack",
                str(ram_root),
                "--output",
                str(ram_rebuilt),
                "--compression",
                "gzip",
                "--json",
            ]
        )
        compared = check(["ram", "cmp", str(ramdisk), str(ram_rebuilt), "--json"])
        assert compared["data"]["semantic_equivalence"] == "SEMANTICALLY_EQUIVALENT"
        dtb = (
            struct.pack(">10I", 0xD00DFEED, 72, 56, 72, 40, 17, 16, 0, 0, 16)
            + bytes(16)
            + struct.pack(">4I", 1, 0, 2, 9)
        )
        dtbo = root / "dtbo.img"
        dtbo.write_bytes(
            struct.pack(">8I", 0xD7B7AB1E, 136, 32, 32, 1, 32, 2048, 0)
            + struct.pack(">8I", 72, 64, 7, 1, 0, 0, 0, 0)
            + dtb
        )
        dt_root = root / "dtbo-workspace"
        check(["dtbo", "insp", str(dtbo), "--json"])
        check(["dtbo", "ext", str(dtbo), "--output", str(dt_root), "--json"])
        check(["dtbo", "rb", str(dt_root), "--output", str(root / "dtbo-rebuilt.img"), "--json"])
        check(["dtbo", "cmp", str(dtbo), str(root / "dtbo-rebuilt.img"), "--json"])
        vbmeta = root / "vbmeta.img"
        vb = bytearray(256)
        vb[:4] = b"AVB0"
        struct.pack_into(">II", vb, 4, 1, 0)
        vbmeta.write_bytes(vb)
        check(["avb", "insp", str(vbmeta), "--json"])
        check(["prov", "--json"])
        check(["providers", "--json"])
        check(["img", "prov", "--json"])
        check(["rcp", "run", "artifact-roundtrip", "--artifact", str(image), "--dry-run", "--json"])
        check(["ry", "doc", "--json"])
        check(["recovery", "doctor", "--json"])
        assert check(["comp", "candidates", "--", "img"]) == check(
            ["completion", "candidates", "--", "image"]
        )
        check(["hist", "--summary", "--limit", "3", "--json"])
        check(["rcpt", "latest", "--json"])
        check(["receipt", "latest", "--json"])
        malformed = root / "bad.img"
        malformed.write_bytes(b"ANDROID!")
        check(["insp", str(malformed), "--json"], expected=1)
        check(["img", "upk", str(image), "--output", str(workspace), "--json"], expected=4)
        if args.aosp_tools:
            check(["img", "diff", str(image), "--tools", str(args.aosp_tools), "--json"])
        passed = True
except (ValueError, AssertionError) as exc:
    passed = False
    print(str(exc), flush=True)
finally:
    if prior is None:
        os.environ.pop("SECRIPTS_DATA_HOME", None)
    else:
        os.environ["SECRIPTS_DATA_HOME"] = prior
write_json(
    output,
    {
        "release": __version__,
        "result": "PASS" if passed else "FAIL",
        "checks": checks,
        "hardware_qualification": "UNTESTED",
        "corpus_binaries_used": False,
    },
)
raise SystemExit(0 if passed else 1)
