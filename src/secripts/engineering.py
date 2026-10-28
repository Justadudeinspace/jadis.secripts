"""Image engineering contracts and adapters shared by CLI, cockpit and recipes."""

from pathlib import Path


def handle(name, parameters):
    from secripts.images import workflows, ramdisk_model, dtbo_model, avbmodel
    from secripts.images.artifacts import read, evidence
    from secripts.images.comparison import ramdisks

    artifact = Path(parameters["artifact"]) if parameters.get("artifact") else None
    other = Path(parameters["other"]) if parameters.get("other") else None
    workspace = Path(parameters["workspace"]) if parameters.get("workspace") else None
    output = Path(parameters["output"]) if parameters.get("output") else None
    if name == "image.differential":
        from secripts.images.oracles import aosp

        return aosp(artifact, Path(parameters["tools"]))
    if name == "image.model":
        value = workflows.model(artifact)
        receipt = evidence(
            name, source=artifact, format=value.get("format"), model_schema=value.get("schema")
        )
        return {**value, "receipt_id": receipt["receipt_id"]}
    if name == "image.unpack":
        return workflows.unpack(artifact, output)
    if name == "image.workspace":
        return workflows.workspace(workspace)
    if name == "image.rebuild":
        return workflows.rebuild(workspace, output)
    if name in {"image.compare", "dtbo.compare"}:
        return workflows.compare(artifact, other)
    if name == "image.roundtrip":
        return workflows.roundtrip(artifact, output)
    if name == "ramdisk.inspect":
        return ramdisk_model.inspect(artifact)
    if name == "ramdisk.extract":
        return ramdisk_model.extract(artifact, output)
    if name == "ramdisk.pack":
        return ramdisk_model.pack(workspace, output, parameters.get("compression"))
    if name == "ramdisk.compare":
        value = ramdisks(read(artifact, 32 * 1024**2), read(other, 32 * 1024**2))
        receipt = evidence(name, source=artifact, comparison=value, second_artifact=str(other))
        return {**value, "receipt_id": receipt["receipt_id"]}
    if name == "dtbo.inspect":
        value = workflows.model(artifact)
        if value.get("model") != "android-dt-table":
            raise ValueError("Expected Android DTBO table")
        receipt = evidence(name, source=artifact, entries=len(value["entries"]))
        return {**value, "receipt_id": receipt["receipt_id"]}
    if name == "dtbo.extract":
        return dtbo_model.extract(artifact, output)
    if name == "dtbo.rebuild":
        return dtbo_model.rebuild(workspace, output)
    if name == "avb.inspect":
        value = avbmodel.metadata(artifact)
        receipt = evidence(name, source=artifact, metadata=value)
        return {**value, "receipt_id": receipt["receipt_id"]}
    if name == "avb.verify":
        return avbmodel.verify(artifact, expected_key=parameters.get("key"))
    raise ValueError("Unknown image engineering operation")


def operations():
    from secripts.registry import Operation, Parameter
    from secripts.safety import Risk

    definitions = [
        (
            "image.differential",
            "AOSP differential verification",
            "Explicit hash-pinned AOSP unpack/repack comparison; no corpus tools.",
            ("artifact", "tools"),
            (),
        ),
        (
            "image.model",
            "Canonical image model",
            "Inspect complete supported artifact structure without payload dumps.",
            ("artifact",),
            (),
        ),
        (
            "image.unpack",
            "Unpack artifact",
            "Create a new isolated artifact workspace, preserving source and section hashes.",
            ("artifact", "output"),
            (),
        ),
        (
            "image.workspace",
            "Artifact workspace evidence",
            "Inspect versioned model and immutable source hash.",
            ("workspace",),
            (),
        ),
        (
            "image.rebuild",
            "Rebuild artifact",
            "Reconstruct a new artifact from an explicit workspace; never overwrite source.",
            ("workspace", "output"),
            (),
        ),
        (
            "image.compare",
            "Compare artifacts",
            "Compare bytes, structure, components, metadata and semantic evidence independently.",
            ("artifact", "other"),
            (),
        ),
        (
            "image.roundtrip",
            "Round-trip artifact",
            "Extract, reconstruct, reparse and compare; device qualification remains UNTESTED.",
            ("artifact",),
            ("output",),
        ),
        (
            "ramdisk.inspect",
            "Inspect ramdisk model",
            "Decode bounded streams and model newc/CRC entries without extraction.",
            ("artifact",),
            (),
        ),
        (
            "ramdisk.extract",
            "Extract virtual ramdisk",
            "Create numbered payload files and metadata; never materialize archive symlinks or special files.",
            ("artifact", "output"),
            (),
        ),
        (
            "ramdisk.pack",
            "Pack ramdisk",
            "Pack a virtual workspace or safe directory deterministically into a new artifact.",
            ("workspace", "output"),
            ("compression",),
        ),
        (
            "ramdisk.compare",
            "Compare ramdisks",
            "Explain file, mode, owner, link, order and encoding differences.",
            ("artifact", "other"),
            (),
        ),
        (
            "dtbo.inspect",
            "Inspect Android DT table",
            "Inspect entry metadata, shared blobs and supported FDT structures.",
            ("artifact",),
            (),
        ),
        (
            "dtbo.extract",
            "Extract DT table",
            "Create an isolated workspace with individually bounded DT blobs.",
            ("artifact", "output"),
            (),
        ),
        (
            "dtbo.rebuild",
            "Rebuild DT table",
            "Create a canonical DT table with shared identical blobs and validated entries.",
            ("workspace", "output"),
            (),
        ),
        (
            "dtbo.compare",
            "Compare DT tables",
            "Separate table layout from entry metadata and blob content.",
            ("artifact", "other"),
            (),
        ),
        (
            "avb.inspect",
            "Inspect AVB model",
            "Inspect authentication, auxiliary regions, descriptor types and public-key identity.",
            ("artifact",),
            (),
        ),
        (
            "avb.verify",
            "Verify AVB evidence",
            "Explicit optional avbtool signature/key verification plus native descriptor hash checks; no device trust claim.",
            ("artifact",),
            ("key",),
        ),
    ]
    writes = {
        "image.unpack",
        "image.rebuild",
        "image.roundtrip",
        "ramdisk.extract",
        "ramdisk.pack",
        "dtbo.extract",
        "dtbo.rebuild",
    }
    descriptions = {
        "artifact": "Source artifact",
        "other": "Second artifact",
        "output": "New output path; overwrite refused",
        "workspace": "Artifact workspace or safe source directory",
        "compression": "Encoder: none/gzip/zlib/raw-deflate/xz/lzma-alone/bzip2/lz4",
        "key": "Expected PEM PUBLIC key; private keys refused",
        "tools": "Reviewed hash-pinned AOSP mkbootimg source directory",
    }
    return [
        Operation(
            identifier,
            title,
            summary,
            identifier.split(".")[0],
            risk=Risk.MUTATING if identifier in writes else Risk.READ_ONLY,
            handler="engineering",
            parameters=tuple(
                Parameter(
                    name,
                    descriptions[name],
                    name in required,
                    "text" if name == "compression" else "path",
                )
                for name in required + optional
            ),
            effect="Create only explicit new workspace/artifact paths; source and devices unchanged."
            if identifier in writes
            else "Inspect explicit local artifacts; verification may invoke installed avbtool with fixed argv.",
        )
        for identifier, title, summary, required, optional in definitions
    ]
