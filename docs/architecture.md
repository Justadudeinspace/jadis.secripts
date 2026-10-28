# Architecture

Project identity: JADIS // SECRIPTS. Distribution: jadis-secripts. Python package: secripts.
Canonical launcher: js. Cockpit: js 1337. No compatibility launcher is installed.
This is an independent personal project, not an Outer Void router or control plane.

The existing typed registry remains the contract for operations, ranked discovery, explanations,
completion, generated catalog and cockpit context. Parameter contracts allow explicit device, tree, artifact, workspace, output, comparison and
verification selectors; arbitrary argv/shell forwarding is absent. The dispatcher validates parameters,
platform/tool preconditions and risk before invoking an allowlisted handler. New operations extend
that dispatcher rather than creating a competing execution framework.

Evidence collectors capture argument-vector commands and preserve individual observation states.
Invocation result and diagnostic status are separate: a successfully collected dossier may contain
WARN, UNKNOWN, UNTESTED, BLOCKED or UNSUPPORTED. Device collectors enforce time budgets and mask
transport identifiers before evidence reaches receipts. Subprocess timeout/interruption kills its group.

Doctor and dossier reuse inspections. Dossier makes no network calls; detailed Java probing and device
interrogation are explicit operations. Cockpit starts with a compact snapshot; non-TTY/JSON snapshots
do not enumerate devices. Interactive enumeration is bounded and never qualifies hardware.

Recipes compose contracts, validate their parameter union and require explicit permission for network
steps. Parent receipts link step receipts and retain partial evidence. Local JSON receipts support
filters, latest/failed, artifact lookup and comparison. Cwd/interpreter/architecture association aids
comparison without promising replay. History currently scans JSON files linearly; no database/index.

Recovery keeps its backend protocol and TWRP implementation. Static tree graphs are bounded and do not
evaluate Make. Image/AVB parsing is native and bounded; decoded CPIO metadata is never extracted.
Reports separate current workspace/tree observations from recorded build inputs and manual hardware
attestations. Only the existing fixed trusted-checkout Bash adapter executes upstream shell functions.

Runtime paths remain unchanged by the launcher migration: `$SECRIPTS_DATA_HOME`, otherwise
`$XDG_DATA_HOME/secripts`, otherwise `~/.local/share/secripts`. JSON uses atomic replacement and 0600;
new state directories use 0700. Build artifacts and logs stay outside Git. One configured recovery
workspace remains supported; multiple-workspace selection is future work. Runtime dependencies remain
standard-library-only. Bash completion dynamically queries candidates and never probes devices/services.

## Phase 3 image and evidence architecture

`secripts.images` is independent of TWRP: common bounds/hash readers, content identification,
Android containers, compression/CPIO, FDT/DTBO, ELF/uImage/vendor markers, AVB and optional
providers. Recovery compatibility modules preserve existing consumers. Native content results
are cached by SHA-256/parser version; external evidence is explicit and per-invocation.

`recovery.model` stores source-linked local JSON facts with conflict detection; `recovery.planner`
correlates those facts with static trees, manifest metadata and host constraints. Candidate
derivation is a guarded local MUTATING operation with line provenance and no build-ready claim.
New registry operations and recipes reuse the existing safety/receipt path. Model-management
commands add structured source evidence, not arbitrary shell commands.

See [Image Intelligence](image-intelligence.md), [Device Models](device-model.md),
[research](research.md) and [credits](../CREDITS.md).

## Phase 4 reconstruction and streamlined CLI

`commands.CommandName` owns canonical shorthand and accepted aliases. Scoped parser construction
rejects collisions. Parsing normalizes spellings before authorization/dispatch. Operation IDs
remain stable; recipes use those IDs, and receipts do not depend on launcher spelling. Completion,
generated CLI maps and cockpit shortcuts consume the naming contracts. No shell alias/router exists.

`images.codecs/lz4codec/cpio` form the reusable compression/ramdisk pipeline. `ramdisk_model`,
`bootmodel`, `dtbo_model`, `artifacts`, `comparison` and `workflows` manage bounded versioned models,
private workspaces, exclusive writes and independent equivalence states. `avbmodel` separates native
metadata/hashes from explicit upstream cryptographic providers. `oracles` quarantines exact pinned
AOSP source for differential validation. No payload executes and no artifact feature accesses devices.

New nested receipt evidence is sanitized and budgeted while historical receipts remain readable.
Source hashes and provenance are not substitutes for trusted-key or hardware qualification.
See [CLI map](cli.md), [roundtrip](roundtrip.md), [ramdisk](ramdisk.md) and [AVB](avb.md).
