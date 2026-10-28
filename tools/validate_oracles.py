"""Explicit small upstream AOSP oracle qualification; never uses corpus executables or signing keys."""

import argparse
import json
from pathlib import Path
import struct
import sys
import tempfile
from secripts.images.oracles import PINNED, AOSP_REVISION, aosp
from provider_sources import fetch
from secripts.images.artifacts import read, digest
from secripts.images.workflows import roundtrip
from secripts.images import cpio, codecs
from secripts.runner import run_command
from secripts.context import data_dir
from secripts.receipts import write_json

parser = argparse.ArgumentParser()
parser.add_argument(
    "--tools", type=Path, help="Existing reviewed hash-pinned AOSP source directory"
)
parser.add_argument(
    "--fetch-upstream",
    action="store_true",
    help="Explicitly retrieve three small hash-pinned AOSP source files",
)
args = parser.parse_args()
records = []
with tempfile.TemporaryDirectory(prefix="js-oracle-qualification-") as directory:
    root = Path(directory)
    provider = root / "provider"
    provider.mkdir()
    for name, expected in PINNED.items():
        if args.tools:
            payload = read(args.tools / name, 1024**2)
        elif args.fetch_upstream:
            url = (
                "https://android.googlesource.com/platform/system/tools/mkbootimg/+/"
                + AOSP_REVISION
                + "/"
                + name
            )
            payload, origin = fetch(url, expected)
            print("Fetched exact pinned source:", origin, flush=True)
        else:
            parser.error("Select --tools or explicitly --fetch-upstream")
        if digest(payload) != expected:
            raise ValueError("Upstream source hash mismatch; no source executed")
        destination = provider / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    dtb = root / "fixture.dtb"
    dtb.write_bytes(
        struct.pack(">10I", 0xD00DFEED, 72, 56, 72, 40, 17, 16, 0, 0, 16)
        + bytes(16)
        + struct.pack(">4I", 1, 0, 2, 9)
    )
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
    ramdisk = root / "ramdisk"
    ramdisk.write_bytes(
        codecs.encode(cpio.pack({"schema": 1, "model": "ramdisk-cpio", "entries": [entry]}), "gzip")
    )
    kernel = root / "kernel"
    kernel.write_bytes(b"SYNTHETIC KERNEL" * 64)
    config = root / "bootconfig"
    config.write_bytes(b"androidboot.fixture=1\n")
    for family, versions in [("BOOT", range(5)), ("VENDOR_BOOT", (3, 4))]:
        for version in versions:
            image = root / f"{family.lower()}{version}.img"
            command = [
                sys.executable,
                str(provider / "mkbootimg.py"),
                "--header_version",
                str(version),
                "--pagesize",
                "4096" if version >= 3 else "2048",
                "--board",
                "fixture",
            ]
            if family == "BOOT":
                command += [
                    "--kernel",
                    str(kernel),
                    "--ramdisk",
                    str(ramdisk),
                    "--cmdline",
                    "console=synthetic",
                    "--os_version",
                    "12.3.4",
                    "--os_patch_level",
                    "2026-10",
                    "--output",
                    str(image),
                ]
                if version in (1, 2):
                    command += ["--recovery_dtbo", str(dtb)]
                if version == 2:
                    command += ["--dtb", str(dtb)]
            else:
                command += [
                    "--vendor_boot",
                    str(image),
                    "--dtb",
                    str(dtb),
                    "--vendor_cmdline",
                    "console=synthetic",
                ]
                if version == 3:
                    command += ["--vendor_ramdisk", str(ramdisk)]
                else:
                    command += ["--vendor_bootconfig", str(config)]
                    for index, kind in enumerate(("NONE", "PLATFORM", "RECOVERY", "DLKM")):
                        command += [
                            "--ramdisk_type",
                            kind,
                            "--ramdisk_name",
                            kind.lower(),
                            "--board_id3",
                            str(index),
                            "--vendor_ramdisk_fragment",
                            str(ramdisk),
                        ]
            built = run_command(command, timeout=20)
            if built["exit_code"]:
                raise ValueError("AOSP fixture generation failed: " + built["stderr"])
            differential = aosp(image, provider)
            rebuilt = roundtrip(image, root / f"workspace-{family}-{version}")
            records.append(
                {
                    "evidence_kind": "SYNTHETIC_UPSTREAM_TOOL_GENERATED",
                    "family": family,
                    "version": version,
                    "sha256": digest(read(image)),
                    "bytes": image.stat().st_size,
                    "differential": differential["status"],
                    "roundtrip": rebuilt["byte_identity"],
                    "semantic_equivalence": rebuilt["semantic_equivalence"],
                    "provider_source_hashes": PINNED,
                    "device_compatibility": "UNTESTED",
                }
            )
            print(family, version, differential["status"], rebuilt["byte_identity"], flush=True)
passed = all(
    r["differential"] == "AGREEMENT" and r["roundtrip"] == "BYTE_IDENTICAL" for r in records
)
write_json(
    data_dir() / "validation/phase4-aosp-qualified.json",
    {"release": "0.4.0", "result": "PASS" if passed else "FAIL", "records": records},
)
print(json.dumps({"status": "PASS" if passed else "FAIL", "cases": len(records)}))
raise SystemExit(0 if passed else 1)
