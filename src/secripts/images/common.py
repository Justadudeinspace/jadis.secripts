"""Shared hostile-input bounds and streaming hashes."""

import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Limits:
    read_bytes: int = 32 * 1024**2
    entries: int = 20000
    nodes: int = 4096
    properties: int = 16000
    string_bytes: int = 4096
    depth: int = 64


DEFAULT_LIMITS = Limits()


def artifact_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Reader:
    def __init__(self, data):
        self.data = data

    def region(self, offset, size):
        if offset < 0 or size < 0 or offset + size > len(self.data):
            raise ValueError("Declared region exceeds bounded input")
        return self.data[offset : offset + size]

    def unpack(self, fmt, offset=0):
        return struct.unpack(fmt, self.region(offset, struct.calcsize(fmt)))

    def string(self, offset, bound, limit=4096):
        raw = self.region(offset, min(bound, limit + 1))
        end = raw.find(b"\0")
        if end < 0:
            raise ValueError("Unterminated or excessive string")
        return raw[:end].decode("utf-8", errors="replace"), end + 1
