"""Static dependency graph: literal and LOCAL_DIR references only, never Make evaluation."""

from pathlib import Path
import re
import xml.etree.ElementTree as ET

GROUPS = {
    "architecture": ("TARGET_ARCH", "TARGET_2ND_ARCH"),
    "products": (
        "PRODUCT_NAME",
        "PRODUCT_DEVICE",
        "PRODUCT_MODEL",
        "PRODUCT_MAKEFILES",
        "COMMON_LUNCH_CHOICES",
    ),
    "slots": (
        "AB_OTA_UPDATER",
        "AB_OTA_PARTITIONS",
        "PRODUCT_VIRTUAL_AB_OTA",
        "PRODUCT_VIRTUAL_AB_COMPRESSION",
    ),
    "dynamic_partitions": (
        "PRODUCT_USE_DYNAMIC_PARTITIONS",
        "BOARD_SUPER_PARTITION_SIZE",
        "BOARD_SUPER_PARTITION_GROUPS",
    ),
    "recovery_arrangement": (
        "BOARD_USES_RECOVERY_AS_BOOT",
        "BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT",
        "BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT",
        "BOARD_BOOT_HEADER_VERSION",
        "BOARD_RECOVERYIMAGE_PARTITION_SIZE",
        "BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE",
        "BOARD_BOOTIMAGE_PARTITION_SIZE",
    ),
    "kernel_dtb": (
        "TARGET_KERNEL_SOURCE",
        "TARGET_PREBUILT_KERNEL",
        "BOARD_PREBUILT_DTBIMAGE_DIR",
        "BOARD_PREBUILT_DTBOIMAGE",
        "BOARD_INCLUDE_DTB_IN_BOOTIMG",
    ),
    "encryption": (
        "TW_INCLUDE_CRYPTO",
        "TW_INCLUDE_CRYPTO_FBE",
        "TW_INCLUDE_FBE_METADATA_DECRYPT",
        "BOARD_USES_METADATA_PARTITION",
    ),
    "avb": (
        "BOARD_AVB_ENABLE",
        "BOARD_AVB_ALGORITHM",
        "BOARD_AVB_ROLLBACK_INDEX",
        "BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS",
    ),
}


def graph(root: Path, files: dict) -> dict:
    nodes = set(files)
    edges = []
    declarations = []
    warnings = []

    def edge(source, reference, kind):
        target = None
        state = "UNRESOLVED"
        reason = "Make expansion or external dependency not evaluated"
        expanded = reference.replace("$(LOCAL_DIR)", str((root / source).parent)).replace(
            "${LOCAL_DIR}", str((root / source).parent)
        )
        if "$" not in expanded and not any(c in expanded for c in "*?"):
            path = Path(expanded)
            if path.is_absolute():
                candidate = path
            else:
                candidate = root / path
                # Android source-root paths are external, not relative to a device directory.
            if candidate.is_relative_to(root) and not candidate.is_symlink():
                relative = str(candidate.relative_to(root))
                if ".." not in candidate.relative_to(root).parts and relative in files:
                    target = relative
                    state = "STATICALLY_RESOLVED"
                    reason = "Local bounded file inventory"
                else:
                    state = (
                        "EXTERNALLY_DEPENDENT"
                        if reference.startswith(("device/", "vendor/", "kernel/", "build/"))
                        else "UNRESOLVED"
                    )
                    reason = "Referenced local file absent or outside supported inventory"
            else:
                state = "EXTERNALLY_DEPENDENT"
                reason = "Reference outside audit boundary; not followed"
        edges.append(
            {
                "source": source,
                "reference": reference,
                "target": target,
                "kind": kind,
                "state": state,
                "reason": reason,
            }
        )

    for filename, text in sorted(files.items()):
        conditional = bool(re.search(r"(?m)^\s*(?:ifeq|ifneq|ifdef|ifndef)\b", text))
        for number, line in enumerate(text.splitlines(), 1):
            match = re.match(r"\s*([A-Z][A-Z0-9_]+)\s*([:+?]?=)\s*([^#]*)", line)
            if match:
                key, operator, value = match.groups()
                declarations.append(
                    {
                        "name": key,
                        "value": value.strip(),
                        "operator": operator,
                        "file": filename,
                        "line": number,
                        "state": "UNRESOLVED"
                        if conditional or "$" in value
                        else "DIRECTLY_DECLARED",
                        "conditional": conditional,
                    }
                )
                if key in {
                    "TARGET_KERNEL_SOURCE",
                    "TARGET_PREBUILT_KERNEL",
                    "BOARD_PREBUILT_DTBOIMAGE",
                    "BOARD_PREBUILT_DTBIMAGE_DIR",
                    "TARGET_RECOVERY_FSTAB",
                }:
                    edge(filename, value.strip(), "configuration_reference")
                if key == "PRODUCT_MAKEFILES":
                    for reference in value.split():
                        edge(filename, reference, "product")
            clean = line.split("#", 1)[0].strip()
            # Do not attempt arbitrary call/function evaluation. LOCAL_DIR is the only supported expansion.
            match = re.match(r"(?:-?include)\s+(.+)", clean)
            inherited = re.search(
                r"\$\(call\s+inherit-product(?:-if-exists)?\s*,\s*(.+)\)\s*$", clean
            )
            if match:
                for reference in match.group(1).split():
                    edge(filename, reference, "include")
            elif inherited:
                edge(filename, inherited.group(1).strip(), "inherit-product")
        if filename.endswith(".xml"):
            # Reject DTD/entity input; standard parser does not access network, and the size is bounded.
            if "<!DOCTYPE" in text or "<!ENTITY" in text or "\x00" in text:
                warnings.append({"file": filename, "reason": "DTD/entities refused"})
                continue
            try:
                manifest = ET.fromstring(text)  # noqa: S314 -- bounded UTF-8 text; DTD/entities/NUL refused above
            except ET.ParseError:
                warnings.append({"file": filename, "reason": "Malformed XML manifest"})
            else:
                for project in manifest.findall(".//project")[:1000]:
                    edges.append(
                        {
                            "source": filename,
                            "reference": project.get("path") or project.get("name"),
                            "revision": project.get("revision"),
                            "kind": "manifest",
                            "target": None,
                            "state": "EXTERNALLY_DEPENDENT",
                        }
                    )
    # Iterative DFS: graph cycles are evidence, not evaluated or recursively expanded.
    adjacency = {name: [] for name in nodes}
    for item in edges:
        if item["target"]:
            adjacency[item["source"]].append(item["target"])
    cycles = []
    visited = set()
    for start in sorted(nodes):
        stack = [(start, [])]
        budget = 0
        while stack and budget < 20000:
            node, trail = stack.pop()
            budget += 1
            if node in trail:
                cycles.append(trail[trail.index(node) :] + [node])
                continue
            if node in visited:
                continue
            visited.add(node)
            stack.extend((child, trail + [node]) for child in adjacency.get(node, []))
    groups = {name: [d for d in declarations if d["name"] in keys] for name, keys in GROUPS.items()}
    return {
        "nodes": sorted(nodes),
        "edges": edges,
        "cycles": cycles,
        "declarations": declarations,
        "groups": groups,
        "warnings": warnings,
        "complete": False,
        "state": "STATICALLY_INFERRED",
        "limits": "Bounded local inventory; no conditional evaluation, arbitrary Make expansion or external traversal",
    }
