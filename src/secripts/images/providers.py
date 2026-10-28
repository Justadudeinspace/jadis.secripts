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
