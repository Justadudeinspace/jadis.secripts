"""Versioned, bounded comparison evidence; equivalence never implies qualification."""

from dataclasses import asdict, dataclass
from enum import StrEnum
from secripts.images.artifacts import digest


class DifferenceClass(StrEnum):
    BYTE = "BYTE"
    STRUCTURE = "STRUCTURE"
    CONTENT = "CONTENT"
    METADATA = "METADATA"
    ORDER = "ORDER"
    ALIGNMENT = "ALIGNMENT"
    COMPRESSION = "COMPRESSION"
    SIGNATURE = "SIGNATURE"
    CHECKSUM = "CHECKSUM"
    PADDING = "PADDING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Difference:
    location: str
    classification: DifferenceClass
    before: object
    after: object
    interpretation: str
    expected: bool = False
    compatibility_affecting: bool = True
    severity: str = "WARN"


class Comparison:
    def __init__(self, first, second):
        self.value = {
            "schema": 1,
            "original_sha256": digest(first),
            "rebuilt_sha256": digest(second),
            "byte_identity": "BYTE_IDENTICAL" if first == second else "DIFFERENT",
            "structural_equivalence": "UNVERIFIED",
            "semantic_equivalence": "UNVERIFIED",
            "component_equivalence": "UNVERIFIED",
            "metadata_equivalence": "UNVERIFIED",
            "cryptographic_state": "UNVERIFIED",
            "device_compatibility": "UNTESTED",
            "bootability": "UNTESTED",
            "hardware_qualification": "UNTESTED",
            "differences": [],
            "difference_count": 0,
            "differences_truncated": False,
            "unresolved": [],
        }

    def add(self, location, classification, before, after, interpretation, **kwargs):
        self.value["difference_count"] += 1
        if len(self.value["differences"]) < 512:
            self.value["differences"].append(
                asdict(
                    Difference(
                        location,
                        DifferenceClass(classification),
                        before,
                        after,
                        interpretation,
                        **kwargs,
                    )
                )
            )
        else:
            self.value["differences_truncated"] = True

    def finish(self):
        self.value["result"] = (
            "BYTE_IDENTICAL"
            if self.value["byte_identity"] == "BYTE_IDENTICAL"
            else (
                "SEMANTICALLY_EQUIVALENT"
                if self.value["semantic_equivalence"] == "SEMANTICALLY_EQUIVALENT"
                else "DIFFERENT"
                if self.value["semantic_equivalence"] == "DIFFERENT"
                else "UNVERIFIED"
            )
        )
        return self.value


def ramdisks(first, second):
    from secripts.images.ramdisk_model import parse

    left, right = parse(first), parse(second)
    result = Comparison(first, second)

    def keyed(model):
        counts = {}
        values = {}
        for entry in model["entries"]:
            name = entry["path"]
            occurrence = counts.get(name, 0)
            counts[name] = occurrence + 1
            values[(name, occurrence)] = entry
        return values

    a, b = keyed(left), keyed(right)
    content = metadata = True
    for key in sorted(set(a) | set(b)):
        location = f"{key[0]}#{key[1]}"
        x, y = a.get(key), b.get(key)
        if x is None or y is None:
            result.add(
                location,
                "CONTENT",
                None if x is None else x["sha256"],
                None if y is None else y["sha256"],
                "ADDED" if x is None else "REMOVED",
            )
            content = False
            metadata = False
            continue
        if x["sha256"] != y["sha256"]:
            result.add(
                location,
                "CONTENT",
                x["sha256"],
                y["sha256"],
                "SYMLINK_CHANGED" if x["type"] == "symlink" else "CONTENT_CHANGED",
            )
            content = False
        for fields, label in [
            (("mode",), "MODE_CHANGED"),
            (("uid", "gid"), "OWNER_CHANGED"),
            (
                (
                    "ino",
                    "nlink",
                    "mtime",
                    "devmajor",
                    "devminor",
                    "rdevmajor",
                    "rdevminor",
                    "type",
                    "archive",
                ),
                "METADATA_CHANGED",
            ),
        ]:
            before = {f: x[f] for f in fields}
            after = {f: y[f] for f in fields}
            if before != after:
                result.add(location, "METADATA", before, after, label)
                metadata = False
    if list(a) != list(b):
        result.add("entries", "ORDER", list(a)[:64], list(b)[:64], "ORDER_CHANGED")
        metadata = False
    if left["compression"]["codec"] != right["compression"]["codec"]:
        result.add(
            "encoding",
            "COMPRESSION",
            left["compression"]["codec"],
            right["compression"]["codec"],
            "COMPRESSION_CHANGED",
            expected=True,
        )
    result.value.update(
        structural_equivalence="STRUCTURALLY_EQUIVALENT" if list(a) == list(b) else "DIFFERENT",
        component_equivalence="CONTENT_EQUIVALENT" if content else "DIFFERENT",
        metadata_equivalence="SEMANTICALLY_EQUIVALENT" if metadata else "DIFFERENT",
        semantic_equivalence="SEMANTICALLY_EQUIVALENT" if content and metadata else "DIFFERENT",
    )
    if first != second and not result.value["difference_count"]:
        result.add(
            "archive-encoding",
            "PADDING",
            digest(first),
            digest(second),
            "CPIO trailer/padding or compressor representation differs; entry semantics matched",
            expected=True,
            compatibility_affecting=False,
        )
    return result.finish()
