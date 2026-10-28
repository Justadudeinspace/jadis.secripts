"""Only TWRP implemented; backend contract does not invent additional recoveries."""

from typing import Protocol


class Backend(Protocol):
    name: str

    def build_command(self, lunch: str, target: str) -> list[str]: ...


class TWRP:
    name = "twrp"
    targets = {
        "recoveryimage": "recovery.img",
        "bootimage": "boot.img",
        "vendorbootimage": "vendor_boot.img",
    }

    def build_command(self, lunch: str, target: str) -> list[str]:
        # A fixed shell program is needed for upstream shell functions. User values are positional
        # arguments, never interpolated into code. Source checkouts are executable trusted input.
        return [
            "bash",
            "-c",
            'set -e; source build/envsetup.sh; lunch "$1"; mka -j2 "$2"',
            "secripts-twrp",
            lunch,
            target,
        ]
