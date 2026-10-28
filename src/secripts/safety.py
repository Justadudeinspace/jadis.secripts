"""Shared risk enforcement. A confirmation is bound to a concrete action."""

from enum import StrEnum
import os
import sys


class Risk(StrEnum):
    READ_ONLY = "READ_ONLY"
    MUTATING = "MUTATING"
    PRIVILEGED = "PRIVILEGED"
    DESTRUCTIVE = "DESTRUCTIVE"


class SecError(Exception):
    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


def authorize(
    risk: Risk, description: str, *, dry_run: bool = False, identity: str | None = None
) -> None:
    if dry_run:
        return
    if risk == Risk.PRIVILEGED and os.geteuid() != 0:
        raise SecError("Requires explicit privileged environment; js never elevates.", 3)
    if risk == Risk.DESTRUCTIVE:
        if not sys.stdin.isatty():
            raise SecError("Destructive action refused without an interactive terminal.", 4)
        phrase = f"CONFIRM {identity or description}"
        print(description)
        if input(f"Type exactly {phrase!r}: ") != phrase:
            raise SecError("Confirmation did not match; no action taken.", 4)
