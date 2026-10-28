"""Apply explicit content/intent review decisions to a fresh metadata inventory."""

from collections import Counter
from pathlib import Path
import json
from secripts.registry import registry
from secripts.provenance import validate

path = Path("src/secripts/data/legacy.json")
value = json.loads(path.read_text())
reviewed = {
    "legacy-0000",
    "legacy-0003",
    "legacy-0009",
    "legacy-0013",
    "legacy-0024",
    "legacy-0032",
    "legacy-0122",
    "legacy-0136",
}
for row in value["artifacts"]:
    replacements = [op.id for op in registry().search() if row["id"] in op.legacy]
    if row["id"] == "legacy-0032":
        replacements += ["js recovery tree audit", "js recovery build"]
    if row["classification"] == "EXTRACT" and row["id"] not in reviewed:
        row["classification"] = "ARCHIVE"
        row["reason"] = (
            "Candidate lineage retained as metadata only; no validated production extraction"
        )
    if (
        any(
            word in row["source"].lower()
            for word in (
                "pwn_",
                "adb_unlock",
                "blux",
                "nexus",
                "vigyl",
                "nanite",
                "design_spec",
                "operating_standard",
                "release_ready",
            )
        )
        and not row["contained_secrets"]
    ):
        row["classification"] = "REJECT"
        row["reason"] = (
            "Ownership bypass/offensive intent or separate project; excluded from Secripts"
        )
    if row["id"] in reviewed:
        assert not row["contained_secrets"]
        row["review"] = "Intent/command review; rewritten independently, no source content imported"
        row["modern_replacement"] = replacements
value["counts"] = dict(Counter(r["classification"] for r in value["artifacts"]))
validate(value)
path.write_text(json.dumps(value, indent=2) + "\n")
print(value["counts"], "DUPLICATE", value["duplicates"])
