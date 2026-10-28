"""Read-only Android evidence. Transport identifiers remain in memory, never in returned receipts."""

import re
import time
from secripts.evidence import observation, overall
from secripts.safety import SecError
from secripts.secrets import mask_identifiers

PROPERTIES = {
    "identity": (
        "ro.product.manufacturer",
        "ro.product.model",
        "ro.product.device",
        "ro.product.name",
    ),
    "android": (
        "ro.build.version.release",
        "ro.build.version.sdk",
        "ro.build.version.security_patch",
    ),
    "build": ("ro.build.fingerprint", "ro.build.type", "ro.debuggable"),
    "security": ("ro.boot.verifiedbootstate", "ro.boot.flash.locked", "ro.secure"),
    "boot": (
        "ro.boot.slot_suffix",
        "ro.bootmode",
        "ro.boot.dynamic_partitions",
        "ro.virtual_ab.enabled",
    ),
    "hardware": ("ro.product.cpu.abi", "ro.product.cpu.abilist", "ro.hardware"),
}


def transports(c, backend="adb"):
    value = c.command([backend, "devices", "-l"], timeout=3)
    raw = value.get("stdout", "")
    rows = []
    malformed = False
    if value["result"] == "PASS":
        for line in raw.splitlines():
            if not line.strip() or line.startswith(("List of devices", "* daemon", "adb server")):
                continue
            parts = line.split()
            if (
                len(parts) < 2
                or not re.fullmatch(r"[A-Za-z0-9_.:-]+", parts[0])
                or parts[0].startswith("-")
            ):
                malformed = True
                continue
            state = parts[1]
            if state not in {
                "device",
                "unauthorized",
                "offline",
                "recovery",
                "sideload",
                "bootloader",
                "fastboot",
                "no",
            }:
                malformed = True
                continue
            rows.append(
                {
                    "serial": parts[0],
                    "state": "no permissions" if state == "no" else state,
                    "index": len(rows) + 1,
                }
            )
    # Enumeration can include unauthorized/offline identifiers and malformed sensitive data. Never
    # persist any raw transport listing, even when parsing fails.
    started = "daemon started successfully" in value.get("stderr", "")
    value["stdout"] = f"{len(rows)} transport(s); identifiers omitted"
    value["stderr"] = "[diagnostic output omitted]" if value.get("stderr") else ""
    return rows, observation(
        "UNKNOWN" if malformed else "PASS" if value["result"] == "PASS" else "WARN",
        {
            "count": len(rows),
            "states": [r["state"] for r in rows],
            "daemon_started_by_probe": started,
        },
        "Malformed transport output" if malformed else value["result"],
    )


def transport_summary(c, backend="adb", **params):
    rows, check = transports(c, backend)
    return {
        "status": check["status"],
        "transport": backend,
        "count": len(rows),
        "devices": [
            {"index": r["index"], "identifier": "[REDACTED_IDENTIFIER]", "state": r["state"]}
            for r in rows
        ],
        "evidence": check,
        "hardware_qualification": "UNTESTED",
    }


def select(c, backend, requested=None):
    rows, check = transports(c, backend)
    if check["status"] != "PASS":
        raise SecError(f"{backend} unavailable or malformed transport output", 3)
    if not rows:
        raise SecError(f"NO DEVICE: {backend}; exactly one authorized transport required", 3)
    if requested:
        rows = [r for r in rows if r["serial"] == requested]
    if len(rows) != 1:
        raise SecError(
            "Exactly one explicitly selected transport required; multiple or unmatched devices", 3
        )
    expected = "device" if backend == "adb" else "fastboot"
    if rows[0]["state"] != expected:
        raise SecError(
            f"Device is {rows[0]['state']}; authorization/transport must be resolved manually", 3
        )
    return rows[0]["serial"]


def adb_inspect(c, device=None, **params):
    c.deadline = time.monotonic() + 20
    serial = select(c, "adb", device)

    def command(args):
        return c.command(["adb", "-s", serial, "shell", *args], identifiers=(serial,), timeout=4)

    sections = {}
    checks = []
    for group, properties in PROPERTIES.items():
        sections[group] = {}
        for prop in properties:
            value = command(["getprop", prop])
            text = value.get("stdout", "").strip()
            check = observation(
                "PASS" if value["result"] == "PASS" and text else "UNKNOWN",
                text or None,
                "Observed property only; absence does not prove false",
            )
            sections[group][prop] = check
            checks.append(check)
    probes = {
        "battery": ["dumpsys", "battery"],
        "storage": ["df", "-k", "/data", "/sdcard"],
        "display": ["wm", "size"],
        "cpu": ["cat", "/proc/cpuinfo"],
        "memory": ["cat", "/proc/meminfo"],
        "packages": ["pm", "list", "packages"],
        "root_observation": ["id"],
    }
    for key, args in probes.items():
        value = command(args)
        text = value.get("stdout", "")
        if key == "cpu":
            text = "\n".join(
                line
                for line in text.splitlines()
                if line.split(":", 1)[0].strip()
                in {"processor", "model name", "CPU architecture", "Hardware", "Features"}
            )
        if key == "packages":
            evidence = {"count": sum(line.startswith("package:") for line in text.splitlines())}
            value["stdout"] = "Package names omitted; count only"
        else:
            evidence = text.strip() or None
            value["stdout"] = text
        check = observation(
            "PASS" if value["result"] == "PASS" and evidence else "UNKNOWN", evidence
        )
        sections[key] = check
        checks.append(check)
    result = {
        "schema": 1,
        "status": overall(checks),
        "transport": "adb",
        "identifier": "[REDACTED_IDENTIFIER]",
        "sections": sections,
        "partitions": "UNRESOLVED: no privileged probing",
        "root_observation_note": "id reports the existing shell UID; js never invokes su or adb root",
        "ownership": "Not inferred; explicit inspection is operator-authorized context",
        "hardware_qualification": "UNTESTED",
    }
    # Defensive second pass, including captured tool output, if a device embeds its serial in properties.
    c.commands[:] = mask_identifiers(c.commands, (serial,))
    return mask_identifiers(result, (serial,))


def fastboot_inspect(c, device=None, **params):
    c.deadline = time.monotonic() + 15
    serial = select(c, "fastboot", device)
    values = {}
    for name in (
        "product",
        "current-slot",
        "unlocked",
        "secure",
        "slot-count",
        "is-userspace",
        "partition-type:boot",
        "partition-type:recovery",
        "partition-type:vendor_boot",
    ):
        result = c.command(
            ["fastboot", "-s", serial, "getvar", name], identifiers=(serial,), timeout=4
        )
        text = result.get("stdout", "") + "\n" + result.get("stderr", "")
        match = re.search(r"(?:\(bootloader\)\s*)?" + re.escape(name) + r":\s*([^\r\n]+)", text)
        values[name] = observation(
            "PASS" if result["result"] == "PASS" and match else "UNKNOWN",
            match.group(1).strip() if match else None,
        )
    return {
        "schema": 1,
        "status": overall(values.values()),
        "transport": "fastboot",
        "identifier": "[REDACTED_IDENTIFIER]",
        "variables": values,
        "temporary_boot_support": "UNRESOLVED",
        "hardware_qualification": "UNTESTED",
    }
