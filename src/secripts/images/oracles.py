"""Explicit differential checks against hash-pinned AOSP source; never corpus executables."""

from pathlib import Path
import shlex
import sys
import tempfile
from secripts.images.artifacts import read, digest, evidence
from secripts.images.bootmodel import model
from secripts.images.providers import trusted_tool
from secripts.runner import run_command
from secripts.safety import SecError

AOSP_REVISION = "d2bb0af5ba6d3198a3e99529c97eda1be0b5a093"

PINNED = {
    "mkbootimg.py": "37d84b3d162e0bc62e36c1f4e1c63c85ea0caa9f29be023eb2f8efe006ad948c",
    "unpack_bootimg.py": "a9d260978a63bd06a24b6347e7dee8a28ff96639793caea15dff6aa491316308",
    "gki/generate_gki_certificate.py": "1bb1feec68a13da18d581aa2c631798f86f6bc10b55d587b2dd31446a0f8a203",
}
PATH_FLAGS = {
    "--kernel",
    "--ramdisk",
    "--second",
    "--dtb",
    "--recovery_dtbo",
    "--vendor_ramdisk",
    "--vendor_ramdisk_fragment",
    "--vendor_bootconfig",
}
VALUE_FLAGS = {
    "--header_version",
    "--cmdline",
    "--board",
    "--base",
    "--kernel_offset",
    "--ramdisk_offset",
    "--second_offset",
    "--tags_offset",
    "--dtb_offset",
    "--pagesize",
    "--os_version",
    "--os_patch_level",
    "--vendor_cmdline",
    "--ramdisk_type",
    "--ramdisk_name",
    *(f"--board_id{n}" for n in range(16)),
}


def aosp(path, tools):
    tools = Path(tools)
    for name, expected in PINNED.items():
        if digest(read(tools / name, 1024**2)) != expected:
            raise SecError("AOSP provider source hash mismatch; executable refused", 4)
    native = model(path)
    commands = []
    with tempfile.TemporaryDirectory(prefix="js-aosp-oracle-") as directory:
        root = Path(directory)
        provider = root / "provider"
        provider.mkdir()
        for name in PINNED:
            destination = provider / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(read(tools / name, 1024**2))
        tools = provider
        original = root / "original.img"
        original.write_bytes(read(path))
        out = root / "unpacked"
        command = run_command(
            [
                sys.executable,
                str((tools / "unpack_bootimg.py").resolve()),
                "--boot_img",
                str(original),
                "--out",
                str(out),
                "--format=mkbootimg",
            ],
            timeout=20,
        )
        commands.append(command)
        if command["exit_code"]:
            return {
                "status": "PROVIDER_FAILED",
                "commands": commands,
                "native": native,
                "exit_code": 1,
            }
        arguments = shlex.split(command["stdout"])
        validated = []
        cursor = 0
        while cursor < len(arguments):
            flag = arguments[cursor]
            cursor += 1
            if flag == "--id":
                validated.append(flag)
                continue
            if flag not in PATH_FLAGS | VALUE_FLAGS or cursor >= len(arguments):
                raise SecError(
                    "Unsupported AOSP reconstruction argument; no execution attempted", 4
                )
            value = arguments[cursor]
            cursor += 1
            if len(value) > 4096 or "\0" in value:
                raise SecError("Excessive oracle argument", 4)
            if flag in PATH_FLAGS:
                component = Path(value)
                if (
                    component.is_symlink()
                    or not component.resolve().is_relative_to(out.resolve())
                    or not component.is_file()
                ):
                    raise SecError("Oracle payload path escaped extraction root", 4)
            if flag == "--vendor_ramdisk_fragment":
                validated.extend([flag, value])
            else:
                validated.append(flag + "=" + value)
        rebuilt = root / "oracle.img"
        output_flag = "--vendor_boot" if native["format"] == "VENDOR_BOOT" else "--output"
        build = run_command(
            [
                sys.executable,
                str((tools / "mkbootimg.py").resolve()),
                *validated,
                output_flag,
                str(rebuilt),
            ],
            timeout=20,
        )
        commands.append(build)
        if build["exit_code"] or not rebuilt.is_file():
            return {"status": "PROVIDER_FAILED", "commands": commands, "exit_code": 1}
        after = model(rebuilt)
        # Compare only fields demonstrated by both paths; raw padding identity is a separate observation.
        first = {
            s["name"]: (s["size"], s["sha256"]) for s in native["sections"] if s["name"] != "header"
        }
        second = {
            s["name"]: (s["size"], s["sha256"]) for s in after["sections"] if s["name"] != "header"
        }
        agreement = first == second and native["header"] == after["header"]
        result = {
            "schema": 1,
            "status": "AGREEMENT" if agreement else "DISAGREEMENT",
            "native_components": first,
            "provider_components": second,
            "native_header": native["header"],
            "provider_header": after["header"],
            "commands": commands,
            "provider_source_hashes": PINNED,
            "byte_identity": digest(read(original)) == digest(read(rebuilt)),
            "cryptographic_state": "UNVERIFIED",
            "device_compatibility": "UNTESTED",
            "exit_code": 0,
        }
    receipt = evidence("image.differential", source=path, provider_comparison=result)
    return {**result, "receipt_id": receipt["receipt_id"]}


def compression(path):
    """Explicit installed lz4/gzip decoder cross-check; bounded file-backed output."""
    from secripts.images import codecs

    raw = read(path, codecs.CAP)
    decoded, native = codecs.decode(raw)
    tool_name = "lz4" if native["codec"] == "lz4" else "gzip" if native["codec"] == "gzip" else None
    tool = trusted_tool(tool_name) if tool_name else None
    if not tool:
        return {"status": "PROVIDER_UNAVAILABLE", "native": native}
    # run_command bounds captured output; compare only small oracle fixtures to avoid truncation ambiguity.
    if len(decoded) > 64 * 1024:
        return {
            "status": "BLOCKED",
            "reason": "Differential output capture limited to 64 KiB; native decode remains available",
        }
    import subprocess
    import resource

    def output_limit():
        resource.setrlimit(resource.RLIMIT_FSIZE, (65537, 65537))

    with tempfile.TemporaryDirectory(prefix="js-codec-oracle-") as directory:
        source = Path(directory) / "input"
        source.write_bytes(raw)
        target = Path(directory) / "output"
        errors = Path(directory) / "errors"
        try:
            with target.open("wb") as stream, errors.open("wb") as error_stream:
                process = subprocess.run(
                    [tool, "-d", "-c", str(source)],
                    stdout=stream,
                    stderr=error_stream,
                    timeout=5,
                    check=False,
                    preexec_fn=output_limit,
                )
        except subprocess.TimeoutExpired:
            return {"status": "PROVIDER_TIMEOUT"}
        external = read(target, 65537)
    return {
        "schema": 1,
        "status": "AGREEMENT"
        if process.returncode == 0 and external == decoded
        else "DISAGREEMENT",
        "provider": tool,
        "exit_code": process.returncode,
        "native_sha256": digest(decoded),
        "provider_sha256": digest(external),
    }
