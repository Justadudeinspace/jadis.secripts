# Architecture

Project identity: JADIS // SECRIPTS. Distribution: jadis-secripts. Python package: secripts.
Canonical launcher: js. Cockpit: js 1337. No compatibility launcher is installed.
This is an independent personal project, not an Outer Void router or control plane.

The existing typed registry remains the contract for operations, ranked discovery, explanations,
completion, generated catalog and cockpit context. Parameter contracts allow only device, tree and
artifact selectors; arbitrary argv/shell forwarding is absent. The dispatcher validates parameters,
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
