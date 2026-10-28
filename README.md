# JADIS // SECRIPTS

**Personal Developer Operations Arsenal & Android Recovery/Image Laboratory**

**CLI: `js` · Cockpit: `js 1337` · Recovery Lab: `js ry` · Image Lab: `js img`**

Christopher Osburn / JADIS's independent personal developer arsenal turns scattered commands,
notes and recovery research into typed, inspectable operations. This private project coexists
with Outer Void tooling; it is not that ecosystem's universal CLI or control plane.

> Build the system. Prove the system. Then remove the scaffolding.

## Install

Python 3.11+; Linux/Termux execution paths. Interpreter tests do not qualify every PRoot host or
Android device. Runtime dependencies are Python's standard library; external providers are optional.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
js --help
js --version
js doc
js dos
js 1337
```

Alternatively use `pipx install .`. Distribution: `jadis-secripts`; Python package: `secripts`;
sole executable: `js`. The old pre-0.2 executable is not installed. Existing system Node `js`
commands are preserved; put the project environment/pipx application directory first on PATH.

## Short working names, descriptive aliases

```sh
js ls                              # also: js list
js fd android                      # also: js find android
js sh android.sdk.validate         # also: js show ...
js exp image.roundtrip             # also: js explain ...
js doc --json                      # also: js doctor --json
js dos --json                      # also: js dossier --json
js hist --failed --limit 10         # also: js history ...
js rcpt latest                     # also: js receipt latest / js receipts latest
js rcp sh python-dev               # also: js recipe show python-dev
js ry doc                          # also: js recovery doctor
```

Aliases are first-class metadata, normalized before guarded execution. Operation IDs remain stable;
`image.inspect` is still `image.inspect`. The [complete CLI map](docs/cli.md) documents every spelling,
nested alias, collision check and convenience route. `js 1337` remains permanent.

## Everyday developer operations

**87 operations across 22 categories; 26 recipes.** The [generated catalog](docs/catalog.md) drives
search, explanations, cockpit context and execution. Discover by ID, title, tags, category or risk:

```sh
js fd 'device tree'
js fd --category git
js fd --risk READ_ONLY
js run git.health
js run python.project
js run java.environment
js run android.sdk.validate
js run git.status --dry-run
js rcps
js rcp run git-review --dry-run
js rcp run python-dev
```

Git/GitHub inspections cover repository health, divergence, changes, worktrees, history and explicit
read-only network queries. Python/JVM/SDK inspections report actual versions/components and conflicts
without installations or license acceptance. Termux/Linux/PRoot, filesystem, SSH, local networking and
model tooling remain bounded diagnostics. No filesystem-wide model search or network scanning occurs.

Doctor reports individual PASS/WARN/FAIL/UNKNOWN/UNTESTED/BLOCKED states and remediation. Dossier combines
local evidence without network calls; transport enumeration is explicit with `--devices`. Neither a
successful invocation nor a tool's presence qualifies the environment or hardware.

## Image engineering — 0.4.0

```sh
js insp /path/to/boot.img --json
js img model /path/to/boot.img --json
js img upk /path/to/boot.img --output /existing/parent/workspace
js img ws /existing/parent/workspace
js img rb /existing/parent/workspace --output /existing/parent/rebuilt.img
js img cmp /path/to/boot.img /existing/parent/rebuilt.img --json
js img rt /path/to/boot.img --json
js prov
js img prov --probe
```

The shared engine identifies content, parses bounded structures, extracts controlled components,
models them, reconstructs supported layouts and compares independently demonstrated properties.
No payload executes. Sources become read-only hash-checked snapshots. Outputs must be new; existing
files/directories, source overwrite and ambiguous edits are refused.

Android boot v0–v2 support exact-layout reconstruction. Boot v3/v4 and vendor_boot v3/v4 additionally
support constrained unsigned component resizing. Headers, addresses, command-line bytes, OS metadata,
fragments/board IDs, DTB, bootconfig, padding and opaque trailers are preserved in the workspace.
Signed/AVB-bearing modifications are refused. Whole-blob v4 resizing requires explicit fragment mapping.

Round trips report byte, structure, component, metadata and semantic equivalence separately. Two corpus
recovery test images and seven current-AOSP-generated boot/vendor_boot cases rebuilt byte-identically.
That evidence is **not stock-device compatibility or bootability**. See [Image Intelligence](docs/image-intelligence.md),
[workspaces](docs/image-workspaces.md), [round-trip semantics](docs/roundtrip.md) and [verification](docs/verification.md).

## Ramdisks, DTB/DTBO and AVB

```sh
js ram insp /path/to/ramdisk.lz4 --json
js ram ext /path/to/ramdisk.lz4 --output /existing/parent/ramdisk-workspace
js ram pack /existing/parent/ramdisk-workspace --output /existing/parent/ramdisk.gz --compression gzip
js ram cmp /path/to/ramdisk.lz4 /existing/parent/ramdisk.gz --json
js dtbo insp /path/to/dtbo.img --json
js dtbo ext /path/to/dtbo.img --output /existing/parent/dtbo-workspace
js dtbo rb /existing/parent/dtbo-workspace --output /existing/parent/rebuilt-dtbo.img
js avb insp /path/to/vbmeta.img --json
js avb vfy /path/to/vbmeta.img --key /path/to/expected-public.pem --json
```

Native LZ4 decodes compressed/uncompressed, dependent/independent blocks, concatenated/skippable and
legacy streams with output limits and standard-frame XXH32 checksum validation. Dictionary-dependent
streams stop as BLOCKED_MISSING_DICTIONARY. Its deterministic encoder emits uncompressed blocks.
Gzip supports concatenated members and checksum checks; zlib and contextual raw DEFLATE reuse stdlib.

CPIO newc/CRC models preserve order, owners, modes, timestamps, links and device metadata. Extraction is
a **virtual payload workspace**: archive paths never become host write paths; links and special files
remain metadata. Sensitive paths/content are refused. Directory packing is deliberately normalized;
workspace packing preserves supported entry metadata. [Ramdisk contracts](docs/ramdisk.md).

DTB/FIT inspection includes canonical property hashes, reserve maps, configurations and embedded FIT
hash checks. DTBO v0/v1 handles shared blobs, documented gzip/zlib flags and canonical reconstruction.
Unknown compression, extended table layouts and arbitrary vendor binding semantics remain limited.

AVB parsing and native hash checks are separate from explicit optional `avbtool` verification.
Signature mathematics, expected-key match, hash/hashtree evidence and vbmeta digest are independent.
Chained verification, FEC, device rollback enforcement and root-of-trust qualification remain unverified.
No homemade RSA, signing-key extraction or AVB bypass is provided. [AVB trust model](docs/avb.md).

## Recovery Device Models and planning

```sh
js ry dce create example
js ry dce add-image example boot /path/to/boot.img
js ry dce add-tree example /path/to/tree
js ry dce report example --json
js ry tree diag /path/to/tree
js ry tree derive --device example --output /existing/parent/candidate
js ry plan example --json
```

Models retain source-linked OBSERVED/DECLARED/DERIVED/INFERRED/USER_SUPPLIED/UNKNOWN/CONFLICT evidence.
Tree analysis never executes Makefiles. Candidate configuration has per-line provenance and unresolved
TODOs; it is not build-ready. Planning explains host/source/kernel/common/vendor blockers without a sync
or compilation. Actual TWRP compilation remains blocked on this host; hardware qualification is UNTESTED.
[Device models](docs/device-model.md) and [Recovery Lab](docs/recovery-lab.md).

Existing `js dce`/`js device` interfaces retain explicit read-only ADB/Fastboot inspection. Serial-like
identifiers are masked. No flashing, unlocking, wiping, root installation or automatic device boot occurs.

## Cockpit, receipts and lineage

`js 1337` shows real host/tool/repository/Recovery/Image Lab evidence and described operations. INSP,
IMG, RAM, RY, DOC, DOS, RCP and HIST shortcuts route to the same CLI contracts. NO_COLOR and non-TTY/JSON
previews remain available. Destructive hardware qualification is never inferred from a dashboard.

```sh
js hist --operation image.roundtrip --limit 20 --summary
js rcpt latest
js rcpt diff FIRST_ID SECOND_ID --json
js comp bash > ~/.config/js-completion.bash
js arch --json
```

Receipts retain sanitized commands, hashes, effects, outcomes and association. New nested evidence is
bounded; truncation is explicit. Raw firmware bodies and signing keys are not receipts. Existing
receipts remain readable, regardless of invocation spelling. Completion performs no probes.

Original legacy lineage remains metadata-only. Phase 4 reused the Phase 3 inventory for targeted
follow-up instead of rescanning everything. Research archives, upstream fixtures, private keys and
firmware images are not repository contents. [Research and fixture provenance](docs/research.md).

## Safety and development

READ_ONLY inspects. MUTATING explains filesystem writes and supports preview. PRIVILEGED never silently
elevates. DESTRUCTIVE requires deliberate identity confirmation; no destructive production operation
ships. Recipes use those same contracts. Pattern scanning does not replace privacy review before sharing.

Runtime state uses `SECRIPTS_DATA_HOME`, otherwise `$XDG_DATA_HOME/secripts`, otherwise
`~/.local/share/secripts`. Artifact workspaces are explicit user-selected new paths. No runtime database
or repository-local receipts are required. Exit codes: 0 invocation success, 1 failure, 2 usage,
3 missing prerequisite, 4 safety refusal, 5 unsupported capability, 130 interrupted.

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest -q
python tools/secret_scan.py
python tools/audit_docs.py
python -m build
```

Optional maintained-source validation is explicit: `python tools/validate_oracles.py --fetch-upstream`.
It retrieves only three small hash-pinned AOSP sources. Ordinary commands and unit tests never sync
Android source trees. CI uses a serial Python matrix and pinned optional verification providers.

The evidence law is permanent: parsing is not verification; structural validity is not authenticity;
round-trip equivalence is not compatibility; compatibility is not bootability; compilation and bootability
are not hardware qualification.

## Credits and attribution

[CREDITS.md](CREDITS.md) identifies material projects, specifications, people and research influences.
[Detailed provenance](docs/provenance.md) remains authoritative for per-capability lineage. Attribution
and license review are implementation requirements; credits never replace required license notices.
