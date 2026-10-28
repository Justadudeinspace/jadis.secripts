"""Compositional recovery facts and output relationships; no architecture enum or AI."""

import json

FLAG_FEATURES = {
    "BOARD_USES_RECOVERY_AS_BOOT": "recovery_in_boot",
    "BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT": "recovery_resources_in_vendor_boot",
    "BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT": "recovery_resources_in_vendor_boot",
    "BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE": "recovery_uses_boot_kernel",
    "BOARD_USES_GENERIC_KERNEL_IMAGE": "gki",
    "PRODUCT_BUILD_RECOVERY_IMAGE": "recovery_image_built",
    "AB_OTA_UPDATER": "a_b",
    "PRODUCT_VIRTUAL_AB_OTA": "virtual_a_b",
    "PRODUCT_USE_DYNAMIC_PARTITIONS": "dynamic_partitions",
    "BOARD_AVB_ENABLE": "avb_enabled",
}
FEATURES = tuple(
    sorted(
        set(FLAG_FEATURES.values())
        | {
            "dedicated_recovery_partition",
            "recovery_contains_kernel",
            "recovery_resources_in_init_boot",
            "boot_present",
            "init_boot_present",
            "vendor_boot_present",
            "recovery_present",
            "vbmeta_present",
            "boot_header_version",
            "vendor_boot_header_version",
            "init_boot_header_version",
            "recovery_header_version",
        }
    )
)
TARGETS = {
    "recovery.img": "recoveryimage",
    "boot.img": "bootimage",
    "vendor_boot.img": "vendorbootimage",
    "init_boot.img": "initbootimage",
    "dtbo.img": "dtboimage",
    "vbmeta.img": "vbmetaimage",
}


def boolean(value):
    if value is True or value == "true":
        return True
    if value is False or value == "" or value == "false":
        return False
    return None


def compose(record):
    collected = {name: [] for name in FEATURES}
    artifacts = list(record.get("artifact_observations", []))
    avb = []

    def add(name, value, state, evidence):
        if name in collected:
            collected[name].append({"value": value, "state": state, "evidence": evidence})

    for row in record.get("configuration_evidence", []):
        key = row["name"]
        value = row.get("resolved_value")
        state = row["state"]
        if key in FLAG_FEATURES:
            add(
                FLAG_FEATURES[key],
                boolean(value),
                state if boolean(value) is not None else "UNKNOWN",
                row,
            )
        if key == "BOARD_RECOVERYIMAGE_PARTITION_SIZE":
            try:
                value = int(str(value), 0) > 0
            except (ValueError, TypeError):
                value = None
            add(
                "dedicated_recovery_partition",
                value,
                state if value is not None else "UNKNOWN",
                row,
            )
        if key == "BOARD_BOOT_HEADER_VERSION":
            add("boot_header_version", value, state, row)
    # Schema-1 adapters preserve old evidence; compatible arrangements compose instead of conflict.
    for row in record.get("evidence", []):
        if row["field"] == "recovery_arrangement" and not record.get("configuration_evidence"):
            feature = (
                {
                    "dedicated": "dedicated_recovery_partition",
                    "boot": "recovery_in_boot",
                    "vendor_boot": "recovery_resources_in_vendor_boot",
                }.get(row["value"])
                if isinstance(row["value"], str)
                else None
            )
            if feature:
                add(feature, True, row["state"], row)
        field = {
            "ab": "a_b",
            "virtual_ab": "virtual_a_b",
            "dynamic_partitions": "dynamic_partitions",
            "avb": "avb_enabled",
        }.get(row["field"])
        if field:
            add(field, row["value"], row["state"], row)
    # Artifact role alone is not a partition, but its supplied dedicated label is retained as such.
    for row in record.get("evidence", []):
        if (
            row["field"] == "recovery_arrangement"
            and row["value"] == "dedicated"
            and row["state"] == "USER_SUPPLIED"
        ):
            add("dedicated_recovery_partition", True, "USER_SUPPLIED", row)
    for image in artifacts:
        role = image["role"]
        feature = (
            role + "_present"
            if role in {"boot", "init_boot", "vendor_boot", "recovery"}
            else "vbmeta_present"
            if role.startswith("vbmeta")
            else None
        )
        if feature:
            add(
                feature,
                True,
                "USER_SUPPLIED",
                {
                    "source": image["source"],
                    "reason": "Operator-supplied artifact role, not independent partition observation",
                },
            )
        if role + "_header_version" in collected and image.get("header_version") is not None:
            add(
                role + "_header_version",
                image["header_version"],
                "OBSERVED",
                {"source": image["source"], "sha256": image["sha256"]},
            )
        if role == "recovery" and image.get("kernel_bytes") is not None:
            add(
                "recovery_contains_kernel",
                image["kernel_bytes"] > 0,
                "OBSERVED",
                {
                    "source": image["source"],
                    "reason": "Parsed recovery-role image kernel section; role remains operator supplied",
                },
            )
        markers = image.get("recovery_markers", [])
        feature = {
            "boot": "recovery_in_boot",
            "vendor_boot": "recovery_resources_in_vendor_boot",
            "init_boot": "recovery_resources_in_init_boot",
        }.get(role)
        if feature and (markers or image.get("recovery_fragment")):
            add(
                feature,
                True,
                "INFERRED",
                {
                    "source": image["source"],
                    "markers": markers,
                    "recovery_fragment": image.get("recovery_fragment", False),
                },
            )
        for desc in image.get("avb_descriptors", []):
            if desc.get("partition"):
                avb.append(
                    {
                        "from": role + ".img",
                        "to": desc["partition"] + ".img",
                        "relation": "chained_from" if desc.get("kind") == "CHAIN" else "verifies",
                        "state": "OBSERVED",
                        "source": image["source"],
                        "descriptor": desc,
                        "cryptographic_state": "UNVERIFIED",
                        "device_trust": "UNVERIFIED",
                    }
                )
    fields = {}
    for name, rows in collected.items():
        distinct = {json.dumps(r["value"], sort_keys=True) for r in rows}
        fields[name] = {
            "value": rows[0]["value"] if len(distinct) == 1 else None,
            "state": "UNKNOWN"
            if not rows
            else "CONFLICT"
            if len(distinct) > 1
            else rows[0]["state"],
            "evidence": rows,
        }
    return {
        "schema": 2,
        "features": fields,
        "artifacts": artifacts,
        "avb_relationships": avb,
        "rollback_index_locations": [
            e["descriptor"]["rollback_location"]
            for e in avb
            if "rollback_location" in e["descriptor"]
        ],
        "conflicts": [k for k, v in fields.items() if v["state"] == "CONFLICT"],
        "hardware_qualification": "UNTESTED",
        "note": "Independent features; artifact presence, resource location, build outputs and device partitions are distinct",
    }


def graph(device, configuration=None):
    architecture = device.get("recovery_architecture") or compose(device)
    features = architecture["features"]
    nodes = {
        a["role"] + ".img": {
            "id": a["role"] + ".img",
            "kind": "artifact",
            "observed_sha256": a["sha256"],
            "role_state": "USER_SUPPLIED",
        }
        for a in architecture["artifacts"]
    }
    edges = list(architecture["avb_relationships"])
    outputs = []
    blockers = []

    def value(feature, flag=None):
        if configuration and flag and flag in configuration["flags"]:
            row = configuration["flags"][flag]
            if row["effective"]["value"] is not None or row.get("user_override") is not None:
                return row["effective"]["value"]
        return features[feature]["value"] if features[feature]["state"] != "CONFLICT" else None

    def output(artifact, reason, evidence):
        nodes.setdefault(artifact, {"id": artifact, "kind": "artifact"})
        outputs.append(
            {
                "artifact": artifact,
                "target": TARGETS[artifact],
                "reason": reason,
                "state": "DERIVED",
                "evidence": evidence,
                "flash_target": "NOT_INFERRED",
            }
        )

    dedicated = value("dedicated_recovery_partition")
    build_recovery = value("recovery_image_built", "PRODUCT_BUILD_RECOVERY_IMAGE")
    if dedicated is True and build_recovery is not False:
        output(
            "recovery.img",
            "Dedicated recovery declaration and no explicit disabled recovery output",
            features["dedicated_recovery_partition"]["evidence"],
        )
    if value("recovery_in_boot", "BOARD_USES_RECOVERY_AS_BOOT") is True:
        output(
            "boot.img",
            "Recovery resources declared/inferred in boot",
            features["recovery_in_boot"]["evidence"],
        )
    if (
        value("recovery_resources_in_vendor_boot", "BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT")
        is True
    ):
        output(
            "vendor_boot.img",
            "Recovery resources declared/inferred in vendor_boot",
            features["recovery_resources_in_vendor_boot"]["evidence"],
        )
    if value("recovery_resources_in_init_boot") is True:
        output(
            "init_boot.img",
            "Recovery-specific markers in init_boot role require source support review",
            features["recovery_resources_in_init_boot"]["evidence"],
        )
        blockers.append(
            "init_boot recovery output requires independently validated source target support"
        )
    if value("recovery_uses_boot_kernel", "BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE") is True:
        nodes.setdefault(
            "boot.img", {"id": "boot.img", "kind": "required_input", "state": "UNKNOWN"}
        )
        nodes.setdefault("recovery.img", {"id": "recovery.img", "kind": "artifact"})
        edges.append(
            {
                "from": "boot.img",
                "to": "recovery.img",
                "relation": "supplies_kernel_to",
                "state": "DERIVED",
                "evidence": features["recovery_uses_boot_kernel"]["evidence"],
            }
        )
    for image in architecture["artifacts"]:
        for section in image.get("sections", []):
            child = image["role"] + ".img/" + section
            nodes.setdefault(child, {"id": child, "kind": "section"})
            edges.append(
                {
                    "from": image["role"] + ".img",
                    "to": child,
                    "relation": "embeds",
                    "state": "OBSERVED",
                    "source": image["source"],
                }
            )
    for e in edges:
        for key in ("from", "to"):
            nodes.setdefault(
                e[key], {"id": e[key], "kind": "referenced_artifact", "state": "UNKNOWN"}
            )
    blockers.extend("Conflicting architecture feature: " + f for f in architecture["conflicts"])
    blockers.extend(
        "Conflicting model field: " + f
        for f in device.get("conflicts", [])
        if not f.startswith("recovery_architecture.")
    )
    if not outputs:
        blockers.append("No recovery output is justified by current evidence/configuration")
    return {
        "schema": 2,
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "edges": sorted(edges, key=lambda e: (e["from"], e["to"], e["relation"])),
        "outputs": outputs,
        "targets": [o["target"] for o in outputs],
        "status": "BLOCKED" if blockers else "REVIEW_REQUIRED",
        "blockers": blockers,
        "install_or_flash_plan": "NOT_PROVIDED",
        "hardware_qualification": "UNTESTED",
    }
