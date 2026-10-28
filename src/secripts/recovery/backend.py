"""Only TWRP implemented; backend contract does not invent additional recoveries."""

from typing import Protocol
from secripts.safety import SecError


class Backend(Protocol):
    name: str

    def build_command(self, lunch: str, target: str) -> list[str]: ...


class TWRP:
    name = "twrp"
    targets = {
        "recoveryimage": "recovery.img",
        "bootimage": "boot.img",
        "vendorbootimage": "vendor_boot.img",
        "initbootimage": "init_boot.img",
    }

    def build_command(self, lunch: str, target: str) -> list[str]:
        # A fixed shell program is needed for upstream shell functions. User values are positional
        # arguments, never interpolated into code. Source checkouts are executable trusted input.
        targets = [target] if isinstance(target, str) else list(target)
        if (
            not targets
            or len(set(targets)) != len(targets)
            or any(t not in self.targets for t in targets)
        ):
            raise SecError("Unsupported/duplicate build targets", 2)
        return [
            "bash",
            "-c",
            'set -e; source build/envsetup.sh; lunch "$1"; shift; mka -j2 "$@"',
            "secripts-twrp",
            lunch,
            *targets,
        ]
