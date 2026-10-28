"""Generate the operation reference from the same metadata used by the CLI."""

from pathlib import Path
from secripts.registry import registry

text = "# Operation catalog\n\nGenerated from `js list --json`; update with `python tools/catalog.py`.\n\n"
text += "| Operation | Summary | Risk |\n|---|---|---|\n"
for op in registry().search():
    text += f"| `{op.id}` | {op.summary} | {op.risk} |\n"
Path("docs/catalog.md").write_text(text)
