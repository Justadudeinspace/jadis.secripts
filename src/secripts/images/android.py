"""Bounded Android boot/vendor_boot structural parser. Image role is evidence, never compatibility."""

from pathlib import Path
import shutil
import struct
from secripts.safety import SecError
from secripts.images.ramdisk import inspect_ramdisk, compression, LIMIT
from secripts.images.avb import inspect_avb


def inspect_image(path: Path) -> dict:
    from secripts.images.common import artifact_hash

    if not path.is_file():
        raise SecError("Recovery image does not exist", 3)
    size = path.stat().st_size
    with path.open("rb") as stream:
        header = stream.read(4096)
    result = {
        "schema": 2,
        "path": str(path.resolve()),
        "bytes": size,
        "sha256": artifact_hash(path),
        "type": "UNKNOWN",
        "confidence": "UNRESOLVED",
        "properties": {},
        "sections": {},
        "architecture": "UNRESOLVED",
        "partition": "UNRESOLVED",
        "device_compatibility": "UNTESTED",
        "bootability": "UNTESTED",
        "warnings": [],
        "optional_tools": {name: shutil.which(name) for name in ("unpack_bootimg", "avbtool")},
    }

    def u32(offset):
        if offset + 4 > len(header):
            raise SecError("Truncated Android image header", 1)
        return struct.unpack_from("<I", header, offset)[0]

    def section(name, offset, length):
        if offset < 0 or length < 0 or offset + length > size:
            raise SecError(f"{name} payload extends beyond file", 1)
        if (
            name not in ("header",)
            and not name.startswith("fragment_")
            and length
            and offset
            % (
                4096
                if header[:8] == b"ANDROID!"
                and len(header) > 44
                and struct.unpack_from("<I", header, 40)[0] >= 3
                else 1
            )
        ):
            raise SecError("Misaligned image section", 1)
        result["sections"][name] = {"offset": offset, "size": length, "bounds": "PASS"}
        return result["sections"][name]

    def align(n, page):
        return (n + page - 1) // page * page

    inspection_budget = {"compressed": 0, "expanded": 0}

    def ramdisk(name, offset, length):
        info = section(name, offset, length)
        if (
            inspection_budget["compressed"] + min(length, LIMIT) > 2 * LIMIT
            or inspection_budget["expanded"] >= 2 * LIMIT
        ):
            info["inspection"] = {
                "status": "UNRESOLVED",
                "reason": "Aggregate ramdisk inspection budget exhausted",
            }
            return
        with path.open("rb") as stream:
            stream.seek(offset)
            data = stream.read(length if length <= LIMIT else 64)
        inspection_budget["compressed"] += len(data)
        info["inspection"] = inspect_ramdisk(
            data, length, output_limit=2 * LIMIT - inspection_budget["expanded"]
        )
        inspection_budget["expanded"] += info["inspection"].get(
            "decompressed_bytes", LIMIT if info["inspection"]["status"] == "FAIL" else 0
        )

    if header[:8] == b"ANDROID!":
        version = u32(40)
        if version not in (0, 1, 2, 3, 4):
            raise SecError("Unsupported boot header version", 5)
        minimum = {0: 1632, 1: 1648, 2: 1660, 3: 1580, 4: 1584}[version]
        if len(header) < minimum:
            raise SecError("Truncated Android boot header", 1)
        kernel = u32(8)
        rd = u32(12 if version >= 3 else 16)
        page = 4096 if version >= 3 else u32(36)
        if page < minimum or page > 65536 or page & (page - 1):
            raise SecError("Invalid boot image page size", 1)
        if version >= 3 and u32(20) != minimum or version in (1, 2) and u32(1644) != minimum:
            raise SecError("Invalid boot header size", 1)
        section("header", 0, minimum)
        section("kernel", page, kernel)
        rd_offset = page + align(kernel, page)
        ramdisk("ramdisk", rd_offset, rd)
        end = rd_offset + align(rd, page)
        if version < 3:
            second = u32(24)
            section("second", end, second)
            end += align(second, page)
            if version in (1, 2):
                dtbo = u32(1632)
                dtbo_offset = struct.unpack_from("<Q", header, 1636)[0]
                if dtbo:
                    if dtbo_offset < end:
                        raise SecError("Recovery DTBO overlaps preceding sections", 1)
                    section("recovery_dtbo", dtbo_offset, dtbo)
                    end = dtbo_offset + align(dtbo, page)
            if version == 2:
                section("dtb", end, u32(1648))
        elif version == 4:
            signature = u32(1580)
            if signature:
                section("boot_signature", end, signature)
        role = "INIT_BOOT_CANDIDATE" if version == 4 and kernel == 0 and rd else "BOOT_OR_RECOVERY"
        result.update(
            type="ANDROID_BOOT",
            confidence="OBSERVED",
            role={"value": role, "state": "INFERRED"},
            properties={
                "header_version": version,
                "page_size": page,
                "kernel_size": kernel,
                "ramdisk_size": rd,
            },
        )
        if kernel:
            with path.open("rb") as stream:
                stream.seek(page)
                magic = stream.read(min(kernel, 64))
            result["sections"]["kernel"]["compression"] = compression(magic)
            if len(magic) >= 60 and magic[56:60] == b"ARM\x64":
                result["architecture"] = {
                    "value": "arm64",
                    "state": "INFERRED",
                    "reason": "ARM64 Image magic",
                }
            elif len(magic) >= 40 and magic[36:40] == b"\x18\x28\x6f\x01":
                result["architecture"] = {
                    "value": "arm",
                    "state": "INFERRED",
                    "reason": "ARM zImage magic",
                }
        result["warnings"].append(
            "Boot versus recovery partition role cannot be proven by the shared header"
        )
    elif header[:8] == b"VNDRBOOT":
        version = u32(8)
        page = u32(12)
        if version not in (3, 4):
            raise SecError("Unsupported vendor_boot header version", 5)
        minimum = 2112 if version == 3 else 2128
        if len(header) < minimum:
            raise SecError("Truncated vendor_boot header", 1)
        if page < 512 or page > 65536 or page & (page - 1) or u32(2096) != minimum:
            raise SecError("Invalid vendor_boot header/page size", 1)
        rd = u32(24)
        offset = align(minimum, page)
        section("header", 0, minimum)
        ramdisk("vendor_ramdisk", offset, rd)
        dtb_offset = offset + align(rd, page)
        dtb = u32(2100)
        section("dtb", dtb_offset, dtb)
        extras = {}
        fragments = []
        if version == 4:
            table, entries, entry_size, bootconfig = struct.unpack_from("<IIII", header, 2112)
            table_offset = dtb_offset + align(dtb, page)
            section("vendor_ramdisk_table", table_offset, table)
            if entries > 4096 or entries and (entry_size < 108 or entries * entry_size > table):
                raise SecError("Invalid vendor ramdisk table bounds", 1)
            with path.open("rb") as stream:
                occupied = []
                for index in range(entries):
                    stream.seek(table_offset + index * entry_size)
                    entry = stream.read(108)
                    length, start, kind = struct.unpack_from("<III", entry)
                    if start + length > rd or any(
                        start < end and start + length > begin for begin, end in occupied
                    ):
                        raise SecError("Vendor ramdisk fragment bounds/overlap", 1)
                    occupied.append((start, start + length))
                    name = entry[12:44].split(b"\0")[0].decode("utf-8", errors="replace")
                    key = f"fragment_{index}"
                    ramdisk(key, offset + start, length)
                    fragments.append(
                        {
                            "index": index,
                            "name": name,
                            "type": kind,
                            "board_ids": list(struct.unpack_from("<16I", entry, 44)),
                            "offset": offset + start,
                            "size": length,
                        }
                    )
            bc_offset = table_offset + align(table, page)
            section("bootconfig", bc_offset, bootconfig)
            extras = {
                "ramdisk_table_size": table,
                "ramdisk_entries": entries,
                "bootconfig_size": bootconfig,
                "fragments": fragments,
            }
        result.update(
            type="VENDOR_BOOT",
            confidence="OBSERVED",
            properties={
                "header_version": version,
                "page_size": page,
                "ramdisk_size": rd,
                "dtb_size": dtb,
                **extras,
            },
        )
    else:
        result["warnings"].append("Unrecognized boot format; no structural or bootability claim")
    extents = [
        (s["offset"], s["offset"] + s["size"], name)
        for name, s in result["sections"].items()
        if s["size"] and not name.startswith("fragment_")
    ]
    for index, (start, end, _name) in enumerate(extents):
        if any(
            start < other_end and end > other_start for other_start, other_end, _ in extents[:index]
        ):
            raise SecError("Overlapping top-level image sections", 1)
    result["trailing_bytes"] = size - max((end for _, end, _ in extents), default=0)
    result["avb"] = inspect_avb(path)
    if result["avb"]["detected"] and result["type"] == "UNKNOWN":
        result["type"] = "AVB_METADATA"
    inspection_states = [s.get("inspection", {}).get("status") for s in result["sections"].values()]
    result["structure_status"] = (
        "FAIL"
        if "FAIL" in inspection_states or result["avb"]["status"] == "FAIL"
        else "PARTIAL"
        if "UNRESOLVED" in inspection_states
        else "PASS"
        if result["sections"]
        else "UNKNOWN"
    )
    result["warnings"].append(
        "Structure and metadata are not signature verification or device compatibility"
    )
    return result
