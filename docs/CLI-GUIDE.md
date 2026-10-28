# CLI guide

Short commands are the working interface; long names are the descriptive interface.
Both use one authoritative naming contract and normalize before risk enforcement.

The [complete command reference](COMMAND-REFERENCE.md) documents every root command,
nested parser, positional argument, option, default and accepted choice. The generated
[alias map](cli.md) includes actions implemented as positional choices.

## Daily sequence

```sh
js ls
js fd recovery
js sh image.roundtrip
js exp image.roundtrip
js run image.roundtrip --artifact IMAGE --dry-run
js hist --summary --limit 10
js rcpt latest --json
```

Replace IMAGE with an actual file before execution. `run` is registry execution; it is
not arbitrary shell routing. Discovery searches IDs/titles/tags/categories and provenance.
`js help image`, `js help recovery`, `js help device`, `js help evidence` and `js help ai`
provide orientation. `--help` supplies parser syntax without probes or network access.

## Outputs, failures and safety

`--json` emits uncolored data where documented. Exit 0 means the invocation completed,
not every diagnosis passed. Exit 1 is operation failure, 2 usage, 3 prerequisite,
4 safety refusal, 5 unsupported environment; interruption returns 130.

READ_ONLY operations inspect. MUTATING operations explain their effect and support
contract dry-runs. PRIVILEGED never silently elevates. DESTRUCTIVE requires the shared
explicit guard; Phase 5 adds no destructive operations. Help/metadata listing does not
write execution receipts. Registry runs and significant artifact/guidance actions do.

Common failures: unknown operation (`js fd`), missing tool (`js doc`), ambiguous transport
(explicit `--device`), existing output (choose a new path), unresolved model (collect
evidence), blocked build (inspect plan), absent AI key (configure privately). Never
resolve a blocker by inventing a PASS. Receipts retain stable IDs through aliases.

## Completion and configuration

```sh
js comp bash
js comp candidates img
```

Save/source the generated Bash definition in your own shell configuration. Completion
queries parser metadata without device/network probes. Runtime state uses
SECRIPTS_DATA_HOME, otherwise XDG_DATA_HOME/secripts, otherwise ~/.local/share/secripts.
AI credentials are environment references, never stored configuration or CLI operands.

Related: [operations](catalog.md), [recipes](RECIPES.md), [cockpit](COCKPIT.md),
[evidence](RECEIPTS-EVIDENCE.md), [safety](safety-model.md).
