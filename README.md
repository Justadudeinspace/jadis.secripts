# JADIS // SECRIPTS

**Personal Developer Operations Arsenal & Android Recovery Laboratory**

Old hacks → hardened tools. Commands → operations. Notes → guided workflows.

**NO COPY/PASTE ROULETTE. NO MYSTERY COMMANDS. NO SILENT DESTRUCTION.**

Secripts is Christopher Osburn / JADIS's personal developer tooling project. The name keeps the
history of a script collection; the implementation gives that collection a contract. `sec` makes
operations discoverable, explains their effects and records what ran. `sec 1337` is the master
operator console. `sec recovery` is a developer-side Android recovery laboratory with a TWRP backend.
This is an independent JADIS project, not an Outer-Void product or universal control plane.

> Build the system. Prove the system. Then remove the scaffolding.

## Install

Python 3.11+; Linux is the primary host. Termux and Debian PRoot diagnostics are supported in the
code path, with separate host qualification still limited. Windows/macOS execution is unsupported.
No runtime dependencies beyond Python's standard library.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
sec --help
sec doctor
sec 1337
```

Alternatively, use `pipx install .`. Keep the virtual environment active, or use pipx, to put `sec`
on PATH. There is no need to invoke source files manually. See [verification](docs/verification.md)
for the exact environments actually exercised.

## Use the arsenal

```sh
sec list
sec find android
sec find 'sdk license'
sec show android.sdk.validate
sec explain git.status
sec run git.status --dry-run
sec run environment.path
sec doctor --json
sec recipes
sec recipe show android-dev
sec recipe run git-review --dry-run
sec history
sec receipt RECEIPT_ID --json
```

Twenty registered operations cover Git/GitHub, ADB/Fastboot, SDK inspection, PATH analysis, runtimes,
Termux boundaries, Debian package queries, SSH, local model runtime detection, network interfaces,
disk and host context. They inspect rather than installing packages or guessing fixes. Five recipes
compose those operations into preparation/diagnostic workflows and stop on failure. They do not
perform an automatic environment bootstrap. The [catalog](docs/catalog.md) is generated from the
same metadata used for execution and search.

`list`, `find`, `show`, `explain`, `doctor`, operation execution, recipes, history and receipts support
`--json`. Diagnostic commands can succeed while individual checks report WARN, UNKNOWN or UNTESTED.
Tool presence is evidence of a found executable, never a connected or qualified device.

## 1337 mode

```sh
sec 1337
```

The console offers described categories, real host/tool detection, metadata-derived operation
context, prerequisites, explain, run and dry-run actions, recipe execution, search and filtered
archaeology. Recovery Lab has its own command prompt using the same CLI handlers. Plain text works
without Unicode frames or terminal libraries. Color is optional (`NO_COLOR` disables it). Without a
TTY it prints a useful menu preview and exits; normal CLI operations never require a TTY.

## Recovery Lab

```sh
sec recovery doctor --json
sec recovery inspect recovery.img --json
sec recovery inspect --device
sec recovery tree audit /path/to/device/tree --json
sec recovery init --help
sec recovery configure
sec recovery sync --dry-run
sec recovery build --dry-run
sec recovery verify recovery.img
sec recovery test recovery.img --device MY_DEVICE
sec recovery report recovery.img --device MY_DEVICE --markdown
```

The tree auditor identifies local architecture/product declarations, fstab, kernel references,
slots, dynamic partitions, recovery/vendor_boot arrangements and crypto declarations. External make
expansion stays UNRESOLVED. Image inspection hashes the file and recognizes Android boot/vendor_boot
headers; it does not unpack ramdisks, validate AVB or certify compatibility.

Workspaces require explicit manifest, revision, tree, lunch product and build target. Sync and build
use at most two jobs and refuse concurrent workspace mutations. Builds collect actual new images,
hashes, source locks, audit evidence, bounded logs and receipts. A successful compile means
**BUILD SUCCESS**, with hardware still **UNTESTED**. Qualification records manual evidence against
an artifact hash and a specific device; reports include failures and untested areas.

| Capability | Release status |
|---|---|
| Registry, CLI, receipts, doctor, console, recipes, archaeology | IMPLEMENTED; locally tested |
| Static tree audit | IMPLEMENTED; heuristic evidence, unresolved external dependencies |
| Image inspection | IMPLEMENTED; partial header inspection only |
| ADB device properties | ENVIRONMENT/HARDWARE-DEPENDENT; no root requested |
| TWRP source sync and build orchestration | EXPERIMENTAL; fixture-tested, real build blocked on this host |
| Actual TWRP compilation and device qualification | UNTESTED |
| Temporary boot | Safety refusal implemented; execution PLANNED pending reliable support checks |
| Permanent flashing, unlocking and wiping | Not implemented |
| Shell completion, multiple workspaces, full ramdisk/AVB inspection | PLANNED |

Read [Recovery Lab](docs/recovery-lab.md) for current upstream references, explicit workspace examples
and limitations. Historical TWRP notes are lineage, never current build authority.

## Lineage without leaking history

The historical archive was inventoried in place: **153 files, 27 duplicate members**. Final decisions:
**8 EXTRACT · 41 ARCHIVE · 69 REJECT · 35 SECRET · 0 PROMOTE**. Eight safe sources inspired rewritten
operations; no historical file contents were imported. Secret-bearing entries have opaque names.
Rejected material includes separate projects, duplicates and ownership-bypass/offensive intent.

```sh
sec archaeology --json
sec ingest /private/legacy.zip --output /private/inventory.json
sec scan path/to/file
```

The [archaeology workflow](docs/archaeology.md) bounds archive processing and separates automatic
classification from explicit human/technical review. [Provenance](docs/provenance.md) connects
source hashes and duplicate groups to modern replacements and verification evidence.

## Safety and receipts

The four risk classes have different enforcement: READ_ONLY inspects; MUTATING describes writes;
PRIVILEGED requires explicit privileges without elevation; DESTRUCTIVE requires a terminal and a
specific confirmation phrase. Recipes use the same guards. No destructive production operation ships.
`sec recovery boot` refuses unresolved support; `clean` explains scope without deleting anything.

The runner uses argument vectors. The only shell program is a fixed TWRP adapter for upstream shell
functions, with product/target passed as arguments. Secret-like arguments are refused; outputs and
receipts are sanitized. Pattern scanning is deliberately conservative and cannot replace review.
Read [SECURITY.md](SECURITY.md) before sharing execution evidence.

Receipts answer “what did that script just do?” with commands, sanitized arguments/output, exit codes,
duration, effects, preconditions, result and artifacts. Canonical storage is private local JSON.
Failures leave receipts too. `history` lists evidence; `receipt` renders human or JSON output.

Configuration precedence: explicit command arguments define a recovery workspace; `SECRIPTS_DATA_HOME`
overrides the XDG data root, then `XDG_DATA_HOME/secripts`, then `~/.local/share/secripts`. SDK discovery
uses `ANDROID_HOME` then `ANDROID_SDK_ROOT`, reporting conflicting roots. Basic commands need no config.
Runtime receipts, workspaces and build evidence stay outside this Git repository. Config stores no
credentials. This release has one workspace configuration, inspectable with `sec recovery configure`.

Exit codes: **0** success, **1** operation/state failure, **2** invalid usage, **3** prerequisite missing,
**4** safety refusal, **5** unsupported host/backend, **130** interrupted. Individual diagnostic states
remain authoritative; an exit code of zero is not hardware qualification.

## Prove changes

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest -q
python tools/secret_scan.py
python -m build
```

The suite tests failure paths, safety refusals, argv handling, sanitized receipts, duplicate/secret
legacy members, image bounds, tree uncertainty, sync/build failure and manual qualification states.
Tests never download Android sources or touch real devices. CI runs the same stack on Linux; external
CI status is distinct from local validation. See [verification evidence](docs/verification.md),
[architecture](docs/architecture.md), [safety](docs/safety-model.md) and [contributing](CONTRIBUTING.md).
