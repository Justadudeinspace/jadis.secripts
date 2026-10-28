"""Content-first Image Intelligence. Heavy parsing only on explicit inspection."""

import copy
import json
from pathlib import Path
from secripts.images import PARSER_VERSION
from secripts.images.common import artifact_hash, DEFAULT_LIMITS
from secripts.images import compression, devicetree, containers, ramdisk
from secripts.safety import SecError
from secripts.context import data_dir
from secripts.receipts import write_json

FORMATS = (
    "ANDROID_BOOT",
    "VENDOR_BOOT",
    "AVB_METADATA",
    "FDT",
    "DTBO",
    "ELF",
    "UBOOT_LEGACY",
    "UBOOT_FIT",
    "MTK_LEGACY_HEADER",
    "ROCKCHIP_MARKER",
    "LOKI_MARKER",
    "CHROMEOS_MARKER",
    "RAMDISK",
    "COMPRESSION",
)


def inspect(path: Path, *, providers=False, cache=True):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise SecError("Image must be an existing regular non-symlink file", 3)
    original_stat = path.stat()
    digest = artifact_hash(path)
    cache_path = data_dir() / "cache/images" / PARSER_VERSION / f"{digest}.json"
    if cache and cache_path.is_file():
        try:
            result = json.loads(cache_path.read_text())
            if (
                not isinstance(result, dict)
                or result.get("parser_version") != PARSER_VERSION
                or result.get("sha256") != digest
            ):
                raise ValueError()
        except (OSError, ValueError):
            result = None
    else:
        result = None
    if result is None:
        result = _parse(path, digest)
        if cache:
            stored = copy.deepcopy(result)
            stored.pop("path", None)
            write_json(cache_path, stored)
    result = copy.deepcopy(result)
    references = {
        "ANDROID_BOOT": ["aosp"],
        "VENDOR_BOOT": ["aosp"],
        "AVB_METADATA": ["avb"],
        "FDT": ["dt-spec"],
        "DTBO": ["aosp-dtbo", "dt-spec"],
        "ELF": ["linux"],
        "UBOOT_LEGACY": ["uboot-header"],
        "UBOOT_FIT": ["uboot", "dt-spec"],
        "MTK_LEGACY_HEADER": ["aik-authors", "mkmtkhdr"],
        "LOKI_MARKER": ["loki"],
        "ROCKCHIP_MARKER": ["aik-authors"],
        "COMPRESSION": ["lz4"],
        "RAMDISK": ["cpio"],
    }
    result["identification"]["research_sources"] = references.get(result["type"], [])
    if result.get("properties", {}).get("header_version") is not None:
        result["identification"]["header_evidence"] = {
            "magic_offset": 0,
            "version_offset": 8 if result["type"] == "VENDOR_BOOT" else 40,
            "value": result["properties"]["header_version"],
            "state": "OBSERVED",
        }
    result["path"] = str(path.resolve())
    result["identification"]["extension_context"] = path.suffix
    if result.get("type") == "ANDROID_BOOT":
        props = result["properties"]
        markers = (
            result.get("sections", {})
            .get("ramdisk", {})
            .get("inspection", {})
            .get("cpio", {})
            .get("markers", [])
        )
        absent = props.get("kernel_size") == 0
        candidate = props.get("header_version") == 4 and absent and props.get("ramdisk_size", 0) > 0
        context = path.name.lower().startswith("init_boot") or "first_stage_ramdisk" in markers
        result["identification"]["role"] = {
            "value": "PROBABLE_INIT_BOOT"
            if candidate and context
            else "BOOT_WITHOUT_KERNEL"
            if absent
            else "BOOT_OR_RECOVERY",
            "state": "INFERRED" if candidate and context else "OBSERVED" if absent else "UNKNOWN",
            "reason": "Header/kernel/ramdisk plus weak filename or first-stage context; partition identity not proven",
        }
    if providers:
        from secripts.images.providers import evidence

        result["providers"] = evidence(path, result["type"])
        external = next(
            (
                p["command"]["stdout"].lower()
                for p in result["providers"]
                if p.get("provider") == "file" and p.get("status") == "PASS"
            ),
            None,
        )
        keywords = {
            "ANDROID_BOOT": ("android", "bootimg"),
            "VENDOR_BOOT": ("vendor", "boot"),
            "ELF": ("elf",),
            "FDT": ("device tree",),
            "UBOOT_FIT": ("device tree", "fit"),
            "COMPRESSION": ("compressed", "lz4", "gzip"),
            "RAMDISK": ("cpio", "compressed"),
        }
        expected = keywords.get(result["type"])
        result["identification"]["provider_agreement"] = (
            "AGREES"
            if external and expected and any(word in external for word in expected)
            else "DISAGREES"
            if external and expected
            else "UNKNOWN"
        )
    if (
        path.stat().st_size != original_stat.st_size
        or path.stat().st_mtime_ns != original_stat.st_mtime_ns
    ):
        raise SecError("Input changed during inspection; evidence discarded", 4)
    return result


def _parse(path, digest):
    size = path.stat().st_size
    with path.open("rb") as stream:
        data = stream.read(DEFAULT_LIMITS.read_bytes + 1)
    bounded = len(data) > DEFAULT_LIMITS.read_bytes
    data = data[: DEFAULT_LIMITS.read_bytes]
    result = {
        "schema": 3,
        "parser_version": PARSER_VERSION,
        "sha256": digest,
        "bytes": size,
        "type": "UNKNOWN",
        "confidence": "UNRESOLVED",
        "structure_status": "UNKNOWN",
        "identification": {
            "basis": "MAGIC_AND_STRUCTURE",
            "state": "UNKNOWN",
            "provider_agreement": "NOT_REQUESTED",
        },
        "warnings": [],
        "qualification": {"bootability": "UNTESTED", "device_compatibility": "UNTESTED"},
        "providers": [],
    }
    try:
        if data.startswith((b"ANDROID!", b"VNDRBOOT")):
            from secripts.images.android import inspect_image

            result.update(inspect_image(path))
            result.update(
                schema=3,
                parser_version=PARSER_VERSION,
                identification={
                    "basis": "ANDROID_MAGIC_AND_VALIDATED_BOUNDS",
                    "state": "OBSERVED",
                    "provider_agreement": "NOT_REQUESTED",
                },
                providers=[],
                qualification={"bootability": "UNTESTED", "device_compatibility": "UNTESTED"},
            )
            for name, section in result["sections"].items():
                if (
                    name in ("dtb", "recovery_dtbo")
                    and 0 < section["size"] <= DEFAULT_LIMITS.read_bytes
                ):
                    with path.open("rb") as stream:
                        stream.seek(section["offset"])
                        blob = stream.read(section["size"])
                    if blob.startswith(b"\xd0\x0d\xfe\xed"):
                        section["device_tree"] = devicetree.fdt(blob)
                if name == "bootconfig" and section["size"]:
                    section["content"] = "NOT_DUMPED: may include unique identifiers"
                    section["state"] = "OBSERVED"
            return result
        if bounded:
            result.update(
                structure_status="PARTIAL",
                warnings=["Non-Android input exceeds bounded parser window; hash only"],
            )
            return result
        details = None
        if data.startswith(b"\xd0\x0d\xfe\xed"):
            details = devicetree.fdt(data)
        elif data.startswith(b"\xd7\xb7\xab\x1e"):
            details = devicetree.dtbo(data)
        elif data.startswith(b"\x7fELF"):
            details = containers.elf(data)
        elif data.startswith(b"\x27\x05\x19\x56"):
            details = containers.uimage(data)
        else:
            details = containers.vendor(data)
            if details["format"] == "UNKNOWN":
                kind = compression.identify(data)
                if kind.startswith("lz4"):
                    details = compression.lz4(data)
                    details["format"] = "COMPRESSION"
                    from secripts.images.codecs import decode
                    from secripts.images.lz4codec import DictionaryRequired

                    try:
                        decoded, verification = decode(data)
                        details["native_verification"] = verification
                        details["decoded_bytes"] = len(decoded)
                    except DictionaryRequired:
                        details["native_verification"] = {"status": "BLOCKED_MISSING_DICTIONARY"}
                    except ValueError as exc:
                        details["native_verification"] = {
                            "status": "CHECKSUM_OR_DECODE_FAILED",
                            "reason": str(exc),
                        }
                elif kind != "UNKNOWN":
                    details = {
                        "format": "RAMDISK",
                        "compression": kind,
                        "structure_status": "PARTIAL",
                        "inspection": ramdisk.inspect_ramdisk(data, len(data)),
                    }
                    details["structure_status"] = details["inspection"]["status"]
                    if details["structure_status"] == "UNRESOLVED":
                        details["structure_status"] = "PARTIAL"
        from secripts.images.avb import inspect_avb

        avb = inspect_avb(path)
        result["avb"] = avb
        result.update(
            type="AVB_METADATA"
            if avb["detected"] and details["format"] == "UNKNOWN"
            else details["format"],
            structure_status="FAIL"
            if avb["status"] == "FAIL"
            else "PASS"
            if avb["status"] == "OBSERVED" and details["format"] == "UNKNOWN"
            else details["structure_status"],
            container=details,
        )
        result["identification"]["state"] = "OBSERVED" if result["type"] != "UNKNOWN" else "UNKNOWN"
    except (ValueError, OverflowError, IndexError, SecError) as exc:
        result.update(structure_status="FAIL", warnings=["Parser refusal: " + str(exc)])
    return result


def inspection_failed(value):
    details = value.get("container", {})
    if value.get("type") == "UBOOT_LEGACY" and (
        "FAIL" in (details.get("header_crc"), details.get("data_crc"))
    ):
        return True
    if any(
        h.get("state") == "HASH_MISMATCH"
        for image in (details.get("fit") or {}).get("images", [])
        for h in image["hashes"]
    ):
        return True
    return (
        value.get("structure_status") == "FAIL"
        or value.get("container", {}).get("native_verification", {}).get("status")
        == "CHECKSUM_OR_DECODE_FAILED"
    )
