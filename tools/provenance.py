"""Generate release-specific lineage without inventing current validation evidence."""

import json
from pathlib import Path
from secripts import __version__
from secripts.context import data_dir
from secripts.provenance import packaged
from secripts.registry import registry

legacy = {row["id"]: row for row in packaged()["artifacts"]}
root = data_dir() / "validation"
quality = (
    json.loads((root / "phase2-quality.json").read_text())
    if (root / "phase2-quality.json").is_file()
    else {}
)
validated = quality.get("release") == __version__ and quality.get("result") == "PASS"
smoke = (
    json.loads((root / "phase2-smoke.json").read_text())
    if (root / "phase2-smoke.json").is_file()
    else {}
)
executed = smoke.get("operations", {}) if smoke.get("release") == __version__ else {}
records = []
for op in registry().search():
    records.append(
        {
            "operation": op.id,
            "created": "2026-10-28",
            "release": __version__,
            "version": 1,
            "legacy": [
                {
                    key: legacy[source][key]
                    for key in (
                        "id",
                        "source",
                        "source_sha256",
                        "classification",
                        "duplicate_group",
                        "contained_secrets",
                        "review",
                    )
                }
                for source in op.legacy
            ],
            "implementation": "Independent rewrite of safe intent"
            if op.legacy
            else "New engineering",
            "review": {
                "sensitive_content_excluded": True,
                "modernized": True,
                "technical_review": "Allowlisted inspection contract; no generic argument forwarding",
            },
            "verification": {
                "registry_and_shared_tests": "PASS" if validated else "UNTESTED",
                "environment": executed.get(op.id, {"invocation": "UNTESTED"}),
                "hardware": "UNTESTED",
            },
        }
    )
Path("src/secripts/data/operations.json").write_text(
    json.dumps({"schema": 1, "release": __version__, "operations": records}, indent=2) + "\n"
)
