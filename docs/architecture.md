# Architecture

The registry is the operation contract. CLI, console, search and generated catalog consume it.
The dispatcher checks platform and tool preconditions, calls shared risk enforcement, invokes
argument-vector subprocesses and persists a receipt even for failed preconditions. Recipes invoke
the same dispatcher and stop on failure. They cannot bypass safety.

The runner uses no `shell=True`. TWRP requires upstream shell functions; a fixed Bash program sources
a trusted checkout and passes validated lunch/target values as positional arguments. Builds use
`-j2`; source sync uses `-j2`. No subprocess runs at normal help startup. Captures are file-backed,
time-limited and truncated to 128 KiB per stream before sanitization. Timeout kills the process group.

Recovery is a separate subsystem with a backend protocol and one real implementation, TWRP.
Inspection is static. Workspace config separates source checkout, explicit product/target and
runtime evidence. A compile result never changes manual qualification states.

Runtime state lives in `$SECRIPTS_DATA_HOME` or `$XDG_DATA_HOME/secripts` (default
`~/.local/share/secripts`). Receipts and JSON state use atomic replace and mode 0600. Parent state
directories are created with mode 0700. Keep this directory private. There is one configured recovery
workspace in this release. Multiple-workspace selection and shell completion are future work.
