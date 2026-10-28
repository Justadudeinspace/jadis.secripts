"""Registry adapters for the image/recovery intelligence laboratory."""

from pathlib import Path


def image(c=None, **parameters):
    from secripts.images.engine import inspect, inspection_failed

    result = inspect(Path(parameters["artifact"]))
    if inspection_failed(result):
        from secripts.safety import SecError

        raise SecError("Image structure inspection failed: " + "; ".join(result["warnings"]), 1)
    return result


def providers(c=None, **parameters):
    from secripts.images.providers import availability
    from secripts.images.engine import FORMATS

    return {
        "formats": list(FORMATS),
        "providers": availability(),
        "execution": "Only explicit --providers runs installed tools",
    }


def device_model(c=None, **parameters):
    from secripts.recovery.model import report

    return report(parameters["model"])


def tree_diagnose(c=None, **parameters):
    from secripts.recovery.planner import diagnose

    return diagnose(Path(parameters["tree"]))


def build_plan(c=None, **parameters):
    from secripts.recovery.planner import plan

    return plan(parameters["model"])


def host(c=None, **parameters):
    from secripts.recovery.planner import host_qualification

    return host_qualification()


def derive(c=None, **parameters):
    from secripts.recovery.planner import derive as generate

    return generate(parameters["model"], Path(parameters["output"]))


HANDLERS = {
    "image_intelligence": image,
    "image_providers": providers,
    "device_model": device_model,
    "tree_diagnose": tree_diagnose,
    "build_plan": build_plan,
    "host_qualification": host,
    "tree_derive": derive,
}


def operations():
    from secripts.registry import Operation, Parameter
    from secripts.safety import Risk

    artifact = (Parameter("artifact", "Image/container/ramdisk to inspect", True, "path"),)
    model = (Parameter("model", "Local recovery device model name", True),)
    tree = (Parameter("tree", "Local device tree", True, "path"),)
    return [
        Operation(
            "image.inspect",
            "Image Intelligence",
            "Identify and inspect bounded image structures without executing payloads.",
            "image",
            handler="image_intelligence",
            parameters=artifact,
            tags=("boot", "dtb", "dtbo", "elf", "fit", "lz4"),
        ),
        Operation(
            "image.providers",
            "Image evidence providers",
            "Inspect optional installed tooling and native formats without invoking providers.",
            "image",
            handler="image_providers",
        ),
        Operation(
            "recovery.model",
            "Recovery Device Model",
            "Inspect source-linked facts, conflicts and unresolved device evidence.",
            "recovery",
            handler="device_model",
            parameters=model,
        ),
        Operation(
            "recovery.diagnose",
            "TWRP tree diagnosis",
            "Explain generation hints, dependencies and reasons a tree needs review.",
            "recovery",
            handler="tree_diagnose",
            parameters=tree,
        ),
        Operation(
            "recovery.plan",
            "Recovery Build Planner",
            "Correlate device/source/tree/host evidence; never sync, build or qualify hardware.",
            "recovery",
            handler="build_plan",
            parameters=model,
        ),
        Operation(
            "recovery.host",
            "Build host qualification evidence",
            "Inspect architecture, memory, disk, prerequisites and unqualified boundaries.",
            "recovery",
            handler="host_qualification",
        ),
        Operation(
            "recovery.derive",
            "Candidate tree derivation",
            "Generate a new candidate tree with per-line evidence; never overwrite or claim build readiness.",
            "recovery",
            risk=Risk.MUTATING,
            handler="tree_derive",
            parameters=model
            + (Parameter("output", "New candidate directory; parent must exist", True, "path"),),
            effect="Creates a new candidate tree and review/provenance files; no source/image/device modification.",
        ),
    ]
