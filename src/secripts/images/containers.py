"""ELF, U-Boot legacy and narrowly recognized vendor wrappers; never execute/repack."""

import zlib
from secripts.images.common import Reader


def elf(data):
    r = Reader(data)
    ident = r.region(0, 16)
    if ident[:4] != b"\x7fELF" or ident[4] not in (1, 2) or ident[5] not in (1, 2) or ident[6] != 1:
        raise ValueError("Invalid ELF identification")
    endian = "<" if ident[5] == 1 else ">"
    bits = 32 if ident[4] == 1 else 64
    fields = r.unpack(endian + ("HHIIIIIHHHHHH" if bits == 32 else "HHIQQQIHHHHHH"), 16)
    (
        kind,
        machine,
        version,
        entry,
        phoff,
        shoff,
        flags,
        ehsize,
        phsize,
        phnum,
        shsize,
        shnum,
        shstr,
    ) = fields
    if version != 1 or ehsize != (52 if bits == 32 else 64) or phnum > 4096 or shnum > 4096:
        raise ValueError("Invalid ELF header/count")
    if (
        phnum
        and phsize < (32 if bits == 32 else 56)
        or shnum
        and shsize < (40 if bits == 32 else 64)
    ):
        raise ValueError("Invalid ELF table entry size")
    r.region(phoff, phsize * phnum)
    r.region(shoff, shsize * shnum)
    programs = []
    for index in range(phnum):
        values = r.unpack(endian + ("8I" if bits == 32 else "II6Q"), phoff + index * phsize)
        if bits == 32:
            ptype, offset, vaddr, paddr, filesz, memsz, pflags, align = values
        else:
            ptype, pflags, offset, vaddr, paddr, filesz, memsz, align = values
        r.region(offset, filesz)
        if ptype == 1 and filesz > memsz:
            raise ValueError("ELF load filesz exceeds memsz")
        programs.append(
            {
                "type": ptype,
                "offset": offset,
                "file_size": filesz,
                "memory_size": memsz,
                "flags": pflags,
                "alignment": align,
            }
        )
    for index in range(shnum):
        values = r.unpack(endian + ("10I" if bits == 32 else "II4QII2Q"), shoff + index * shsize)
        if values[1] != 8:
            r.region(values[4], values[5])
    return {
        "format": "ELF",
        "structure_status": "PASS",
        "bits": bits,
        "endianness": "little" if endian == "<" else "big",
        "machine": machine,
        "architecture": {3: "x86", 40: "arm", 62: "x86_64", 183: "arm64"}.get(machine, "UNKNOWN"),
        "entry": entry,
        "program_headers": programs,
        "section_count": shnum,
        "executable": "NEVER_RUN",
    }


def uimage(data):
    r = Reader(data)
    magic, hcrc, timestamp, size, load, entry, dcrc, os_id, arch, kind, comp, name = r.unpack(
        ">7I4B32s"
    )
    if magic != 0x27051956:
        raise ValueError("Invalid uImage magic")
    payload = r.region(64, size)
    header = bytearray(r.region(0, 64))
    header[4:8] = b"\0" * 4
    return {
        "format": "UBOOT_LEGACY",
        "structure_status": "PASS",
        "name": name.split(b"\0")[0].decode(errors="replace"),
        "timestamp": timestamp,
        "payload_size": size,
        "load": load,
        "entry": entry,
        "os_id": os_id,
        "architecture_id": arch,
        "image_type": kind,
        "compression_id": comp,
        "header_crc": "PASS" if zlib.crc32(header) == hcrc else "FAIL",
        "data_crc": "PASS" if zlib.crc32(payload) == dcrc else "FAIL",
        "signature_verification": "UNTESTED",
    }


def vendor(data):
    r = Reader(data)
    if data.startswith(b"\x88\x16\x88\x58"):
        length = r.unpack("<I", 4)[0]
        name = r.region(8, 32).split(b"\0")[0].decode(errors="replace")
        r.region(0, 512)
        r.region(512, length)
        return {
            "format": "MTK_LEGACY_HEADER",
            "structure_status": "PASS",
            "payload_offset": 512,
            "payload_size": length,
            "name": name,
            "state": "OBSERVED",
            "compatibility": "UNTESTED",
        }
    if data[0x400:0x404] == b"LOKI":
        return {
            "format": "LOKI_MARKER",
            "structure_status": "PARTIAL",
            "state": "INFERRED",
            "offset": 0x400,
        }
    if data.startswith((b"RKAF", b"RKFW")):
        return {
            "format": "ROCKCHIP_MARKER",
            "structure_status": "PARTIAL",
            "state": "INFERRED",
            "reason": "Magic recognition only",
        }
    if data.startswith(b"CHROMEOS"):
        return {
            "format": "CHROMEOS_MARKER",
            "structure_status": "PARTIAL",
            "state": "INFERRED",
            "reason": "Signing container not verified",
        }
    return {"format": "UNKNOWN", "structure_status": "UNKNOWN"}
