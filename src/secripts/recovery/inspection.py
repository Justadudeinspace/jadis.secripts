"""Static evidence only: never execute makefiles, scripts, or image payloads."""

import hashlib
import json
from pathlib import Path
import re
from secripts.safety import SecError


def artifact_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_image(path: Path) -> dict:
    from secripts.recovery.images import inspect_image as inspect

    return inspect(path)


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
            or path.suffix not in {".mk", ".fstab", ".sh", ".dependencies", ".json", ".xml"}
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
    from secripts.recovery.tree import graph

    dependency_graph = graph(root, files)
    return {
        "dependency_graph": dependency_graph,
        "tree": str(root),
        "files": sorted(files),
        "configuration_hashes": {name: artifact_hash(root / name) for name in sorted(files)},
        "variables": variables,
        "findings": findings,
        "result": "FAIL" if any(f["severity"] == "FAIL" for f in findings) else "REVIEW_REQUIRED",
        "execution": "Static parsing only; makefiles were not executed",
        "hardware": "UNTESTED",
    }
