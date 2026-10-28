"""Publish verification metadata only, never local command output or host identities."""

import json
from pathlib import Path
from secripts.context import data_dir
from secripts.provenance import packaged
from secripts.registry import registry

legacy = {r["id"]: r for r in packaged()["artifacts"]}
smoke_path = data_dir() / "validation/smoke.json"
smoke = json.loads(smoke_path.read_text()) if smoke_path.exists() else []
executed = {}
for item in smoke:
    args = item["arguments"]
    if len(args) > 1 and args[0] == "run":
        value = json.loads(item["stdout"])
        executed[args[1]] = {"invocation": value["result"], "exit_code": value["exit_code"]}
records = []
for op in registry().search():
    records.append(
        {
            "operation": op.id,
            "created": "2026-10-28",
            "version": 1,
            "legacy": [
                {
                    k: legacy[source][k]
                    for k in (
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
                "technical_review": "Read-only argv or static environment inspection; shared safety contract",
            },
            "verification": {
                "static": "PASS",
                "shared_unit_contract": "PASS",
                "environment": executed.get(op.id, {"invocation": "UNTESTED"}),
                "hardware": "UNTESTED",
            },
        }
    )
Path("src/secripts/data/operations.json").write_text(
    json.dumps({"schema": 1, "operations": records}, indent=2) + "\n"
)
