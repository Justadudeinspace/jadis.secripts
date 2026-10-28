"""Recovery inspection shares the bounded, identifier-safe device dossier collector."""

from secripts.evidence import Collector
from secripts.devices import adb_inspect
from secripts.runner import run_command


def inspect_device() -> dict:
    collector = Collector(runner=run_command)
    value = adb_inspect(collector)
    return {**value, "commands": collector.commands}
