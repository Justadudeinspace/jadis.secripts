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
flags, partition sizes and block-device paths are not invented. Fstab is deliberately
a TODO until reviewed. This is a review scaffold, **not a build-ready tree**.

## Build planner

The planner correlates model conflicts, configured workspace/tree, bounded manifest
metadata, host architecture/RAM/free disk, repo/tool observations and static dependencies.
Candidate targets derive from explicit recovery arrangements: dedicated→recoveryimage,
recovery-as-boot→bootimage, vendor_boot→vendorbootimage. A conflict/absence returns UNKNOWN.
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
