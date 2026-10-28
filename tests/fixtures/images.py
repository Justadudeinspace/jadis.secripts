"""Minimal independently generated binary fixtures."""

import struct
import zlib


def fdt(fit=False):
    strings = b"compatible\0arch\0type\0default\0"
    tokens = bytearray()

    def begin(name):
        tokens.extend(struct.pack(">I", 1) + name.encode() + b"\0")
        tokens.extend(b"\0" * (-len(tokens) % 4))

    def prop(name, value):
        tokens.extend(
            struct.pack(">III", 3, len(value), strings.index(name.encode() + b"\0")) + value
        )
        tokens.extend(b"\0" * (-len(tokens) % 4))

    def end():
        tokens.extend(struct.pack(">I", 2))

    begin("")
    prop("compatible", b"fixture,device\0")
    if fit:
        begin("images")
        begin("kernel")
        prop("arch", b"arm64\0")
        prop("type", b"kernel\0")
        end()
        end()
        begin("configurations")
        prop("default", b"conf\0")
        begin("conf")
        end()
        end()
    end()
    tokens.extend(struct.pack(">I", 9))
    offset = 56
    strings_offset = offset + len(tokens)
    total = strings_offset + len(strings)
    return (
        struct.pack(
            ">10I",
            0xD00DFEED,
            total,
            offset,
            strings_offset,
            40,
            17,
            16,
            0,
            len(strings),
            len(tokens),
        )
        + bytes(16)
        + tokens
        + strings
    )


def dtbo():
    tree = fdt()
    header = struct.pack(">8I", 0xD7B7AB1E, 64 + len(tree), 32, 32, 1, 32, 2048, 0)
    return header + struct.pack(">8I", len(tree), 64, 7, 1, 0, 0, 0, 0) + tree


def elf(bits=64, big=False):
    endian = ">" if big else "<"
    ident = b"\x7fELF" + bytes([2 if bits == 64 else 1, 2 if big else 1, 1]) + bytes(9)
    values = (
        2,
        183 if bits == 64 else 40,
        1,
        0,
        0,
        0,
        0,
        64 if bits == 64 else 52,
        56 if bits == 64 else 32,
        0,
        64 if bits == 64 else 40,
        0,
        0,
    )
    return ident + struct.pack(
        endian + ("HHIQQQIHHHHHH" if bits == 64 else "HHIIIIIHHHHHH"), *values
    )


def uimage():
    payload = b"synthetic payload"
    header = bytearray(
        struct.pack(
            ">7I4B32s",
            0x27051956,
            0,
            0,
            len(payload),
            0x8000,
            0x8000,
            zlib.crc32(payload),
            5,
            2,
            2,
            0,
            b"fixture",
        )
    )
    struct.pack_into(">I", header, 4, zlib.crc32(header))
    return bytes(header) + payload


def lz4():
    return (
        b"\x04\x22\x4d\x18"
        + bytes([0x60, 0x40, 0])
        + struct.pack("<I", 0x80000003)
        + b"abc"
        + bytes(4)
    )


def boot(version):
    page = 4096 if version >= 3 else 2048
    header = bytearray(page)
    header[:8] = b"ANDROID!"
    struct.pack_into("<I", header, 40, version)
    if version >= 3:
        struct.pack_into("<I", header, 20, 1584 if version == 4 else 1580)
    else:
        struct.pack_into("<I", header, 36, page)
        if version in (1, 2):
            struct.pack_into("<I", header, 1644, 1648 if version == 1 else 1660)
    return bytes(header)
