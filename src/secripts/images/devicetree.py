"""Bounded FDT tokens, Android DT tables and FIT metadata. No DT compilation/evaluation."""

from secripts.images.common import Reader, DEFAULT_LIMITS


def fdt(data):
    r = Reader(data)
    (
        magic,
        total,
        off_struct,
        off_strings,
        off_reserve,
        version,
        compatible,
        cpu,
        string_size,
        struct_size,
    ) = r.unpack(">10I")
    if magic != 0xD00DFEED or total > len(data) or total < 40 or version < 17 or compatible > 17:
        raise ValueError("Unsupported/truncated FDT header")
    if off_struct % 4 or off_reserve % 8 or min(off_struct, off_strings, off_reserve) < 40:
        raise ValueError("Invalid FDT alignment/offset")
    ranges = [(off_struct, off_struct + struct_size), (off_strings, off_strings + string_size)]
    if any(end > total for _, end in ranges) or max(ranges[0][0], ranges[1][0]) < min(
        ranges[0][1], ranges[1][1]
    ):
        raise ValueError("FDT region bounds/overlap")
    reserve = off_reserve
    for _ in range(DEFAULT_LIMITS.nodes):
        address, size = r.unpack(">QQ", reserve)
        reserve += 16
        if reserve > total:
            raise ValueError("FDT reservation bounds")
        if not address and not size:
            break
    else:
        raise ValueError("FDT reservation count")
    if any(max(off_reserve, start) < min(reserve, end) for start, end in ranges):
        raise ValueError("FDT reservation overlap")
    strings = Reader(r.region(off_strings, string_size))
    tokens = Reader(r.region(off_struct, struct_size))
    cursor = 0
    stack = []
    nodes = []
    properties = []
    ended = False
    while cursor < len(tokens.data):
        opcode = tokens.unpack(">I", cursor)[0]
        cursor += 4
        if opcode == 1:
            name, used = tokens.string(cursor, len(tokens.data) - cursor)
            cursor = (cursor + used + 3) // 4 * 4
            if "/" in name:
                raise ValueError("Invalid FDT node name")
            if (not stack and (nodes or name)) or (stack and not name):
                raise ValueError("Invalid or repeated FDT root")
            stack.append(name)
            if len(stack) > DEFAULT_LIMITS.depth or len(nodes) >= DEFAULT_LIMITS.nodes:
                raise ValueError("FDT node/depth limit")
            nodes.append("/" + "/".join(stack[1:]))
        elif opcode == 2:
            if not stack:
                raise ValueError("Unbalanced FDT node")
            stack.pop()
        elif opcode == 3:
            if not stack:
                raise ValueError("FDT property outside node")
            length, offset = tokens.unpack(">II", cursor)
            cursor += 8
            value = tokens.region(cursor, length)
            cursor = (cursor + length + 3) // 4 * 4
            name, _ = strings.string(offset, len(strings.data) - offset)
            if len(properties) >= DEFAULT_LIMITS.properties:
                raise ValueError("FDT property count limit")
            entry = {"node": "/" + "/".join(stack[1:]), "name": name, "bytes": length}
            # Payloads/signatures/keys/serial properties are never dumped.
            if (
                name
                in {
                    "compatible",
                    "model",
                    "device_type",
                    "description",
                    "type",
                    "arch",
                    "os",
                    "compression",
                    "default",
                    "kernel",
                    "ramdisk",
                    "fdt",
                    "algo",
                }
                and length <= 4096
            ):
                entry["value"] = value.rstrip(b"\0").decode("utf-8", errors="replace").split("\0")
            elif name in {"load", "entry", "#address-cells", "#size-cells"} and length in (4, 8):
                entry["value"] = int.from_bytes(value, "big")
            properties.append(entry)
        elif opcode == 4:
            continue
        elif opcode == 9:
            if stack:
                raise ValueError("FDT ended inside node")
            ended = True
            break
        else:
            raise ValueError("Unknown FDT token")
    if not ended or not nodes or nodes[0] != "/":
        raise ValueError("FDT missing root/end")
    is_fit = "/images" in nodes and "/configurations" in nodes
    return {
        "format": "UBOOT_FIT" if is_fit else "FDT",
        "structure_status": "PASS",
        "version": version,
        "total_size": total,
        "boot_cpu": cpu,
        "node_count": len(nodes),
        "property_count": len(properties),
        "nodes": nodes[:256],
        "properties": properties[:512],
        "output_truncated": len(nodes) > 256 or len(properties) > 512,
        "signature_verification": "UNTESTED",
        "trailing_bytes": len(data) - total,
    }


def dtbo(data):
    r = Reader(data)
    magic, total, header, entry_size, count, offset, page, version = r.unpack(">8I")
    if (
        magic != 0xD7B7AB1E
        or total > len(data)
        or header < 32
        or entry_size < 32
        or count > 4096
        or version not in (0, 1)
    ):
        raise ValueError("Invalid DTBO header")
    if page < 512 or page & (page - 1) or offset < header or offset + count * entry_size > total:
        raise ValueError("Invalid DTBO table bounds")
    entries = []
    regions = []
    for index in range(count):
        size, start, identity, revision, *custom = r.unpack(">8I", offset + index * entry_size)
        if (
            start < offset + count * entry_size
            or start + size > total
            or any(start < end and start + size > begin for begin, end in regions)
        ):
            raise ValueError("DTBO payload overlap/bounds")
        regions.append((start, start + size))
        payload = r.region(start, size)
        details = (
            fdt(payload)
            if payload.startswith(b"\xd0\x0d\xfe\xed")
            else {"format": "UNKNOWN_OR_COMPRESSED", "structure_status": "PARTIAL"}
        )
        entries.append(
            {
                "index": index,
                "offset": start,
                "size": size,
                "id": identity,
                "revision": revision,
                "custom": custom,
                "device_tree": details,
            }
        )
    return {
        "format": "DTBO",
        "structure_status": "PASS"
        if all(e["device_tree"]["structure_status"] == "PASS" for e in entries)
        else "PARTIAL",
        "version": version,
        "page_size": page,
        "entries": entries,
        "total_size": total,
    }
