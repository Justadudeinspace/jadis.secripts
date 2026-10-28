"""Check current documentation links, CLI examples, catalog and attribution references locally."""

import json
from pathlib import Path
import re
from urllib.parse import urlparse
from secripts.registry import registry

root = Path(__file__).resolve().parents[1]
errors = []
for path in [root / "README.md", root / "CREDITS.md", *sorted((root / "docs").glob("*.md"))]:
    text = path.read_text()
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if target.startswith("https://"):
            if not urlparse(target).hostname:
                errors.append(f"{path.name}: malformed URL")
        elif not target.startswith(("#", "http://")):
            if not (path.parent / target.split("#", 1)[0]).exists():
                errors.append(f"{path.name}: missing local reference {target}")
    if re.search(
        r"(?:^|[`$\s])sec(?: --| (?:1337|doctor|recovery|run|find|list|explain|receipt|history|recipes)\b|://)",
        text,
    ):
        errors.append(f"{path.name}: stale CLI example")
research = json.loads((root / "src/secripts/data/research.json").read_text())
if any(not urlparse(r["url"]).hostname for r in research["sources"]):
    errors.append("Invalid research URL")
if "CREDITS.md" not in (root / "README.md").read_text():
    errors.append("README attribution link missing")
catalog = (root / "docs/catalog.md").read_text()
if any(f"`{op.id}`" not in catalog for op in registry().search()):
    errors.append("Catalog operation missing")
print("\n".join(errors) if errors else "Documentation/reference audit: PASS")
raise SystemExit(bool(errors))
