"""Registry-facing artifact engineering workflows. No payload execution or device access."""

from pathlib import Path
import tempfile
from secripts.images import bootmodel, dtbo_model, ramdisk_model
from secripts.images.artifacts import read, digest, evidence, canonical, json_model, child
from secripts.images.comparison import Comparison, ramdisks
from secripts.images.devicetree import fdt
from secripts.safety import SecError


def family(raw):
    if raw.startswith((b"ANDROID!", b"VNDRBOOT")):
        return "android"
    if raw.startswith(b"\xd7\xb7\xab\x1e"):
        return "dtbo"
    if raw.startswith(b"\xd0\x0d\xfe\xed"):
        return "fdt"
    if raw.startswith(b"\x27\x05\x19\x56"):
        return "uimage"
    from secripts.images.codecs import detect

    return "ramdisk" if detect(raw) != "UNKNOWN" else "opaque"


def model(path):
    raw = read(path)
    kind = family(raw)
    if kind == "android":
        return bootmodel.model(path)
    if kind == "dtbo":
        value = dtbo_model.model(raw)
        return {
            **value,
            "entries": [{k: v for k, v in e.items() if k != "payload"} for e in value["entries"]],
        }
    if kind == "fdt":
        return fdt(raw, canonical=True)
    if kind == "uimage":
        from secripts.images.containers import uimage

        return uimage(raw)
    if kind == "ramdisk":
        return ramdisk_model.inspect(path)
    from secripts.images.engine import inspect

    return inspect(path)


def unpack(path, output):
    kind = family(read(path))
    if kind == "android":
        return bootmodel.unpack(path, output)
    if kind == "dtbo":
        return dtbo_model.extract(path, output)
    if kind == "ramdisk":
        return ramdisk_model.extract(path, output)
    raise SecError(
        "Extraction unsupported for this format; native model/compare remain available", 5
    )


def workspace(path):
    path = Path(path)
    for name, kind in [
        ("image", "android-image"),
        ("ramdisk", "ramdisk-cpio"),
        ("dtbo", "android-dt-table"),
    ]:
        candidate = child(path, f"model/{name}.json")
        if candidate.is_file():
            value = json_model(candidate, kind)
            source = read(child(path, "source/artifact.bin"))
            expected = (
                value.get("source_sha256") if name != "ramdisk" else value.get("encoded_sha256")
            )
            return {
                "schema": 1,
                "model": kind,
                "immutable_source": "PASS" if digest(source) == expected else "FAIL",
                "source_sha256": digest(source),
                "model_data": value,
                "device_compatibility": "UNTESTED",
            }
    raise SecError("Artifact workspace model missing", 3)


def rebuild(path, output):
    kind = workspace(path)["model"]
    if kind == "android-image":
        return bootmodel.rebuild(path, output)
    if kind == "android-dt-table":
        return dtbo_model.rebuild(path, output)
    return ramdisk_model.pack(path, output)


def compare(first, second):
    a, b = read(first), read(second)
    kind = family(a)
    if family(b) != kind:
        result = Comparison(a, b)
        result.add("container", "STRUCTURE", kind, family(b), "Different image families")
        result.value.update(structural_equivalence="DIFFERENT", semantic_equivalence="DIFFERENT")
        value = result.finish()
    elif kind == "android":
        value = bootmodel.compare(first, second)
    elif kind == "dtbo":
        value = dtbo_model.compare(first, second)
    elif kind == "ramdisk":
        value = ramdisks(a, b)
    elif kind == "fdt":
        left, right = fdt(a, canonical=True), fdt(b, canonical=True)
        result = Comparison(a, b)

        def semantic(tree):
            return {
                "header": tree["header"],
                "reservations": tree["reservations"],
                "nodes": sorted(tree["nodes"]),
                "properties": sorted(
                    (p["node"], p["name"], p["sha256"]) for p in tree["properties"]
                ),
            }

        equal = semantic(left) == semantic(right)
        if not equal:
            result.add(
                "fdt",
                "CONTENT",
                digest(a),
                digest(b),
                "Node/property/reservation/header semantics differ",
            )
        elif a != b:
            result.add(
                "fdt-layout",
                "ALIGNMENT",
                left["regions"],
                right["regions"],
                "FDT encoding/layout differs; modeled semantics matched",
                expected=True,
            )
        result.value.update(
            structural_equivalence="STRUCTURALLY_EQUIVALENT",
            semantic_equivalence="SEMANTICALLY_EQUIVALENT" if equal else "DIFFERENT",
            component_equivalence="CONTENT_EQUIVALENT" if equal else "DIFFERENT",
            metadata_equivalence="SEMANTICALLY_EQUIVALENT" if equal else "DIFFERENT",
        )
        value = result.finish()
    elif kind == "opaque":
        result = Comparison(a, b)
        if a != b:
            result.add(
                "opaque-artifact",
                "BYTE",
                digest(a),
                digest(b),
                "Unsupported semantic format; byte comparison only",
            )
        result.value["unresolved"].append("No canonical semantic model for this format")
        value = result.finish()
    else:
        from secripts.images.containers import uimage

        left, right = uimage(a), uimage(b)
        result = Comparison(a, b)
        if a != b:
            result.add("uimage", "CONTENT", left, right, "uImage metadata or payload bytes differ")
        result.value.update(
            structural_equivalence="STRUCTURALLY_EQUIVALENT",
            semantic_equivalence="SEMANTICALLY_EQUIVALENT" if a == b else "DIFFERENT",
            component_equivalence="CONTENT_EQUIVALENT" if a[64:] == b[64:] else "DIFFERENT",
            metadata_equivalence="SEMANTICALLY_EQUIVALENT" if a[:64] == b[:64] else "DIFFERENT",
        )
        value = result.finish()
    receipt = evidence("image.compare", source=first, comparison=value, second_artifact=str(second))
    return {**value, "receipt_id": receipt["receipt_id"]}


def roundtrip(path, output=None):
    if output is None:
        with tempfile.TemporaryDirectory(prefix="js-roundtrip-") as directory:
            value = roundtrip(path, Path(directory) / "workspace")
            value["workspace"] = "TEMPORARY_DISCARDED"
            return value
    unpack(path, output)
    rebuilt = Path(output) / "rebuilt/artifact.bin"
    rebuild(output, rebuilt)
    value = compare(path, rebuilt)
    canonical(Path(output) / "reports/roundtrip.json", value)
    receipt = evidence("image.roundtrip", source=path, output=rebuilt, comparison=value)
    return {**value, "workspace": str(output), "receipt_id": receipt["receipt_id"]}
