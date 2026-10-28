"""Evidence acquisition plans, not downloads, extraction or device modification."""

from pathlib import Path
from secripts.safety import SecError

INPUTS = {
    "firmware": (
        "Stock firmware package",
        "Exact device/build provenance matters; inspect the package offline before selecting partition images.",
    ),
    "images": (
        "Extracted partition images",
        "boot/vendor_boot/init_boot/recovery describe different roles; inspect content rather than extensions.",
    ),
    "device": (
        "Authorized connected device",
        "Read-only properties can supplement firmware; they cannot qualify recovery or establish ownership.",
    ),
    "tree": (
        "Existing recovery tree",
        "Static declarations expose dependencies, kernel strategy and conflicts; Make is never evaluated.",
    ),
    "recovery": (
        "Existing recovery image",
        "Structure and reconstruction evidence do not prove compatibility or bootability.",
    ),
    "kernel": (
        "Kernel source or prebuilt",
        "Record revision/configuration, DTB/DTBO and vendor module relationships before selecting a strategy.",
    ),
    "identity": (
        "Device identity only",
        "Start with exact codename, variant, launch generation and lawful stock-image sources; do not guess from marketing names.",
    ),
}


def acquire(have="identity", *, artifact=None, tree=None, model=None):
    if have not in INPUTS:
        raise SecError("Unsupported acquisition input", 2)
    observations = []
    if artifact:
        from secripts.images.engine import inspect

        observations.append({"artifact": inspect(Path(artifact))})
    if tree:
        from secripts.recovery.planner import diagnose

        observations.append({"tree": diagnose(Path(tree))})
    if model:
        from secripts.recovery.model import report

        observations.append({"device_model": report(model)})
    steps = [
        {
            "stage": "IDENTIFY",
            "why": "Separate device variant and partition role from file naming.",
            "command": ["js", "ry", "dce", "create", "MODEL"],
        },
        {
            "stage": "INSPECT",
            "why": "Hash and inspect selected images before assigning their evidenced partition role.",
            "command": ["js", "insp", "IMAGE", "--json"],
        },
        {
            "stage": "MODEL",
            "why": "Attach image evidence; disagreement remains CONFLICT.",
            "command": ["js", "ry", "dce", "add-image", "MODEL", "ROLE", "IMAGE"],
        },
        {
            "stage": "TREE",
            "why": "Audit an existing tree or derive a review-only candidate after architecture evidence exists.",
            "command": ["js", "ry", "tree", "diag", "TREE", "--json"],
        },
        {
            "stage": "PLAN",
            "why": "Resolve source, kernel/common/vendor dependencies and host constraints before building.",
            "command": ["js", "ry", "plan", "MODEL", "--json"],
        },
        {
            "stage": "BUILD",
            "why": "Review an explicitly configured workspace; a dry run does not compile.",
            "command": ["js", "ry", "build", "--dry-run"],
        },
    ]
    if have == "device":
        steps.insert(
            0,
            {
                "stage": "READ_ONLY_DEVICE",
                "why": INPUTS[have][1],
                "command": ["js", "dce", "insp", "--device", "EXPLICIT_TRANSPORT"],
            },
        )
    return {
        "schema": 1,
        "status": "PARTIAL",
        "input": have,
        "explanation": INPUTS[have][1],
        "choices": [{"id": k, "title": v[0], "why": v[1]} for k, v in INPUTS.items()],
        "observations": observations,
        "steps": steps,
        "placeholders": "Uppercase command operands must be replaced with reviewed local values; ROLE is an evidenced partition role.",
        "boundaries": [
            "No firmware download or package extraction",
            "No device mutation",
            "Candidate is REVIEW_REQUIRED",
            "Compilation is not qualification",
        ],
        "hardware_qualification": "UNTESTED",
    }
