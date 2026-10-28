"""Read-only single-device inspection; never probe by flashing or rebooting."""

import re
from secripts.runner import run_command
from secripts.safety import SecError

PROPERTIES = (
    "ro.product.manufacturer",
    "ro.product.model",
    "ro.product.device",
    "ro.product.cpu.abi",
    "ro.build.version.release",
    "ro.boot.slot_suffix",
    "ro.boot.verifiedbootstate",
    "ro.boot.flash.locked",
    "ro.boot.dynamic_partitions",
)


def inspect_device() -> dict:
    command = run_command(["adb", "devices", "-l"])
    if command["result"] != "PASS":
        raise SecError("ADB unavailable or failed", 3)
    rows = [line.split() for line in command["stdout"].splitlines()[1:] if line.strip()]
    devices = [row[0] for row in rows if len(row) > 1 and row[1] == "device"]
    if len(devices) != 1:
        raise SecError(
            "Exactly one authorized ADB device required; disconnect extras or authorize device.", 3
        )
    serial = devices[0]
    if not re.fullmatch(r"[A-Za-z0-9_.:-]+", serial) or serial.startswith("-"):
        raise SecError("Unsupported transport identifier", 4)
    properties, commands = {}, [command]
    for prop in PROPERTIES:
        result = run_command(["adb", "-s", serial, "shell", "getprop", prop])
        commands.append(result)
        properties[prop] = {
            "value": result["stdout"].strip() or None,
            "state": "OBSERVED"
            if result["result"] == "PASS" and result["stdout"].strip()
            else "UNRESOLVED",
        }
    return {
        "serial": serial,
        "properties": properties,
        "commands": commands,
        "partitions": "UNRESOLVED",
        "temporary_boot_support": "UNRESOLVED",
        "hardware_qualification": "UNTESTED",
    }
