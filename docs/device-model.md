# Recovery Device Model and build planning

Models are local JSON evidence ledgers, not a device database or compatibility score.
They live under `$SECRIPTS_DATA_HOME/recovery/devices` (or the normal XDG data root).
Names are restricted lowercase identifiers. Source paths/hashes and fact locations
remain traceable; sharing local exports requires privacy review.

```sh
js recovery device create example
js recovery device add-image example boot /path/to/boot.img
js recovery device add-image example vendor_boot /path/to/vendor_boot.img
js recovery device add-tree example /path/to/tree
js recovery device add-metadata example /path/to/metadata.json
js recovery device inspect example --json
js recovery device report example --json
js recovery tree diagnose /path/to/tree --json
js recovery tree derive --device example --output /existing/parent/new-candidate
js recovery plan example --json
```

`add-metadata` accepts a small allowlisted JSON object, for example
`{"architecture":"arm64","codename":"example"}`. These are USER_SUPPLIED facts,
not independent observations. No arbitrary Make configuration is accepted.
Image roles are operator labels; labeling a file recovery does not prove a partition.
Sources are hash snapshots. A changed source must be deliberately re-added; the ledger
does not silently reinterpret an old observation.

Significant facts preserve value, state, source, location and reason. States are
OBSERVED, DECLARED, DERIVED, INFERRED, USER_SUPPLIED, UNKNOWN and CONFLICT. Exclusive
facts that disagree remain CONFLICT with all evidence visible. Compatible multi-valued
collections (compression, different image header generations, dependencies, fstab and
encryption indicators) are retained together. Consensus does not upgrade confidence.
A model's status remains PARTIAL even without conflict; hardware stays UNTESTED.

Image observations include headers/kernel regions, architecture markers when known,
ramdisk fstab/flags, vendor fragment types, DTB/DTBO and AVB presence. Static tree
facts cover direct architecture/identity and recovery/partition declarations. Not every
possible model field is automatically inferred; unknown is an intentional result.
Connected-device evidence is not automatically imported into the model; saved device
dossiers can still enter the existing artifact qualification report explicitly.

## Candidate derivation

Derivation requires unambiguous supported architecture evidence and a safe codename
(or explicit model-name fallback). It creates a **new** directory and refuses existing
paths. Images, source trees and devices remain untouched. Every generated configuration
line has a candidate manifest entry with source evidence/reason and review-required state.
Local generated relationships are identified as such, rather than claiming firmware
provenance. The banner itself is not a generated configuration value.

Output: BoardConfig.mk, AndroidProducts.mk, twrp_NAME.mk, device.mk, recovery.fstab,
candidate.json and REVIEW.md. Unsupported settings, kernel dependencies, encryption
flags, partition sizes and block-device paths are not invented. Fstab is preserved from unambiguous safe source declarations where available; missing or conflicting paths remain unresolved. This is a review scaffold, **not a build-ready tree**.

## Build planner

The planner correlates model conflicts, configured workspace/tree, bounded manifest
metadata, host architecture/RAM/free disk, repo/tool observations and static dependencies.
Independent recovery features select a multi-output dependency graph. Dedicated, boot,
vendor_boot and init_boot relationships may coexist. Presence alone does not schedule outputs.
The legacy single-target projection returns UNKNOWN for multiple outputs/conflicts.
Android version alone never selects a target or JDK.

Every blocker gives a reason. The current backend's non-x86_64 path is unqualified;
40 GiB free/8 GiB RAM are conservative planning floors, not promises of build capacity.
Filesystem semantics remain UNKNOWN without a deliberate qualification probe. Even an
apparently suitable host remains HOST_UNTESTED until qualified. Planning never syncs,
compiles, boots or flashes. It writes a sanitized receipt, and a successful invocation
can correctly contain a BLOCKED build plan.

Product prefixes `omni_` and `twrp_` are generation hints, not proof of Android base.
Local Make analysis resolves only bounded simple earlier literal variables, LOCAL_DIR,
append/default declarations and explicit paths. Conditional/external/dynamic Make
expansion remains unresolved. Source manifest selections and default revisions are
reported as declarations; no complete GNU Make or repo manifest evaluator is claimed.

## Phase 4 artifact interfaces

Recovery Device Models use schema 2. Schema 1 records are adapted in memory without rewriting;
new evidence mutations save schema 2. Compatible legacy arrangements become a collection.
New canonical image, ramdisk, DTBO, AVB and comparison models use explicit schema 1 interfaces
and hashes. Device identity, image format and contextual partition role remain separate.
Use `js ry dce`/`js recovery device` interchangeably. Image workspaces and round-trip results
are offline artifact evidence, not a device qualification import or a new automatic trust score.
See [workspaces](image-workspaces.md), [comparison](roundtrip.md), [CLI aliases](cli.md).

See [configuration](RECOVERY-CONFIGURATION.md) for layers, graphs and source constraints.
