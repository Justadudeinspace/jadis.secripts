"""Local recovery device evidence ledger; conflicting sources are never silently preferred."""

from datetime import datetime, timezone
import copy
import json
from pathlib import Path
import re
from secripts.context import data_dir
from secripts.receipts import write_json, save
from secripts.safety import SecError
from secripts.images.common import artifact_hash

STATES = {"OBSERVED", "DECLARED", "DERIVED", "INFERRED", "USER_SUPPLIED", "UNKNOWN", "CONFLICT"}
ROLES = {
    "boot",
    "vendor_boot",
    "init_boot",
    "recovery",
    "vbmeta",
    "vbmeta_system",
    "vbmeta_vendor",
    "dtbo",
    "dtb",
    "ramdisk",
    "kernel",
}
FIELDS = (
    "architecture",
    "codename",
    "manufacturer",
    "platform",
    "android_generation",
    "boot_header",
    "recovery_arrangement",
    "ab",
    "virtual_ab",
    "dynamic_partitions",
    "metadata",
    "userdata",
    "encryption",
    "avb",
    "kernel",
    "dtb",
    "dtbo",
    "ramdisk_compression",
    "vendor_fragments",
    "fstab",
    "dependencies",
)


def name_valid(name):
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", name):
        raise SecError("Model name must be a safe lowercase identifier", 2)
    return name


def model_path(name):
    return data_dir() / "recovery/devices" / f"{name_valid(name)}.json"


def load(name):
    try:
        from secripts.images.artifacts import read

        value = json.loads(read(model_path(name), 8 * 1024**2))
        if (
            value.get("schema") not in (1, 2)
            or value.get("name") != name
            or not isinstance(value.get("evidence"), list)
            or not isinstance(value.get("sources"), list)
        ):
            raise ValueError()
        for fact in value["evidence"]:
            if fact.get("state") not in STATES or fact.get("source") not in {
                s["id"] for s in value["sources"]
            }:
                raise ValueError()
        if value["schema"] == 1:
            value["loaded_from_schema"] = 1
            value["schema"] = 2
        return value
    except (OSError, ValueError, AttributeError, KeyError) as exc:
        raise SecError("Device model missing or malformed", 3) from exc


def create(name):
    path = model_path(name)
    if path.exists():
        raise SecError("Device model already exists; no overwrite", 4)
    value = {
        "schema": 2,
        "name": name,
        "sources": [],
        "evidence": [],
        "created": datetime.now(timezone.utc).isoformat(),
    }
    write_json(path, value)
    save("recovery.device.create", "MUTATING", [], result="PASS", artifacts=[{"path": str(path)}])
    return value


def fact(model, field, value, state, source, location, reason):
    if state not in STATES or field not in FIELDS:
        raise ValueError("Invalid evidence contract")
    model["evidence"].append(
        {
            "field": field,
            "value": value,
            "state": state,
            "source": source,
            "location": location,
            "reason": reason,
        }
    )


def source_record(model, kind, path, digest, role=None):
    identifier = f"evidence-{len(model['sources']):04d}"
    model["sources"].append(
        {"id": identifier, "kind": kind, "path": str(path), "sha256": digest, "role": role}
    )
    return identifier


def fstab_facts(model, entries, source, location):
    from secripts.recovery.fstab import parse

    mounts = []
    for row in entries:
        fields = row.get("fields", [])
        if len(fields) < 3:
            continue
        structured = parse(fields, source, location)
        if structured:
            model.setdefault("fstab_evidence", []).append(structured)
        mount = (
            fields[0]
            if fields[1] in {"ext4", "f2fs", "vfat", "emmc", "auto", "squashfs", "erofs"}
            else fields[1]
        )
        mounts.append(mount)
        indicators = row.get("indicators", [])
        if "slotselect" in indicators:
            fact(model, "ab", True, "INFERRED", source, location, "fstab slotselect indicator")
        if "logical" in indicators:
            fact(
                model,
                "dynamic_partitions",
                True,
                "INFERRED",
                source,
                location,
                "fstab logical partition flag",
            )
        if "fileencryption" in indicators:
            fact(
                model,
                "encryption",
                "FBE",
                "INFERRED",
                source,
                location,
                "fstab fileencryption; decryption support untested",
            )
        if "metadata_encryption" in indicators:
            fact(
                model,
                "encryption",
                "METADATA_ENCRYPTION",
                "INFERRED",
                source,
                location,
                "fstab metadata encryption",
            )
    if mounts:
        fact(
            model,
            "fstab",
            mounts,
            "OBSERVED",
            source,
            location,
            "Parsed mount declarations, not live partitions",
        )
        if "/metadata" in mounts:
            fact(model, "metadata", True, "OBSERVED", source, location, "fstab mount declaration")
        if "/data" in mounts:
            fact(model, "userdata", True, "OBSERVED", source, location, "fstab mount declaration")


def add_image(name, role, path):
    if role not in ROLES:
        raise SecError("Unsupported evidence image role", 2)
    from secripts.images.engine import inspect

    image = inspect(Path(path))
    if image["structure_status"] == "FAIL":
        raise SecError("Malformed image cannot enter a device model", 3)
    model = load(name)
    src = source_record(model, "image", Path(path).resolve(), image["sha256"], role)
    if image.get("properties", {}).get("header_version") is not None:
        fact(
            model,
            "boot_header",
            image["properties"]["header_version"],
            "OBSERVED",
            src,
            "header",
            "Parsed header version; does not identify Android release",
        )
    if role == "recovery":
        fact(
            model,
            "recovery_arrangement",
            "dedicated",
            "USER_SUPPLIED",
            src,
            "image-role",
            "Operator labels stock image recovery; partition not independently proven",
        )
    fragments = image.get("properties", {}).get("fragments", [])
    if fragments:
        fact(
            model,
            "vendor_fragments",
            fragments,
            "OBSERVED",
            src,
            "vendor_ramdisk_table",
            "Bounded vendor fragment table",
        )
        if any(f["type"] == 2 for f in fragments):
            fact(
                model,
                "recovery_arrangement",
                "vendor_boot",
                "INFERRED",
                src,
                "vendor_ramdisk_table",
                "Recovery-type vendor fragment; device layout still requires review",
            )
    for key, section in image.get("sections", {}).items():
        rd = section.get("inspection", {})
        if rd.get("compression"):
            fact(
                model,
                "ramdisk_compression",
                rd["compression"],
                "OBSERVED",
                src,
                key,
                "Compression magic",
            )
        for table in rd.get("cpio", {}).get("fstabs", []):
            fstab_facts(model, table["entries"], src, key + "/" + table["path"])
        if key == "kernel" and section.get("size"):
            fact(
                model,
                "kernel",
                {"size": section["size"]},
                "OBSERVED",
                src,
                key,
                "Kernel region present; source/prebuilt requirements unresolved",
            )
        if key in ("dtb", "recovery_dtbo") and section.get("size"):
            fact(
                model,
                key if key == "dtb" else "dtbo",
                True,
                "OBSERVED",
                src,
                key,
                "Declared image section",
            )
    standalone = image.get("container", {}).get("inspection", {})
    for table in standalone.get("cpio", {}).get("fstabs", []):
        fstab_facts(model, table["entries"], src, "ramdisk/" + table["path"])
    if standalone.get("compression"):
        fact(
            model,
            "ramdisk_compression",
            standalone["compression"],
            "OBSERVED",
            src,
            "ramdisk",
            "Standalone compression recognition",
        )
    architecture = image.get("architecture")
    if isinstance(architecture, dict):
        fact(
            model,
            "architecture",
            architecture["value"],
            architecture["state"],
            src,
            "kernel",
            "Kernel architecture marker",
        )
    container = image.get("container", {})
    if container.get("architecture") not in (None, "UNKNOWN"):
        fact(
            model,
            "architecture",
            container["architecture"],
            "OBSERVED",
            src,
            "elf",
            "ELF e_machine",
        )
    if image.get("avb", {}).get("detected"):
        fact(
            model,
            "avb",
            True,
            "OBSERVED",
            src,
            "avb",
            "Metadata present; no cryptographic trust verified",
        )
    if role in ("dtb", "dtbo"):
        fact(
            model,
            role,
            True,
            "USER_SUPPLIED",
            src,
            "image-role",
            "Role supplied; inspect identification separately",
        )
    image_record = {
        "identification": image["identification"],
        "type": image["type"],
        "structure_status": image["structure_status"],
    }
    model["sources"][-1]["inspection"] = image_record
    from secripts.images.avbmodel import metadata

    descriptors = []
    if image.get("avb", {}).get("detected"):
        try:
            descriptors = metadata(Path(path))["descriptors"]
        except (ValueError, SecError):
            descriptors = []
    markers = []
    for section in image.get("sections", {}).values():
        markers.extend(
            m
            for m in section.get("inspection", {}).get("cpio", {}).get("markers", [])
            if m in {"recovery", "twrp", "init.recovery.*"}
        )
    model.setdefault("artifact_observations", []).append(
        {
            "role": role,
            "source": src,
            "sha256": image["sha256"],
            "bytes": image.get("size"),
            "header_version": image.get("properties", {}).get("header_version"),
            "kernel_bytes": image.get("sections", {}).get("kernel", {}).get("size"),
            "sections": [k for k, v in image.get("sections", {}).items() if v.get("size")],
            "recovery_markers": sorted(set(markers)),
            "recovery_fragment": any(f.get("type") == 2 for f in fragments),
            "avb_descriptors": descriptors,
            "structure_status": image["structure_status"],
            "cryptographic_state": "UNVERIFIED",
        }
    )
    write_json(model_path(name), model)
    save(
        "recovery.device.addimage",
        "MUTATING",
        [],
        result="PASS",
        file_sha256=image["sha256"],
        model=name,
        role=role,
        parser_version=image["parser_version"],
    )
    return summarize(model)


TREE_MAP = {
    "TARGET_ARCH": "architecture",
    "PRODUCT_DEVICE": "codename",
    "PRODUCT_MANUFACTURER": "manufacturer",
    "PRODUCT_SHIPPING_API_LEVEL": "android_generation",
    "AB_OTA_UPDATER": "ab",
    "PRODUCT_VIRTUAL_AB_OTA": "virtual_ab",
    "PRODUCT_USE_DYNAMIC_PARTITIONS": "dynamic_partitions",
    "BOARD_USES_METADATA_PARTITION": "metadata",
    "BOARD_AVB_ENABLE": "avb",
}


def add_tree(name, path):
    from secripts.recovery.inspection import audit_tree

    audit = audit_tree(Path(path))
    model = load(name)
    digest = (
        __import__("hashlib")
        .sha256(json.dumps(audit["configuration_hashes"], sort_keys=True).encode())
        .hexdigest()
    )
    src = source_record(model, "tree", Path(path).resolve(), digest)
    for row in audit["dependency_graph"]["declarations"]:
        key = row["name"]
        value = row.get("resolved_value") or row["value"]
        location = f"{row['file']}:{row['line']}"
        state = (
            "DECLARED"
            if row["state"] in ("DIRECTLY_DECLARED", "STATICALLY_RESOLVED")
            and not row["conditional"]
            else "UNKNOWN"
        )
        from secripts.recovery.flags import spec
        from secripts.secrets import contains_secret

        if spec(key) and not contains_secret(row["value"]):
            model.setdefault("configuration_evidence", []).append(
                {
                    "name": key,
                    "value": row["value"],
                    "resolved_value": value if state != "UNKNOWN" else None,
                    "state": state,
                    "source": src,
                    "location": location,
                    "conditional": row["conditional"],
                }
            )
        if state == "UNKNOWN":
            uncertain_field = TREE_MAP.get(key)
            if key in {
                "BOARD_USES_RECOVERY_AS_BOOT",
                "BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT",
                "BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT",
                "BOARD_RECOVERYIMAGE_PARTITION_SIZE",
            }:
                uncertain_field = "recovery_arrangement"
            if uncertain_field:
                fact(
                    model,
                    uncertain_field,
                    None,
                    "UNKNOWN",
                    src,
                    location,
                    "Conditional/external declaration may change this field; static evaluation unresolved",
                )
            continue
        if key in TREE_MAP:
            value = {"true": True, "false": False}.get(value, value)
            fact(
                model,
                TREE_MAP[key],
                value,
                state,
                src,
                location,
                "Static declaration; not device qualification",
            )
        arrangements = {
            "BOARD_USES_RECOVERY_AS_BOOT": "boot",
            "BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT": "vendor_boot",
            "BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT": "vendor_boot",
        }
        if key in arrangements and value == "true":
            fact(
                model,
                "recovery_arrangement",
                arrangements[key],
                state,
                src,
                location,
                "Explicit recovery arrangement declaration",
            )
        if key == "BOARD_RECOVERYIMAGE_PARTITION_SIZE" and value.isdigit() and int(value) > 0:
            fact(
                model,
                "recovery_arrangement",
                "dedicated",
                state,
                src,
                location,
                "Dedicated recovery size declaration",
            )
    for finding in audit["findings"]:
        if finding["check"] == "fstab declaration":
            e = finding["evidence"]
            fstab_facts(
                model,
                [{"fields": e.get("fields", e["first_fields"]), "indicators": e["indicators"]}],
                src,
                f"{e['file']}:{e['line']}",
            )
    fact(
        model,
        "dependencies",
        audit["dependency_graph"]["edges"],
        "DECLARED",
        src,
        "dependency_graph",
        "Partial graph; external dependencies not acquired",
    )
    write_json(model_path(name), model)
    save("recovery.device.addtree", "MUTATING", [], result="PASS", model=name, tree_sha256=digest)
    return summarize(model)


def add_metadata(name, path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > 65536:
        raise SecError("Metadata must be a small JSON file", 2)
    try:
        values = json.loads(path.read_text())
        if not isinstance(values, dict) or set(values) - set(FIELDS):
            raise ValueError()
        if any(not isinstance(v, (str, int, bool)) or len(str(v)) > 256 for v in values.values()):
            raise ValueError()
    except (ValueError, OSError) as exc:
        raise SecError("Unsupported user metadata shape", 2) from exc
    model = load(name)
    src = source_record(model, "user_metadata", path.resolve(), artifact_hash(path))
    for key, value in values.items():
        fact(
            model,
            key,
            value,
            "USER_SUPPLIED",
            src,
            key,
            "Operator assertion, not independently verified",
        )
    write_json(model_path(name), model)
    save("recovery.device.metadata", "MUTATING", [], result="PASS", model=name)
    return summarize(model)


def summarize(model):
    result = copy.deepcopy(model)
    fields = {}
    for field in FIELDS:
        evidence = [e for e in model["evidence"] if e["field"] == field]
        distinct = {json.dumps(e["value"], sort_keys=True) for e in evidence}
        fields[field] = {
            "state": "UNKNOWN"
            if not evidence
            else "CONFLICT"
            if len(distinct) > 1
            else evidence[0]["state"],
            "value": evidence[0]["value"] if len(distinct) == 1 else None,
            "evidence": evidence,
            "consensus": len(distinct) == 1 and len(evidence) > 1,
        }
    for field in (
        "recovery_arrangement",
        "boot_header",
        "ramdisk_compression",
        "vendor_fragments",
        "fstab",
        "dependencies",
        "encryption",
    ):
        values = fields[field]
        if values["state"] == "CONFLICT":
            values["state"] = "DERIVED"
            values["value"] = [entry["value"] for entry in values["evidence"]]
            values["combination"] = "MULTI_VALUED"
    fields["recovery_arrangement"]["deprecated"] = (
        "Compatibility projection only; use recovery_architecture independent features"
    )
    from secripts.recovery.architecture import compose

    result["recovery_architecture"] = compose(model)
    result["fields"] = fields
    result["conflicts"] = [k for k, v in fields.items() if v["state"] == "CONFLICT"]
    result["conflicts"].extend(
        "recovery_architecture." + name for name in result["recovery_architecture"]["conflicts"]
    )
    result["qualification"] = "UNTESTED"
    result["status"] = "CONFLICT" if result["conflicts"] else "PARTIAL"
    return result


def report(name):
    return summarize(load(name))


def catalog():
    root = data_dir() / "recovery/devices"
    return [
        p.stem for p in sorted(root.glob("*.json")) if re.fullmatch(r"[a-z][a-z0-9_]{0,63}", p.stem)
    ]
