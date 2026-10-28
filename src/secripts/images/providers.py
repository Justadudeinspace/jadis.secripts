"""Optional installed providers. Never discover/run tools from corpus directories."""

import shutil
from pathlib import Path
from secripts.runner import run_command

TOOLS = ("file", "dtc", "avbtool", "lz4", "unlz4", "cpio")


def availability():
    return {
        name: {
            "path": shutil.which(name),
            "state": "AVAILABLE" if shutil.which(name) else "MISSING",
        }
        for name in TOOLS
    }


def evidence(path, formats):
    reports = []
    for name in ("file", "avbtool"):
        tool = shutil.which(name)
        if not tool:
            reports.append({"provider": name, "status": "UNSUPPORTED"})
            continue
        resolved = Path(tool).resolve()
        if "research" in resolved.parts or "storage" in resolved.parts:
            reports.append(
                {"provider": name, "status": "BLOCKED", "reason": "Untrusted provider location"}
            )
            continue
        if name == "avbtool" and "AVB" not in formats:
            continue
        argv = (
            [tool, "--brief", "--", str(Path(path).resolve())]
            if name == "file"
            else [tool, "info_image", "--image", str(Path(path).resolve())]
        )
        result = run_command(argv, timeout=5)
        reports.append(
            {
                "provider": name,
                "status": result["result"],
                "command": result,
                "note": "External identification/metadata only; not signature or trust verification",
            }
        )
    return reports


def trusted_tool(name):
    tool = shutil.which(name)
    if not tool:
        return None
    resolved = Path(tool).resolve()
    if any(word in resolved.parts for word in ("research", "storage")):
        return None
    return str(resolved)


def inventory(*, probe=False):
    tools = {
        "file": (["--version"], ["identify"]),
        "avbtool": (["version"], ["info_image", "verify_image", "calculate_vbmeta_digest"]),
        "lz4": (["--version"], ["decode", "encode", "frame_oracle"]),
        "gzip": (["--version"], ["decode", "gzip_oracle"]),
        "dtc": (["--version"], ["fdt_oracle"]),
        "mkdtimg": (["--help"], ["dtbo_oracle"]),
        "mkbootimg": (["--help"], ["aosp_boot_oracle"]),
        "unpack_bootimg": (["--help"], ["aosp_unpack_oracle"]),
    }
    records = []
    for name, (version_args, capabilities) in tools.items():
        tool = trusted_tool(name)
        row = {
            "provider": name,
            "path": tool,
            "availability": "AVAILABLE" if tool else "ABSENT",
            "capabilities": capabilities,
            "version": "UNTESTED",
            "invocation": None,
        }
        if probe and tool:
            command = run_command([tool, *version_args], timeout=5)
            row.update(
                invocation=command,
                version=command["stdout"].splitlines()[0][:160]
                if "--help" not in version_args and command["stdout"].splitlines()
                else "UNKNOWN",
            )
        records.append(row)
    return {
        "schema": 1,
        "providers": records,
        "native_evidence": "INDEPENDENT",
        "note": "Presence is not provider qualification; versions run only with explicit --probe",
    }
