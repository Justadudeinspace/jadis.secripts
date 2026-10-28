"""Static evidence only: never execute makefiles, scripts, or image payloads."""

import hashlib
import json
from pathlib import Path
import re
import struct
from secripts.safety import SecError


def artifact_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_image(path: Path) -> dict:
    if not path.is_file():
        raise SecError("Recovery image does not exist", 3)
    size = path.stat().st_size
    with path.open("rb") as stream:
        header = stream.read(4096)
    result = {
        "path": str(path.resolve()),
        "bytes": size,
        "sha256": artifact_hash(path),
        "type": "UNKNOWN",
        "confidence": "UNRESOLVED",
        "properties": {},
        "architecture": "UNRESOLVED",
        "partition": "UNRESOLVED",
        "device_compatibility": "UNTESTED",
        "warnings": [],
    }
    if header[:8] == b"ANDROID!":
        if len(header) < 48:
            raise SecError("Truncated Android boot header", 1)
        version = struct.unpack_from("<I", header, 40)[0]
        if version > 4:
            result["warnings"].append("Unsupported boot header version")
            return result
        minimum = {0: 1632, 1: 1648, 2: 1660, 3: 1580, 4: 1584}[version]
        if size < minimum:
            raise SecError("Truncated Android boot image", 1)
        kernel_size = struct.unpack_from("<I", header, 8)[0]
        ramdisk_size = struct.unpack_from("<I", header, 12 if version >= 3 else 16)[0]
        page_size = 4096 if version >= 3 else struct.unpack_from("<I", header, 36)[0]
        if page_size < minimum or page_size > 65536 or page_size & (page_size - 1):
            raise SecError("Invalid boot image page size", 1)

        def align(n):
            return ((n + page_size - 1) // page_size) * page_size

        if page_size + align(kernel_size) + ramdisk_size > size:
            raise SecError("Boot image payload extends beyond file", 1)
        result.update(
            type="ANDROID_BOOT",
            confidence="VERIFIED",
            properties={
                "header_version": version,
                "kernel_size": kernel_size,
                "ramdisk_size": ramdisk_size,
                "page_size": page_size,
            },
        )
        result["warnings"].append(
            "Header recognized; AVB, ramdisk contents and target compatibility unresolved"
        )
    elif header[:8] == b"VNDRBOOT":
        if len(header) < 2112:
            raise SecError("Truncated vendor_boot header", 1)
        version, page = struct.unpack_from("<II", header, 8)
        if version not in (3, 4):
            raise SecError("Unsupported vendor_boot header version", 5)
        minimum = 2112 if version == 3 else 2128
        if len(header) < minimum:
            raise SecError("Truncated vendor_boot header", 1)
        ramdisk = struct.unpack_from("<I", header, 24)[0]
        header_size, dtb = struct.unpack_from("<II", header, 2096)
        if page < 512 or page > 65536 or page & (page - 1) or header_size != minimum:
            raise SecError("Invalid vendor_boot page/header size", 1)

        def aligned(n):
            return ((n + page - 1) // page) * page

        required = aligned(header_size) + aligned(ramdisk) + aligned(dtb)
        extra = {}
        if version == 4:
            table, entries, entry_size, bootconfig = struct.unpack_from("<IIII", header, 2112)
            if entries and (entry_size < 108 or entries * entry_size > table):
                raise SecError("Invalid vendor ramdisk table bounds", 1)
            required += aligned(table) + aligned(bootconfig)
            extra = {
                "ramdisk_table_size": table,
                "ramdisk_entries": entries,
                "bootconfig_size": bootconfig,
            }
        if required > size:
            raise SecError("Vendor boot payload extends beyond file", 1)
        result.update(
            type="VENDOR_BOOT",
            confidence="VERIFIED",
            properties={
                "header_version": version,
                "page_size": page,
                "ramdisk_size": ramdisk,
                "dtb_size": dtb,
                **extra,
            },
        )
        result["warnings"].append(
            "Magic/header only; vendor ramdisk table and target relationship unresolved"
        )
    else:
        result["warnings"].append("Unrecognized image; no bootability claim")
    return result


def audit_tree(root: Path) -> dict:
    if not root.is_dir():
        raise SecError("Device tree directory does not exist", 3)
    root = root.resolve()
    findings, files, variables = [], {}, {}

    def finding(severity, check, evidence):
        findings.append({"severity": severity, "check": check, "evidence": evidence})

    for index, path in enumerate(root.rglob("*")):
        if index >= 10000:
            raise SecError("Tree exceeds audit limit", 4)
        if path.is_symlink():
            finding("UNRESOLVED", "symlink", str(path.relative_to(root)))
            continue
        if (
            not path.is_file()
            or path.suffix not in {".mk", ".fstab", ".sh", ".dependencies", ".json"}
            and path.name not in {"recovery.fstab", "dependencies"}
        ):
            continue
        if path.stat().st_size > 1024 * 1024:
            finding("WARN", "oversize file", str(path.relative_to(root)))
            continue
        text = path.read_text(errors="replace").replace("\\\n", " ")
        files[str(path.relative_to(root))] = text
        for key, value in re.findall(r"(?m)^\s*([A-Z][A-Z0-9_]+)\s*:?=\s*([^\n#]+)", text):
            variables[key] = value.strip()
    for name in ("BoardConfig.mk", "AndroidProducts.mk"):
        matches = [p for p in files if Path(p).name == name]
        finding(
            "INFO" if matches else "WARN", name, matches or "Not found; alternate layout may apply"
        )
    arch = variables.get("TARGET_ARCH")
    finding("INFO" if arch else "UNRESOLVED", "architecture", arch or "TARGET_ARCH not resolved")
    products = [p for p in files if re.search(r"(?:twrp|device|omni).*\.mk$", p)]
    finding(
        "INFO" if products else "WARN",
        "product definitions",
        products or "No conventional product makefile",
    )
    fstabs = [p for p in files if "fstab" in p]
    finding(
        "INFO" if fstabs else "WARN",
        "recovery fstab",
        fstabs or "No fstab found; could be external",
    )
    groups = {
        "slots": ("AB_OTA_UPDATER", "AB_OTA_PARTITIONS"),
        "dynamic partitions": ("PRODUCT_USE_DYNAMIC_PARTITIONS", "BOARD_SUPER_PARTITION_SIZE"),
        "recovery arrangement": (
            "BOARD_USES_RECOVERY_AS_BOOT",
            "BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT",
            "BOARD_BOOT_HEADER_VERSION",
            "BOARD_RECOVERYIMAGE_PARTITION_SIZE",
        ),
        "decryption": ("TW_INCLUDE_CRYPTO", "TW_INCLUDE_CRYPTO_FBE"),
        "kernel": ("TARGET_PREBUILT_KERNEL", "TARGET_KERNEL_SOURCE", "BOARD_PREBUILT_DTBIMAGE_DIR"),
    }
    for name, keys in groups.items():
        declarations = {k: variables[k] for k in keys if k in variables}
        finding(
            "INFO" if declarations else "UNRESOLVED", name, declarations or "Not declared locally"
        )
    for filename, text in files.items():
        if "fstab" in filename:
            for number, line in enumerate(text.splitlines(), 1):
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
                fields = line.split()
                if len(fields) < 3:
                    finding("WARN", "malformed fstab entry", {"file": filename, "line": number})
                else:
                    flags = [
                        flag
                        for flag in (
                            "logical",
                            "slotselect",
                            "fileencryption",
                            "metadata_encryption",
                            "encryptable",
                        )
                        if flag in line
                    ]
                    finding(
                        "INFO",
                        "fstab declaration",
                        {
                            "file": filename,
                            "line": number,
                            "first_fields": fields[:3],
                            "indicators": flags,
                        },
                    )
        if "dependenc" in filename:
            try:
                dependencies = json.loads(text)
            except ValueError:
                finding("UNRESOLVED", "dependency format", filename)
            else:
                if not isinstance(dependencies, list):
                    finding("WARN", "dependency format", "Expected list of dependency objects")
                else:
                    for dependency in dependencies:
                        if not isinstance(dependency, dict):
                            finding("WARN", "dependency entry", filename)
                            continue
                        finding(
                            "UNRESOLVED",
                            "external dependency",
                            {k: dependency.get(k) for k in ("repository", "target_path", "branch")},
                        )
        if re.search(r"(?m)^\s*(?:ifeq|ifneq|ifdef|ifndef)\b", text):
            finding("UNRESOLVED", "conditional make declarations", filename)
        for reference in re.findall(
            r"(?:include|inherit-product(?:-if-exists)?[, ]+)\s*([^\s)]+\.mk)", text
        ):
            finding(
                "UNRESOLVED",
                "make dependency",
                {
                    "file": filename,
                    "reference": reference,
                    "reason": "Make expansion and external source tree are not evaluated",
                },
            )
        for reference in re.findall(
            r"(?:TARGET_PREBUILT_KERNEL|TARGET_RECOVERY_FSTAB)\s*:?=\s*([^\s#]+)", text
        ):
            if "$" in reference:
                finding("UNRESOLVED", "expanded reference", reference)
            elif Path(reference).is_absolute() or ".." in Path(reference).parts:
                finding("WARN", "nonportable reference", reference)
            elif not Path(reference).is_absolute() and not (root / reference).is_file():
                finding("WARN", "missing local reference", reference)
    if not files:
        finding("FAIL", "tree contents", "No supported recovery configuration files")
    return {
        "tree": str(root),
        "files": sorted(files),
        "configuration_hashes": {name: artifact_hash(root / name) for name in sorted(files)},
        "variables": variables,
        "findings": findings,
        "result": "FAIL" if any(f["severity"] == "FAIL" for f in findings) else "REVIEW_REQUIRED",
        "execution": "Static parsing only; makefiles were not executed",
        "hardware": "UNTESTED",
    }
