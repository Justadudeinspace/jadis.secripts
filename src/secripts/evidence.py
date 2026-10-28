"""Small evidence primitives shared by inspections; status is not an invocation exit code."""

from dataclasses import dataclass, field
from collections.abc import Callable
import time
from secripts.runner import run_command

STATES = {"PASS", "WARN", "FAIL", "UNKNOWN", "UNTESTED", "BLOCKED", "UNSUPPORTED"}


def observation(status, evidence=None, reason="", remediation="") -> dict:
    if status not in STATES:
        raise ValueError("Unknown evidence state")
    return {"status": status, "evidence": evidence, "reason": reason, "remediation": remediation}


def overall(checks) -> str:
    states = {v.get("status", "UNKNOWN") for v in checks}
    for state in ("FAIL", "BLOCKED", "UNSUPPORTED", "WARN", "UNKNOWN", "UNTESTED"):
        if state in states:
            return state
    return "PASS" if states else "UNKNOWN"


@dataclass
class Collector:
    commands: list = field(default_factory=list)
    deadline: float | None = None
    runner: Callable[..., dict] | None = None

    def command(self, argv, *, timeout=5, identifiers=()) -> dict:
        if self.deadline is not None and time.monotonic() >= self.deadline:
            from secripts.secrets import mask_identifiers

            value = mask_identifiers(
                {
                    "executable": argv[0],
                    "arguments": list(argv[1:]),
                    "result": "BLOCKED",
                    "exit_code": None,
                    "stdout": "",
                    "stderr": "Inspection time budget exhausted",
                    "duration": 0,
                },
                identifiers,
            )
        else:
            remaining = (
                timeout
                if self.deadline is None
                else max(0.01, min(timeout, self.deadline - time.monotonic()))
            )
            value = (self.runner or run_command)(
                list(argv), timeout=remaining, identifiers=identifiers
            )
        self.commands.append(value)
        return value

    def text(self, argv, **kwargs):
        value = self.command(argv, **kwargs)
        return value.get("stdout", "").strip() if value["result"] == "PASS" else None
