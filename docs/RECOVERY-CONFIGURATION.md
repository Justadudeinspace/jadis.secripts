# Recovery configuration and composite architectures

Recovery engineering works without AI, API credits or an AI network connection.
A Device Model is evidence. A build configuration is a choice. They are not interchangeable.

## Independent relationships

Model schema 2 stores independent recovery features, artifact observations and AVB edges.
It reads schema 1 records without rewriting them. The old `recovery_arrangement` field
is a compatibility collection; it no longer selects one exclusive architecture.

| Example | Relevant relationships | Candidate outputs |
|---|---|---|
| Dedicated recovery | recovery contains kernel and ramdisk | recoveryimage |
| Dedicated recovery using boot kernel | boot supplies kernel to recovery; exclusion declared | recoveryimage; boot is a required input, not automatically rebuilt |
| Recovery-as-boot | recovery resources in boot | bootimage |
| Vendor recovery | GKI context plus recovery resources in vendor_boot | vendorbootimage |
| init_boot-aware | generic ramdisk in init_boot, vendor resources separately | Presence alone schedules no initbootimage |
| Dedicated plus boot/init_boot/vendor_boot | retain every artifact; locate resources independently | Only justified outputs; may be multiple |
| AVB chained device | observed descriptor edges connect vbmeta partitions and covered images | AVB references are not instructions to rebuild or flash |

These are examples, not an exhaustive enum. Header versions describe the image whose
header was parsed; filenames/roles remain operator-supplied context. Init_boot recovery
output requires independently established source support. TeamWin 12.1 is not assumed
to provide modern initbootimage support. No flash/install plan is generated.

```sh
js ry graph example --json
js ry status example --json
js ry flags example --json
js ry flags ls example --json
js ry flags sh example BOARD_USES_RECOVERY_AS_BOOT --json
```

## Typed flags and expert choices

Known booleans, sizes, header/page values, source-relative paths and literal text have
bounded validators. Make expansion and shell syntax are refused in overrides. Defaults
are applied only for a selected known source generation; unspecified conditional build
behavior stays unknown. Read-only AVB signing/rollback declarations can be inspected but
cannot be edited through this interface. No private keys are imported.

Precedence: USER_OVERRIDE, direct/static source declaration, derived evidence, documented
source-generation default, UNKNOWN. Each layer remains visible. Conditional declarations
are not evaluated as GNU Make. Positive image size is not a partition-size measurement.

```sh
js ry flags set example BOARD_KERNEL_PAGESIZE 4096 --reason 'Reviewed image header'
js ry flags unset example BOARD_KERNEL_PAGESIZE --acknowledge-conflict
js ry flags reset example BOARD_KERNEL_PAGESIZE
js ry flags diff example --json
js ry flags validate example --json
js ry flags export example --format make --output /existing/parent/BoardConfig.review.mk
js ry flags export example --output /existing/parent/flags.json
js ry flags import example /path/to/flags.json
```

`unset` records an explicit removal (false/empty for booleans, `undefine` for other
Make exports). `reset` removes the override and returns to underlying evidence/defaults.
Conflicting writes require `--acknowledge-conflict`. This acknowledges storage of a
choice, never validates it. History records timestamp, previous value and developer note.
Exports refuse overwrites. Flags/history/profiles live in private XDG state outside Git.

```sh
js ry flags profile save example reviewed
js ry flags profile ls
js ry flags profile diff example reviewed --json
js ry flags profile apply example reviewed
```

Profiles contain overrides, not secrets or evidence. Imports preflight every entry before
writing. Rollback/signing edits remain protected. Unreviewed/external source applicability
is unresolved. Recognized rules reject contradictory recovery-as-boot/vendor resource
flags, missing GKI/boot-kernel context, unsupported generations and suppressed dependencies.
A validation PASS means only the implemented rules found no findings; it is not Make,
source completeness, bootability, decryption or device qualification.

## Dependencies and source selection

A reviewed lock contains schema 1, dependencies with unique ID, role, canonical GitHub
HTTPS repository, full commit and distinct safe relative destination, plus optional source
manifest/generation/commit/lunch. The packaged `reference-a51.json` is an investigated
example, not a complete transitive Android source lock or universal recommendation.

```sh
js ry source resolve example --lock /path/to/reviewed-lock.json --json
js ry source example --json
js ry deps resolve example --root /outside/git/checkout --dry-run --json
js ry deps resolve example --root /outside/git/checkout --fetch --json
js ry deps graph example --json
js ry deps validate example --json
```

Acquisition is sequential, shallow and explicitly opted in. Existing destinations and
symlinks are refused; no submodules, hooks or downloaded source scripts execute. There
is a 2 GiB download floor, not a promise of sufficient Android build space. Selected
repositories are checked for exact commit and cleanliness. Unresolved static references
and complete repo-manifest pinning remain separate obligations.

## Tree, fstab and build binding

Candidate generation exports safe effective flags, provenance, reviewed dependencies,
manifest snippet and fstab declarations where unambiguous. Android and TWRP fstab forms
retain their original ordering/flags. Conflicting mounts generate no guessed table.
Block paths, sizes and encryption support are never invented. Candidate files still need
source-generation/common/vendor/kernel review. No stock image or source tree is modified.

A configured workspace accepts repeated `--target` options and optional `--model` binding.
With a model binding, the build preflight compares outputs, pinned source, dependencies,
host, validation and actual tree declarations. An unapplied override blocks compilation.
Apply reviewed Make exports deliberately; storing choices does not edit a checkout.
Legacy unbound workspaces remain supported but cannot claim this complete input chain.
All requested outputs must be freshly generated before BUILD_SUCCESS is recorded.
Build logs/source locks/hashes and model-bound inspection reports enter local receipts.
Hardware stays UNTESTED. Even byte-identical rebuilt artifacts do not prove compatibility.

## Current live reference evidence

The [A51 evidence record](research/phase6-a51-evidence.json) identifies the exact official
TeamWin tree revision and real prebuilt input hashes. Kernel identification is PARTIAL;
DTB/DTBO structural parsing passed. These are upstream inputs, not locally compiled outputs.
The tree's dependency-suppression declaration is a real review blocker. Stock firmware
build/hashes and the complete transitive source manifest are unacquired. This ARM64 host
has insufficient disk/RAM and no qualified build route. Real compilation is BLOCKED;
there are no generated recovery images and no hardware qualification.
