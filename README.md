# JADIS // SECRIPTS

**Personal Developer Operations Arsenal & Android Recovery Laboratory**

**CLI: `js` · Cockpit: `js 1337` · Recovery Lab: `js recovery`**

Secripts is Christopher Osburn / JADIS's independent personal developer arsenal: one inspectable
command surface for understanding a development environment, a repository, and Android recovery work.
The name keeps the history of scattered scripts; typed operations give that knowledge a contract.
This private repository coexists with Outer Void projects. It is not their universal CLI/control plane.

> Build the system. Prove the system. Then remove the scaffolding.

No copy/paste roulette. No mystery commands. No silent destruction.

## Install

Python 3.11+; Linux and Termux are the supported execution paths. Native Termux/PRoot and hardware
qualification remain distinct from interpreter tests. Runtime dependencies: Python standard library only.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
js --help
js --version
js doctor
js dossier
js 1337
```

Alternatively, `pipx install .` exposes `js` without activating a project environment. The distribution
is `jadis-secripts`; the Python package remains `secripts`. Version 0.2.0 makes a deliberate pre-1.0
launcher break; no compatibility alias is installed. Existing receipts retain their operation identities.
If your system already uses `js` for Node, keep that executable and place the virtual environment or
pipx application directory first on PATH. This host's `/usr/bin/js` is preserved.

## Everyday operations

```sh
js list
js find git
js find 'device tree'
js find --category recovery
js find --risk READ_ONLY
js show android.sdk.validate
js explain git.health
js run git.health
js run python.project
js run java.environment
js run android.sdk.validate
js run git.status --dry-run
```

**70 operations across 19 categories** cover Git/GitHub, Python, Java, SDK, ADB/Fastboot, Termux,
Linux/Debian, SSH, local networking, filesystem, environment, local AI tooling and Recovery Lab.
The [generated catalog](docs/catalog.md) is the same contract consumed by search, execution and menus.
Search ranks exact IDs, ID prefixes, titles, tags, categories, summaries and sanitized legacy filenames.

Git tools inspect worktrees, local divergence, tags, submodules, stashes, changed/untracked/ignored files,
working-file sizes, object storage and recorded signature headers. No branches are deleted and no
signature verifier runs implicitly. Remote reachability and GitHub operations are explicit network calls.

Python inspections use the interpreter running Secripts: venv boundaries, allowlisted pyproject metadata,
editable installs and dependency checks. Project build backends and Gradle wrappers are not executed by
inspection. Java inspection reports observed versions and architecture; branch-specific Android JDK
compatibility stays UNKNOWN. SDK inspection lists installed components and root conflicts without
updating packages or accepting licenses. Local model inspection never searches the entire filesystem.

## Dossier and doctor

```sh
js doctor
js doctor --json
js dossier
js dossier --json
js dossier --devices --json
```

Doctor gives a concise human summary and detailed JSON with PASS/WARN/FAIL/UNKNOWN/UNTESTED/BLOCKED/
UNSUPPORTED states and non-destructive remediation. Invocation success is not a global environment pass.

Dossier combines host, filesystem, guest boundaries, current repository, Python, tool presence, SDK,
local network configuration, model tooling, history and Recovery Lab state. It performs no network calls.
Device counts remain UNTESTED until `--devices` explicitly enumerates transports; enumeration does not
qualify hardware. Java version probing and detailed device interrogation are separate operations.

## The developer cockpit

```sh
js 1337
js 1337 --json
```

The opening dashboard shows actual host/tool evidence, repository branch/dirty/upstream state,
operation/recipe/receipt counts, latest operation/failure, SDK state and Recovery Lab blockers.
An interactive session enumerates transports with bounded probes. Non-TTY preview and JSON snapshots
do not probe devices. Hardware remains UNTESTED regardless of tool presence or device counts.

Described categories lead to metadata-derived operation context, prerequisites, run/dry-run, recipes,
ranked search, filtered archaeology, history/receipt comparison and the Recovery Lab prompt. `V` refreshes
evidence and transports; `T` opens history. `NO_COLOR` disables color. Plain terminals need no frames,
Unicode decoration or terminal framework. The operator prompt is `js://1337 >`.

## Guided workflows

```sh
js recipes
js recipe show python-dev
js recipe run git-review --dry-run
js recipe run python-dev
js recipe run github-readiness --network
js recipe run twrp-tree-review --tree /path/to/tree --dry-run
js recipe run post-build-verification --artifact /path/to/recovery.img
```

**23 recipes** explain purpose and prerequisites, expose their operations, support dry-run and write a
parent receipt linking step receipts. They stop on invocation failure and retain uncertain evidence.
Network recipes require `--network`; dry-runs never contact services. These are inspection/preparation
workflows, not automatic package bootstraps, release publishing or device qualification.

## Android devices

```sh
js device transports --json
js device inspect --json
js device inspect --device TRANSPORT_IDENTIFIER --json
js device fastboot --json
```

ADB dossier selects one authorized transport and collects allowlisted properties plus battery, storage,
display, CPU/memory, package count and existing shell-UID observations. Missing/unauthorized/multiple
transports stop clearly. Identity, Android, build, security, boot and hardware sections retain individual
unknown states. No root/reboot request is sent. Inspection is explicit operator context, not proof of ownership.

Serials are omitted from returned evidence, argv and receipts. Package names and CPU serial fields are
not retained. Fastboot reads a fixed getvar allowlist, never `getvar all`, flash, unlock, erase or reboot.
A device observation does not establish recovery functionality.

## Image Intelligence and Recovery Device Models — 0.3.0

```sh
js inspect /path/to/boot.img --json
js inspect /path/to/kernel --providers --json
js run image.providers
js recovery device create example
js recovery device add-image example boot /path/to/boot.img
js recovery device add-tree example /path/to/tree
js recovery device report example --json
js recovery tree diagnose /path/to/tree --json
js recovery tree derive --device example --output /existing/parent/new-candidate
js recovery plan example --json
```

The reusable Image Intelligence Engine handles Android containers, bounded compression/CPIO,
FDT/DTBO, ELF, legacy uImage and FIT metadata, AVB and partial vendor-marker recognition.
It never executes payloads. Optional installed `file`/`avbtool` evidence is explicit; structural
inspection is not cryptographic verification. [Format support and bounds](docs/image-intelligence.md).

Local Recovery Device Models retain source hashes, fact locations, confidence states and conflicts.
Candidate derivation writes review-only configuration with per-line provenance and unresolved TODOs;
it does not guess kernel paths, partition sizes or a functional fstab. The build planner explains
host/source/tree/model blockers and candidate targets without syncing or compiling.
[Device models and planning](docs/device-model.md). The cockpit/dossier show actual Image Lab
capabilities, optional provider presence and local model/analysis counts.

The supplied recovery corpus is inspected recursively under strict limits, outside Git. Historical
tools are research input, never trusted executables. [Research coverage](docs/research.md).

## Recovery Lab

```sh
js recovery doctor --json
js recovery tree audit /path/to/tree --json
js recovery inspect recovery.img --json
js recovery inspect --device
js recovery verify recovery.img
js recovery init --help
js recovery configure
js recovery sync --dry-run
js recovery build --dry-run
js recovery test recovery.img --device OWNER_CHOSEN_ALIAS
js recovery report recovery.img --tree /path/to/tree --json
js recovery report recovery.img --markdown
```

Static tree intelligence covers products, architecture, slots/virtual A/B, dynamic partitions,
recovery/vendor_boot arrangements, kernel/DTB/DTBO references, fstab, encryption/metadata and AVB flags.
A bounded graph resolves literal local and LOCAL_DIR references, reports cycles and separates direct
from conditional/external/unresolved evidence. No Makefile or dependency code is executed.

Image inspection supports Android boot headers v0–v4 and vendor_boot v3/v4, section bounds, ramdisk
compression, bounded gzip/bzip2/XZ decoding, non-extracting newc CPIO metadata, DTB/bootconfig boundaries,
vendor fragment tables and inferred init_boot candidates. Boot and recovery share a header: partition
role cannot be proven from a filename. LZ4/Zstd are recognized but not decompressed natively. Phase 3 adds bounded LZ4 structural parsing.

AVB footer/vbmeta parsing reports untrusted algorithm, rollback/flags and bounded hash-descriptor
partition declarations. **No cryptographic signature, trusted-key, rollback enforcement, bootability or
compatibility verification occurs.** Optional upstream tools are detected, not silently installed/run.

Reports combine current workspace/tree evidence, graph findings, hash-matched recorded builds,
image/AVB inspection, explicit saved device dossiers and manual qualification records. Source, tree,
build, image structure, device observations and device qualification are separate states. A current tree
audit does not prove which inputs produced an old image.

TWRP orchestration remains **experimental**. It requires explicit source/revision/tree/product/target,
uses at most two jobs and refuses concurrent workspace mutations. This ARM64, low-disk host is not
qualified for real TWRP compilation. Temporary boot refuses unresolved support. Permanent flashing,
unlocking, wiping and repartitioning are absent. Read [Recovery Lab](docs/recovery-lab.md).

## Receipts, completion and lineage

```sh
js history --operation git.health --limit 20 --summary
js history --failed --since 2026-01-01 --json
js receipt latest
js receipt latest --failed
js receipt diff FIRST_ID SECOND_ID --json
js history --artifact ARTIFACT_SHA256 --json
js completion bash > ~/.config/js-completion.bash
# Source that file from your Bash configuration after creating its parent directory.
js archaeology --json
```

Receipts retain sanitized commands, effects, prerequisites, results, durations, artifacts, launcher
release and cwd/environment association. Filters, latest-failure retrieval and comparison do not replay
commands. Older receipts remain readable. Canonical storage is private local JSON, without a database.

Bash completion discovers commands, operation/recipe IDs and safe enumerations from current contracts.
It performs no diagnostics, network requests or device probes. Zsh/Fish-specific completion is not provided.

The historical archive remains metadata-only: **153 members · 27 duplicates · 8 EXTRACT · 41 ARCHIVE ·
69 REJECT · 35 SECRET · 0 PROMOTE**. No source contents or historical credentials are imported. Existing
opaque secret exclusions and source hashes remain intact. [Archaeology](docs/archaeology.md) and
[provenance](docs/provenance.md) explain review boundaries and release-specific verification.

## Safety and configuration

READ_ONLY inspects; MUTATING describes writes; PRIVILEGED never elevates; DESTRUCTIVE requires a
specific interactive phrase. No destructive production operation ships. Recipes use the same dispatcher.
Argument vectors are the rule; the fixed TWRP shell adapter exists only for trusted upstream shell
functions. Secret-like arguments are refused and output is sanitized. Pattern scanning and identifier
masking cannot replace review of personal information before sharing. Read [SECURITY.md](SECURITY.md).

Explicit CLI parameters override workspace choices. `SECRIPTS_DATA_HOME` overrides
`$XDG_DATA_HOME/secripts`, defaulting to `~/.local/share/secripts`. SDK selection uses `ANDROID_HOME`
then `ANDROID_SDK_ROOT`, reporting conflicts. Basic commands require no configuration. Runtime state,
receipts and builds stay outside Git; the launcher rename does not migrate or rewrite that state.

Exit codes: 0 invocation success; 1 operation/state failure; 2 invalid usage; 3 missing prerequisite or
device; 4 safety refusal; 5 unsupported host/backend; 130 interruption. Inspect evidence states separately.

## Prove changes

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest -q
python tools/secret_scan.py
python -m build
python tools/qualify.py
python tools/validate.py                 # installed js must be on PATH
python tools/validate.py --devices       # explicit transport enumeration
```

No unit test downloads Android sources or touches devices. Synthetic fixtures are explicitly labeled.
CI uses a serial Python matrix and local checks; its observed results are recorded separately from local
validation. See [verification](docs/verification.md), [architecture](docs/architecture.md) and
[contributing](CONTRIBUTING.md) for evidence, limits and remaining qualification work.

## Credits and attribution

[CREDITS.md](CREDITS.md) identifies material specifications, developers, projects and research
influences, with source and licensing boundaries. Detailed lineage lives in research provenance.
Attribution and licensing review are required when adding an externally influenced capability;
credits do not substitute for required license notices.
