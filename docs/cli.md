# Streamlined CLI — 0.5.0

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
| `js help` | — | `help` |
| `js guide` | — | `guide` |
| `js ai` | — | `ai` |
| `js img` | `image` | `image` |
| `js ram` | `ramdisk` | `ramdisk` |
| `js dtbo` | — | `dtbo` |
| `js avb` | — | `avb` |
| `js insp` | `inspect` | `inspect` |
| `js prov` | `providers` | `providers` |
| `js res` | `research` | `research` |
| `js ls` | `list` | `list` |
| `js fd` | `find` | `find` |
| `js dos` | `dossier` | `dossier` |
| `js comp` | `completion` | `completion` |
| `js dce` | `device` | `device` |
| `js sh` | `show` | `show` |
| `js exp` | `explain` | `explain` |
| `js doc` | `doctor` | `doctor` |
| `js run` | — | `run` |
| `js rcps` | `recipes` | `recipes` |
| `js rcp` | `recipe` | `recipe` |
| `js hist` | `history` | `history` |
| `js rcpt` | `receipt`, `receipts` | `receipt` |
| `js 1337` | — | `1337` |
| `js arch` | `archaeology` | `archaeology` |
| `js scan` | — | `scan` |
| `js ing` | `ingest` | `ingest` |
| `js ry` | `recovery` | `recovery` |

## Nested map

Any parent spelling combines with any accepted child spelling. Examples: `js img rt`
and `js image roundtrip`; `js ry dce ls` and `js recovery device list`.

| Working namespace | Action | Accepted aliases |
|---|---|---|
| `js help` | `img` | `image` |
| `js help` | `ry` | `recovery` |
| `js help` | `dce` | `device` |
| `js help` | `evidence` | — |
| `js help` | `ai` | — |
| `js ai` | `setup` | — |
| `js ai` | `prov` | `providers` |
| `js ai` | `models` | — |
| `js ai` | `context` | — |
| `js ai` | `ask` | — |
| `js ai` | `tools` | — |
| `js ai tools` | `registry.search` | — |
| `js ai tools` | `registry.show` | — |
| `js ai tools` | `receipt.summary` | — |
| `js img` | `insp` | `inspect` |
| `js img` | `model` | — |
| `js img` | `upk` | `unpack` |
| `js img` | `ws` | `workspace` |
| `js img` | `rb` | `rebuild` |
| `js img` | `cmp` | `compare` |
| `js img` | `rt` | `roundtrip` |
| `js img` | `prov` | `providers` |
| `js img` | `diff` | `differential` |
| `js ram` | `insp` | `inspect` |
| `js ram` | `ext` | `extract` |
| `js ram` | `pack` | — |
| `js ram` | `cmp` | `compare` |
| `js dtbo` | `insp` | `inspect` |
| `js dtbo` | `ext` | `extract` |
| `js dtbo` | `rb` | `rebuild` |
| `js dtbo` | `cmp` | `compare` |
| `js avb` | `insp` | `inspect` |
| `js avb` | `vfy` | `verify` |
| `js comp` | `bash` | — |
| `js comp` | `candidates` | — |
| `js dce` | `insp` | `inspect` |
| `js dce` | `transports` | — |
| `js dce` | `fastboot` | — |
| `js rcp` | `sh` | `show` |
| `js rcp` | `run` | — |
| `js ry` | `acquire` | — |
| `js ry` | `source` | — |
| `js ry` | `status` | — |
| `js ry` | `graph` | — |
| `js ry` | `fstab` | — |
| `js ry` | `deps` | — |
| `js ry deps` | `graph` | — |
| `js ry deps` | `validate` | — |
| `js ry deps` | `resolve` | — |
| `js ry` | `flags` | — |
| `js ry` | `failure` | — |
| `js ry` | `doc` | `doctor` |
| `js ry` | `insp` | `inspect` |
| `js ry` | `tree` | — |
| `js ry tree` | `audit` | — |
| `js ry tree` | `insp` | `inspect` |
| `js ry tree` | `diag` | `diagnose` |
| `js ry tree` | `derive` | — |
| `js ry` | `plan` | — |
| `js ry` | `dce` | `device` |
| `js ry dce` | `create` | — |
| `js ry dce` | `ls` | `list` |
| `js ry dce` | `add-image` | — |
| `js ry dce` | `add-tree` | — |
| `js ry dce` | `add-metadata` | — |
| `js ry dce` | `insp` | `inspect` |
| `js ry dce` | `report` | — |
| `js ry` | `init` | — |
| `js ry` | `cfg` | `configure` |
| `js ry` | `sync` | — |
| `js ry` | `build` | — |
| `js ry` | `vfy` | `verify` |
| `js ry` | `boot` | — |
| `js ry` | `test` | — |
| `js ry` | `report` | — |
| `js ry` | `clean` | — |

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
