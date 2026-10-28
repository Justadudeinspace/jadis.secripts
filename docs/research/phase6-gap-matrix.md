# Phase 6 audit and design gate

Recorded before implementation. Baseline main: 2ae5c69552385d57453fd9e8fcf5689a014689e5,
private, clean, installed js 0.5.0, 92 operations / 23 categories / 28 recipes.
The complete baseline gate passed 364 tests, Ruff, formatting, secret scan, docs and build.

| Blocker | Classification | Planned deterministic work |
|---|---|---|
| Exclusive recovery_arrangement loses compatible resources | MISSING IMPLEMENTATION | Versioned atomic architecture facts and artifact/dependency graph; preserve legacy readers without using exclusive field for decisions |
| Single target backend/configuration | MISSING IMPLEMENTATION | Multi-output explicit targets; source applicability and output reasons; never infer flash targets |
| No typed flag overrides/profiles | MISSING IMPLEMENTATION | Typed catalog, source-linked observations, derived/default/override layers, history, validation, guarded import/export |
| Fstab retains only mount names | MISSING IMPLEMENTATION | Structured source/mount/type/options/slot/encryption facts; preserve conflicts, no path guessing |
| Dependency paths are unresolved strings | MISSING DEPENDENCY | Reviewed HTTPS repository/commit/path lock, explicit bounded sequential acquisition and checkout validation |
| Source branch and transitive revisions not acquired | MISSING SOURCE | Pin source manifest/tree/core repositories; resolved repo manifest required on qualified build host |
| Candidate scaffold ignores available safe flags | MISSING DEVICE CONFIGURATION | Generate reviewed safe values and provenance; retain unresolved kernel/fstab only when truly missing |
| Current local ARM64 host, ~29.8 GiB free / ~5.3 GiB RAM | MISSING HOST CAPABILITY / UNSUPPORTED ARCHITECTURE | Keep host gate; prepare external x86_64 Linux build contract |
| No SSH configuration, no self-hosted runners | MISSING HOST CAPABILITY | Asked for an existing host; continue local deterministic work |
| Codespaces API denied; billing API inaccessible | MISSING EVIDENCE | Do not create paid infrastructure or assume free Actions allowance |
| Stock images/build identity not yet acquired | MISSING EVIDENCE / LICENSING LIMIT | Target public upstream strategy, record missing stock hashes explicitly; no downloaded recovery presented as compilation |
| Real device unavailable | HARDWARE-ONLY QUALIFICATION | Hardware remains UNTESTED; no device mutation |

## Research and target decision

[Primary sources](phase6-sources.json) include current AOSP generic boot/vendor_boot,
AVB, main build configuration and the actual TeamWin Android 12.1 build files.
They explicitly permit composite dedicated/boot/init_boot/vendor_boot arrangements.
TWRP 12.1 does not establish init_boot target support; do not assume it from modern
AOSP documentation. Boolean board flags use true/empty, not a blanket false string.

Selected reference candidate: Samsung Galaxy A51 SM-A515F (a51), Exynos9611.
Official TeamWin tree is pinned at d6d2a9d69f2b77bd63161618f859ef0d65e23a31,
manifest at 6dc117d9cbd08430daa16db2013560e1c4017fa8. It declares dedicated recovery,
boot, DTBO, dynamic partitions and a self-contained prebuilt kernel/DTB strategy.
OnePlus guacamole was compared but adds common/vendor dependencies and firmware
variant constraints; a51 is the smaller proving target. Upstream suppression of
missing dependencies is recorded as a review issue, never silently adopted.

The current host is genuinely insufficient. GitHub reports zero self-hosted runners;
Codespaces requires an unavailable scope and billing reads require unavailable user
scope. Hosted Actions may incur charges beyond allowance according to GitHub docs.
No paid runner or cloud machine is provisioned. This is a real external build blocker,
not a successful compile. Ordinary cheap CI remains separately authorized.

## Design

Use a model schema migration read adapter, not loss of historical evidence. Architecture
features carry independent provenance/conflicts; artifact role labels remain user claims.
Graph outputs follow recovery resource/build declarations, while kernel/AVB links are
independent edges. Image presence alone never schedules an unrelated image build.
Flags are versioned local state, with explicit USER_OVERRIDE history and review notes;
protected rollback/signing controls cannot become automatic edits. Profiles contain
only validated values. Conflicting overrides can be stored only with explicit warning
acknowledgement, and build validation still blocks invalid combinations.

Dependencies must be explicit reviewed HTTPS URLs and full commit IDs, outside project
Git; no arbitrary name-to-repository cloning. Source sync/build uses trusted upstream
source only after host/configuration gates. Receipts link model, graph, flags, dependencies,
source, host and actual output hashes. No synthetic fixture can become a live build.

The complete core is deterministic and AI-free. AI credentials/services are never
consulted by architecture, flags, dependency, synthesis, planning or build code.
