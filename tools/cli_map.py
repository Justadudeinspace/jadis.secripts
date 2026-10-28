"""Generate the complete canonical/alias reference from parser naming contracts."""

import json
from pathlib import Path
from secripts.cli import parser
from secripts.commands import inventory, name

rows = inventory(parser())
Path("docs/cli-map.json").write_text(json.dumps({"schema": 1, "commands": rows}, indent=2) + "\n")
text = """# Streamlined CLI — 0.5.0

Frequently typed namespaces/actions normally use 2–4 character shorthand. Full descriptive
names remain accepted aliases. Never shorten a command when ambiguous or misleading.

Short commands are the working interface; long commands are the descriptive interface.
Both normalize to the same stable command identity **before dispatch and authorization**.
Operation IDs, recipes and historical receipts retain their existing identities.

`js --help` emphasizes canonical names and lists accepted aliases. Both spellings provide
the same command help. Close invalid top-level/subcommand spellings receive suggestions.
No shell aliases, duplicate registry operations or compatibility executables are created.

## Top-level map

| Working form | Accepted aliases | Stable identity |
|---|---|---|
"""
for row in rows:
    if not row["scope"]:
        text += f"| `js {row['canonical']}` | {', '.join('`' + a + '`' for a in row['aliases']) or '—'} | `{row['identity']}` |\n"
text += """
## Nested map

Any parent spelling combines with any accepted child spelling. Examples: `js img rt`
and `js image roundtrip`; `js ry dce ls` and `js recovery device list`.

| Working namespace | Action | Accepted aliases |
|---|---|---|
"""
for row in rows:
    if row["scope"]:
        scope = " ".join(name(part).canonical for part in row["scope"])
        text += f"| `js {scope}` | `{row['canonical']}` | {', '.join('`' + a + '`' for a in row['aliases']) or '—'} |\n"
text += """
## Convenience, compatibility and safety

`js insp IMAGE`, `js inspect IMAGE`, `js img insp IMAGE` and `js image inspect IMAGE`
converge on the same inspection command and `image.inspect` receipt identity. `js prov`
and `js img prov` share provider inventory. Most engineering actions stay under `img`/`ram`
to keep the root small; top-level `ws`, `cmp`, `rb`, `upk` and `rt` were deliberately not
added as redundant routes. There is no standalone `dtb` namespace: use `js insp` or
`js img model` for FDT/DTB evidence. Help never advertises an unimplemented namespace.

`run`, `avb`, `dtbo`, `1337` and `scan` remain unchanged. Nested `plan`, `pack`, `tree`,
`report`, `model`, `build`, `audit` and `derive` favor established readable words over
code-golf. Rare model-import actions retain descriptive names. Device is `dce`, never `dev`.

Bash completion derives canonical names, aliases and nested choices from these contracts;
canonical names appear first. It performs no diagnostics, device/network probes or providers.
Recipes refer to operation IDs rather than CLI strings. Existing long-form scripts remain
valid. Historical evidence and runtime receipts are not rewritten. Raw invocation spelling
is not retained as new receipt data, avoiding accidental device-identifier retention.

The [pre-streamlining inventory](cli-before-streamlining.json),
[collision audit](cli-collision-audit.json) and [machine-readable current map](cli-map.json)
are review artifacts. `python tools/cli_map.py` regenerates the current map from code;
`python tools/audit_docs.py` checks it for drift. Tests prove scoped uniqueness, parser
identity, arguments, exit codes, JSON semantics, receipt IDs, risk guards and nested aliases.
"""
Path("docs/cli.md").write_text(text)
