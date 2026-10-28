"""Lazy host context and XDG state paths."""

import os
import platform
import sys
from pathlib import Path


def data_dir() -> Path:
    path = Path(
        os.environ.get(
            "SECRIPTS_DATA_HOME",
            Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "secripts",
        )
    )
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def host() -> dict:
    termux = any(
        "com.termux" in value
        for value in (
            os.environ.get("PREFIX", ""),
            sys.base_prefix,
            str(Path(sys.executable).resolve()),
        )
    )
    proot = bool(os.environ.get("PROOT_TMP_DIR") or os.environ.get("PROOT_LOADER"))
    return {
        "os": platform.system(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "termux": termux,
        "proot": "DETECTED" if proot else "UNKNOWN",
        "platform": "termux"
        if termux
        else "linux"
        if platform.system() == "Linux"
        else "unsupported",
    }
