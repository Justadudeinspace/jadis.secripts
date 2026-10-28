"""Typed, layered recovery build configuration. Overrides never become observations."""

from dataclasses import dataclass, asdict
import json
import re
from pathlib import Path
from secripts.recovery import projects
from secripts.safety import SecError
from secripts.secrets import contains_secret
from secripts.images.artifacts import read
from secripts.receipts import save


@dataclass(frozen=True)
class Flag:
    name: str
    kind: str
    documentation: str
    generations: tuple[str, ...] = ("twrp-12.1", "aosp-main", "aosp-13+")
    default: object = None
    editable: bool = True
    reference: str = "generic"


BOOLS = {
    "BOARD_USES_RECOVERY_AS_BOOT": "Recovery resources in boot, independent of artifact presence",
    "BOARD_USES_GENERIC_KERNEL_IMAGE": "GKI build context, not proof from Android version",
    "BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT": "Place recovery resources in vendor ramdisk",
    "BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT": "Source-specific recovery fragment inclusion",
    "BOARD_MOVE_GSI_AVB_KEYS_TO_VENDOR_BOOT": "Relocate GSI public verification keys; never import signing keys",
    "BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE": "Dedicated recovery obtains kernel externally through boot architecture",
    "PRODUCT_BUILD_RECOVERY_IMAGE": "Explicit recovery output policy; unset default is conditional",
    "BOARD_INCLUDE_RECOVERY_DTBO": "Recovery image DTBO relationship",
    "BOARD_INCLUDE_DTB_IN_BOOTIMG": "DTB inclusion in boot-format output",
    "BOARD_AVB_ENABLE": "Source build AVB metadata policy; not device enforcement",
    "PRODUCT_USE_DYNAMIC_PARTITIONS": "Dynamic logical partitions",
    "AB_OTA_UPDATER": "Slot-based update declaration",
    "PRODUCT_VIRTUAL_AB_OTA": "Virtual A/B declaration",
    "ALLOW_MISSING_DEPENDENCIES": "Dependency suppression is not supported by Secripts build validation",
}
SIZES = [
    "BOARD_RECOVERYIMAGE_PARTITION_SIZE",
    "BOARD_BOOTIMAGE_PARTITION_SIZE",
    "BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE",
    "BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE",
    "BOARD_DTBOIMG_PARTITION_SIZE",
]
PATHS = [
    "TARGET_PREBUILT_KERNEL",
    "TARGET_KERNEL_SOURCE",
    "BOARD_PREBUILT_BOOTIMAGE",
    "BOARD_PREBUILT_DTBOIMAGE",
    "BOARD_PREBUILT_DTBIMAGE_DIR",
    "TARGET_RECOVERY_FSTAB",
]
TEXT = [
    "TARGET_ARCH",
    "TARGET_ARCH_VARIANT",
    "TARGET_CPU_ABI",
    "TARGET_CPU_VARIANT",
    "TARGET_2ND_ARCH",
    "TARGET_2ND_ARCH_VARIANT",
    "TARGET_2ND_CPU_ABI",
    "TARGET_2ND_CPU_VARIANT",
    "TARGET_BOARD_PLATFORM",
    "TARGET_KERNEL_CONFIG",
    "BOARD_KERNEL_CMDLINE",
    "BOARD_BOOTCONFIG",
    "BOARD_KERNEL_IMAGE_NAME",
    "BOARD_MKBOOTIMG_ARGS",
    "TW_THEME",
]
CATALOG = {
    f.name: f
    for f in [
        *[
            Flag(
                k,
                "bool",
                v,
                default=False
                if k
                in {
                    "BOARD_USES_RECOVERY_AS_BOOT",
                    "BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT",
                    "BOARD_MOVE_GSI_AVB_KEYS_TO_VENDOR_BOOT",
                    "BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE",
                }
                else None,
            )
            for k, v in BOOLS.items()
        ],
        *[
            Flag(
                k,
                "size",
                "Positive partition size in bytes; never inferred from file size",
                generations=("aosp-main", "aosp-13+")
                if k == "BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE"
                else ("twrp-12.1", "aosp-main", "aosp-13+"),
            )
            for k in SIZES
        ],
        *[Flag(k, "path", "Explicit source-root-relative reviewed path") for k in PATHS],
        *[
            Flag(
                k,
                "text",
                "Literal build configuration; Make functions are not accepted as overrides",
            )
            for k in TEXT
        ],
        Flag("BOARD_BOOT_HEADER_VERSION", "header", "Boot header version, not Android generation"),
        Flag("BOARD_KERNEL_PAGESIZE", "page", "Boot image page alignment"),
    ]
}


def spec(name):
    if name in CATALOG:
        return CATALOG[name]
    if re.fullmatch(
        r"BOARD_AVB_(?:BOOT|INIT_BOOT|RECOVERY|VBMETA_SYSTEM|VBMETA_VENDOR|VENDOR_BOOT)_(?:ALGORITHM|KEY_PATH|ROLLBACK_INDEX|ROLLBACK_INDEX_LOCATION)",
        name,
    ):
        kind = (
            "integer"
            if "ROLLBACK_INDEX" in name
            else "path"
            if name.endswith("KEY_PATH")
            else "text"
        )
        return Flag(
            name,
            kind,
            "AVB source declaration; signing and rollback edits are protected",
            editable=False,
            reference="avb",
        )
    return None


def normalize(flag, value):
    if value is None:
        return None
    if isinstance(value, (list, dict)) or contains_secret(str(value)):
        raise SecError("Unsafe or secret-like flag value", 4)
    text = str(value)
    if (
        len(text) > 2048
        or any(c in text for c in "\n\r\0`$;\\#")
        or re.search(r"(?i)(?:serialno|imei|android_id)\s*=", text)
    ):
        raise SecError("Flag must be a bounded literal; Make/shell injection refused", 4)
    if flag.kind == "bool":
        if value is True or text == "true":
            return True
        if value is False or text in {"false", ""}:
            return False
        raise SecError("Boolean flags accept true, false or empty; Make export uses true/empty", 2)
    if flag.kind in {"size", "integer", "header", "page"}:
        try:
            n = int(text, 0)
        except ValueError as exc:
            raise SecError("Flag requires a literal integer", 2) from exc
        if (
            n < 0
            or n > 2**63 - 1
            or flag.kind == "size"
            and n == 0
            or flag.kind == "header"
            and n not in range(5)
            or flag.kind == "page"
            and n not in {2048, 4096, 8192, 16384, 32768, 65536}
        ):
            raise SecError("Flag integer out of supported bounds", 2)
        return n
    if flag.kind == "path" and (
        text.startswith(("/", "-"))
        or ".." in Path(text).parts
        or not re.fullmatch(r"[A-Za-z0-9_./+-]+", text)
    ):
        raise SecError("Path flags require a safe source-root-relative literal", 4)
    if not re.fullmatch(r'[A-Za-z0-9_./:=,+ @()"\'-]*', text):
        raise SecError("Unsupported literal flag characters", 4)
    return text


def generation(name):
    state = projects.load(name, "dependencies", {}) or {}
    return state.get("lock", {}).get("source", {}).get("generation", "UNKNOWN")


def view(name):
    from secripts.recovery import model
    from secripts.recovery.architecture import FLAG_FEATURES

    device = model.report(name)
    state = projects.load(name, "flags", {"schema": 1, "overrides": {}, "history": []})
    if not isinstance(state.get("overrides"), dict) or len(state["overrides"]) > 128:
        raise SecError("Malformed flag state", 3)
    names = (
        set(CATALOG)
        | {r["name"] for r in device.get("configuration_evidence", []) if spec(r["name"])}
        | set(state["overrides"])
    )
    values = {}
    gen = generation(name)
    for key in sorted(names):
        flag = spec(key)
        if not flag:
            raise SecError("Unknown flag in stored state", 3)
        observed = []
        for row in device.get("configuration_evidence", []):
            if row["name"] != key:
                continue
            try:
                value = normalize(flag, row["resolved_value"])
            except SecError:
                value = None
            observed.append(
                {
                    "value": value,
                    "state": row["state"] if value is not None else "UNKNOWN",
                    "source": row["source"],
                    "location": row["location"],
                    "raw_literal": row["value"],
                }
            )
        distinct = {json.dumps(r["value"], sort_keys=True) for r in observed}
        observation = {
            "value": observed[0]["value"] if len(distinct) == 1 else None,
            "state": "UNKNOWN"
            if not observed
            else "CONFLICT"
            if len(distinct) > 1
            else observed[0]["state"],
            "evidence": observed,
        }
        derived = {"value": None, "state": "UNKNOWN", "evidence": []}
        if key in FLAG_FEATURES:
            feature = device["recovery_architecture"]["features"][FLAG_FEATURES[key]]
            derived = {
                "value": feature["value"],
                "state": "DERIVED"
                if feature["state"] not in {"UNKNOWN", "CONFLICT"}
                else feature["state"],
                "evidence": feature["evidence"],
            }
        if key == "TARGET_ARCH":
            derived = device["fields"]["architecture"]
        default = flag.default if gen in flag.generations else None
        override = state["overrides"].get(key)
        if override is not None:
            if not isinstance(override, dict) or override.get("source") != "USER_OVERRIDE":
                raise SecError("Malformed override", 3)
            effective = {"value": normalize(flag, override["value"]), "source": "USER_OVERRIDE"}
        elif observation["value"] is not None and observation["state"] not in {
            "UNKNOWN",
            "CONFLICT",
        }:
            effective = {
                "value": observation["value"],
                "source": "OBSERVED" if observation["state"] == "OBSERVED" else "DECLARED",
            }
        elif derived.get("value") is not None and derived["state"] not in {"UNKNOWN", "CONFLICT"}:
            effective = {"value": derived["value"], "source": "DERIVED"}
        else:
            effective = {
                "value": default,
                "source": "DEFAULT" if default is not None else "UNKNOWN",
            }
        values[key] = {
            **asdict(flag),
            "observed": observation,
            "derived": derived,
            "default": default,
            "user_override": override,
            "effective": effective,
            "conflicts": bool(
                override is not None
                and observation["value"] is not None
                and effective["value"] != observation["value"]
            ),
        }
    return {
        "schema": 1,
        "model": name,
        "source_generation": gen,
        "flags": values,
        "configuration_sha256": projects.digest({k: v["effective"] for k, v in values.items()}),
        "history": state.get("history", []),
        "evidence_policy": "USER_OVERRIDE is a configuration choice, never observation",
    }


def validate(name, configuration=None):
    configuration = configuration or view(name)
    rows = []
    f = configuration["flags"]
    gen = configuration["source_generation"]

    def val(k):
        return f[k]["effective"]["value"] if k in f else None

    def finding(state, message, flag=None):
        rows.append({"state": state, "flag": flag, "reason": message})

    for key, row in f.items():
        if row["conflicts"]:
            finding("CONFLICT", "Override differs from observed declaration", key)
        if row["observed"]["state"] == "CONFLICT":
            finding("CONFLICT", "Source declarations disagree; no automatic preference", key)
        if (
            row["effective"]["value"] is not None
            and gen != "UNKNOWN"
            and gen not in row["generations"]
        ):
            finding(
                "UNSUPPORTED_FOR_SOURCE_GENERATION",
                "Flag support not established in selected source",
                key,
            )
        if row["effective"]["source"] == "UNKNOWN":
            continue
        if (
            any(o["raw_literal"] == "false" for o in row["observed"]["evidence"])
            and row["kind"] == "bool"
        ):
            finding("UNRESOLVED", "Native AOSP boolean uses true/empty; review literal false", key)
    if val("BOARD_USES_RECOVERY_AS_BOOT") and val("BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT"):
        finding(
            "INVALID_COMBINATION",
            "AOSP rejects simultaneous recovery-as-boot and moved vendor recovery resources",
        )
    if (
        val("BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT")
        and val("BOARD_USES_GENERIC_KERNEL_IMAGE") is not True
    ):
        finding(
            "MISSING_DEPENDENCY", "Vendor recovery resources require confirmed GKI/source context"
        )
    if val("BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE"):
        from secripts.recovery import model

        device = model.report(name)
        if not any(
            a["role"] == "boot" and a.get("kernel_bytes", 0)
            for a in device.get("artifact_observations", [])
        ) and not val("BOARD_PREBUILT_BOOTIMAGE"):
            finding(
                "MISSING_DEPENDENCY",
                "Excluded recovery kernel requires boot kernel/prebuilt evidence",
            )
    if val("BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE") and not any(
        k.startswith("BOARD_AVB_INIT_BOOT_") and r["effective"]["value"] is not None
        for k, r in f.items()
    ):
        finding("UNRESOLVED", "init_boot size set without associated AVB relationship evidence")
    from secripts.recovery import model

    device = model.report(name)
    if device["recovery_architecture"]["features"]["dedicated_recovery_partition"][
        "value"
    ] is True and not val("BOARD_RECOVERYIMAGE_PARTITION_SIZE"):
        finding(
            "MISSING_DEPENDENCY",
            "Dedicated recovery size is absent; image file size is not partition size",
        )
    if val("ALLOW_MISSING_DEPENDENCIES"):
        finding(
            "INVALID_COMBINATION",
            "Secripts refuses to qualify dependency-suppressed builds; review upstream setting explicitly",
        )
    if gen == "UNKNOWN":
        finding("UNRESOLVED", "Select and pin source generation before claiming flag applicability")
    blocking = {"INVALID_COMBINATION", "MISSING_DEPENDENCY", "UNSUPPORTED_FOR_SOURCE_GENERATION"}
    return {
        "schema": 1,
        "model": name,
        "status": "FAIL"
        if any(r["state"] in blocking for r in rows)
        else "WARN"
        if rows
        else "PASS",
        "findings": rows,
        "configuration_sha256": configuration["configuration_sha256"],
        "qualification": "CONFIGURATION_RULES_ONLY; Make acceptance and hardware remain separate",
    }


def change(name, key, value=None, *, action="set", reason="", acknowledge=False):
    from secripts.recovery import model

    model.load(name)
    flag = spec(key)
    if flag is None:
        raise SecError("Unknown build flag; use flags ls", 2)
    if not flag.editable:
        raise SecError("Rollback/signing declarations are read-only; no index or key changes", 4)
    if contains_secret(reason) or len(reason) > 1024:
        raise SecError("Unsafe developer note", 4)
    with projects.locked(name):
        old = view(name)
        state = projects.load(name, "flags", {"schema": 1, "overrides": {}, "history": []})
        previous = state["overrides"].get(key)
        if action in {"set", "unset"}:
            normalized = (
                normalize(flag, value)
                if action == "set"
                else False
                if flag.kind == "bool"
                else None
            )
            observation = old["flags"][key]["observed"]
            if (
                observation["value"] is not None
                and normalized != observation["value"]
                and not acknowledge
            ):
                raise SecError(
                    "Override conflicts with evidence; review flags sh and repeat with --acknowledge-conflict to store a choice, not evidence",
                    4,
                )
            state["overrides"][key] = {
                "value": normalized,
                "source": "USER_OVERRIDE",
                "timestamp": projects.now(),
                "reason": reason,
                "previous_value": previous["value"] if previous else None,
            }
        elif action == "reset":
            state["overrides"].pop(key, None)
        else:
            raise SecError("Unknown flag action", 2)
        if len(state["history"]) >= 256:
            raise SecError(
                "Override history budget reached; export/review before further changes", 4
            )
        state["history"].append(
            {
                "flag": key,
                "action": action,
                "previous": previous,
                "current": state["overrides"].get(key),
                "timestamp": projects.now(),
                "reason": reason,
            }
        )
        projects.store(name, "flags", state)
    result = view(name)
    save(
        "recovery.flags." + action,
        "MUTATING",
        [],
        result="PASS",
        model=name,
        flag=key,
        configuration_sha256=result["configuration_sha256"],
    )
    return {
        "schema": 1,
        "flag": result["flags"][key],
        "validation": validate(name, result),
        "configuration_sha256": result["configuration_sha256"],
    }


def make(configuration):
    lines = ["# JADIS // SECRIPTS — reviewed configuration; overrides are not evidence"]
    provenance = []
    for key, row in configuration["flags"].items():
        value = row["effective"]["value"]
        if value is None:
            if row["effective"]["source"] == "USER_OVERRIDE":
                lines.append("undefine " + key)
                provenance.append(
                    {
                        "line": len(lines),
                        "flag": key,
                        "value": None,
                        "source": "USER_OVERRIDE",
                        "override": row["user_override"],
                    }
                )
            continue
        rendered = "true" if value is True else "" if value is False else str(value)
        lines.append(key + " := " + rendered)
        provenance.append(
            {
                "line": len(lines),
                "flag": key,
                "value": value,
                "source": row["effective"]["source"],
                "observed": row["observed"],
                "derived": row["derived"],
                "override": row["user_override"],
            }
        )
    return "\n".join(lines) + "\n", provenance


def export(name, output=None, format="json"):
    state = view(name)
    payload = (
        make(state)[0]
        if format == "make"
        else json.dumps(
            {
                "schema": 1,
                "kind": "SECRIPTS_FLAG_PROFILE",
                "overrides": {
                    k: v["user_override"]
                    for k, v in state["flags"].items()
                    if v["user_override"] is not None
                },
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    return projects.export_file(output, payload) if output else payload


def import_profile(name, path, acknowledge=False):
    data = json.loads(read(Path(path), 128 * 1024))
    if (
        data.get("schema") != 1
        or data.get("kind") != "SECRIPTS_FLAG_PROFILE"
        or not isinstance(data.get("overrides"), dict)
        or len(data["overrides"]) > 128
    ):
        raise SecError("Unsupported profile schema", 2)
    # Preflight all entries; no partial import on an invalid/sensitive value.
    current = view(name)
    for key, row in data["overrides"].items():
        flag = spec(key)
        if not flag or not flag.editable or not isinstance(row, dict):
            raise SecError("Profile contains unsupported/protected flag", 4)
        value = normalize(flag, row.get("value"))
        note = row.get("reason", "")
        if not isinstance(note, str) or contains_secret(note) or len(note) > 1024:
            raise SecError("Unsafe profile note", 4)
        observed = current["flags"].get(key, {}).get("observed", {}).get("value")
        if observed is not None and value != observed and not acknowledge:
            raise SecError("Profile conflicts with evidence; explicit acknowledgement required", 4)
    with projects.locked(name):
        state = projects.load(name, "flags", {"schema": 1, "overrides": {}, "history": []})
        if len(state["history"]) >= 256:
            raise SecError("Override history budget reached", 4)
        for key, row in data["overrides"].items():
            prior = state["overrides"].get(key)
            state["overrides"][key] = {
                "value": normalize(spec(key), row["value"]),
                "source": "USER_OVERRIDE",
                "timestamp": projects.now(),
                "reason": row.get("reason", ""),
                "previous_value": prior["value"] if prior else None,
            }
        state["history"].append(
            {
                "action": "import",
                "profile_sha256": projects.digest(data),
                "timestamp": projects.now(),
            }
        )
        projects.store(name, "flags", state)
    save(
        "recovery.flags.import",
        "MUTATING",
        [],
        result="PASS",
        model=name,
        profile_sha256=projects.digest(data),
    )
    return view(name)


def profile(action, name=None, label=None, acknowledge=False):
    from secripts.context import data_dir
    from secripts.recovery.model import name_valid

    root = data_dir() / "recovery/flag-profiles"
    if action == "list":
        return sorted(p.stem for p in root.glob("*.json"))
    path = root / (name_valid(label) + ".json")
    if action == "save":
        return (
            projects.export_file(path, export(name))
            if root.exists()
            else _first_profile(root, path, name)
        )
    if action == "apply":
        return import_profile(name, path, acknowledge)
    data = json.loads(read(path, 128 * 1024))
    current = json.loads(export(name))
    return {
        "schema": 1,
        "profile": label,
        "changes": {
            key: {"current": current["overrides"].get(key), "profile": data["overrides"].get(key)}
            for key in sorted(set(current["overrides"]) | set(data["overrides"]))
            if current["overrides"].get(key, {}).get("value")
            != data["overrides"].get(key, {}).get("value")
        },
    }


def _first_profile(root, path, name):
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    return projects.export_file(path, export(name))
