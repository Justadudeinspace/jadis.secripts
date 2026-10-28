# Phase 5 research gap gate

Gate recorded before implementation, 2026-10-28. Baseline main is
`bc943ec1c124b12235763df379bbf37883a371bd`, version 0.4.0; 87 operations,
22 categories, 26 recipes. Full baseline gate passes 265 tests, Ruff, secret scan,
documentation audit and package build. Repository is private and initially clean.

[Source ledger](phase5-sources.json) records 65 bounded retrievals, 61 accessed and
4 unavailable, with content hashes and source roles. Two subsequent official browser
retrievals establish the Claude schema/billing details, bringing the ledger to 67 records. Targeted follow-up of TeamWin issues 79 and 312
adds two hashed issue records (69 total); those logs demonstrate missing build input
and source/API compile symptoms, with no locally verified repair. Six selected tree revisions
are pinned. Cached documents/source remain outside Git; no external code is adapted.
The [baseline inventory](phase5-baseline.json) maps all 125 tracked files from the immutable starting commit.

## System audit and implementation decisions

| Subsystem | Existing evidence | Gap / decision | Remaining limit |
|---|---|---|---|
| CLI / aliases | Scoped contracts, equivalence tests | Add topic help and guided entry using same contracts | Keep non-TTY help stable |
| Registry / recipes | Typed operations, generated catalog | Add acquisition, source and failure evidence contracts | No count-driven wrappers |
| Receipts / evidence | Sanitized bounded JSON | Reuse for guidance and AI metadata; do not retain AI bodies | Local evidence is not attestation |
| Cockpit / dossier / doctor | Live host + registry views | Compact domain entry, drill-down instead of opening flood | Presence is not readiness |
| Developer / Android / ADB / Fastboot | Read-only collectors, masked IDs | Preserve; guide explicit device selection | No hardware qualification |
| Image engine / codecs / ramdisk | 265-test baseline, AOSP and library oracles | Preserve regression suite, surface workflows in manual | Limited modern stock diversity |
| DTB / DTBO / AVB / U-Boot | Native bounded models and optional providers | Explain crypto/trust and unsupported variants clearly | AVB chains/FEC/FIT signatures unresolved |
| Device models / correlation | Source-linked facts and conflicts | Guide evidence acquisition; never invent identity | Models remain partial without inputs |
| Trees / derivation | Static Make graph, candidate provenance | Add explicit review-state summary | No GNU Make execution or compatibility score |
| Source intelligence / planner | Minimal manifest heuristic | Resolve local declared project toolchains and research-linked options | Branch name is not suitability proof |
| TWRP backend | Safe fixed adapter, mocked orchestration | Attach bounded failure diagnosis and external-host requirements | Real build BLOCKED here |
| Qualification | Manual area attestations | Beginner manual and stop boundaries | No device = UNTESTED |
| AI | Runtime detection only | Fixed official providers, BYOK, preview-before-send, no autonomous shell | Live calls untested; subscription eligibility unconfirmed |
| Research / provenance / credits | Phase 3/4 lineage and corpus inventory | Add current research, pins, source-generation/failure matrix | Upstream availability varies |
| Documentation / packaging | Generated map; fragmented documents | Unified manual + generated full parser reference and example validation | Offline link audit cannot prove remote content |
| Tests / CI | Serial 3.11/3.13/3.14 | Mock AI, guidance/parser/docs/failure regression; installed wheel | No paid calls or firmware CI |

## Questions answered

AOSP distinguishes the generic ramdisk, vendor ramdisk fragments, init_boot context,
recovery arrangements, super/dynamic partitions, virtual A/B snapshots and metadata
encryption. Partition presence and Android version alone cannot choose a TWRP target.
Kernel strategy must account for prebuilt/source kernel, DTB/DTBO and recovery modules;
GKI does not eliminate vendor dependencies.

The current TeamWin compilation page points to AOSP 11/12.1 and historical Omni
generations. The 12.1 manifest defaults to android-12.1.0_r4 and includes JDK11,
JDK8 and JDK9 projects. Listing several JDKs does NOT identify the active JDK.
Select the toolchain from the checked-out build configuration, not host Java or
installed Android version. Current full AOSP host guidance uses x86_64 Linux,
400 GB disk and 64 GB RAM; those are full-AOSP planning references, not measured
minimums for every reduced recovery tree. Existing 40 GiB/8 GiB floors are only
early rejection floors and must not imply host qualification.

## Source generation / backend matrix

| Source family | Product / target evidence | Java / Python | Boundary |
|---|---|---|---|
| TWRP AOSP 12.1 | twrp prefix; recoveryimage/bootimage/vendorbootimage chosen by actual arrangement | Manifest declares JDK11/8/9; Python components; active version requires local build config | FDE unsupported according to branch README; FBE device-dependent |
| TWRP AOSP 11 | Review branch README and local products | Branch-specific; inspect checkout | Not every Android 11+ device fits |
| TWRP Omni 9 and older | Historical omni products | Legacy branch-specific; do not prescribe modern Java | Historical recovery constraints |
| OrangeFox | fox_12.1 and conditional fox_14.1 guidance | Own source/build prerequisites | GPLv3+ stated upstream; no new backend implemented |
| Lineage Recovery | Device/common/vendor integration in Lineage trees | Branch prebuilts/configuration | Shares Android formats, not TWRP flags/UI |
| AOSP Recovery | Upstream recovery/build integration | Exact platform checkout | No TWRP-specific decryption assumptions |
| PitchBlack | Organization investigated | Not qualified | Insufficient current build evidence; no implementation |

## Representative tree findings

TeamWin a51 (Exynos), dm1q (Qualcomm) and RMX1941 (MediaTek) declare dedicated
recovery sizes and prebuilt kernels. Lineage gs201/pantah (Tensor) demonstrates
common-tree, vendor_boot and chained-vbmeta relationships. The community HVAHW P30
(Unisoc) tree declares header v4/vendor_boot/dynamic-partition/FBE configuration.
That community tree is lower-confidence research, not a known-working assertion.
No local stock-image-to-tree-to-successful-build chain was established for these
samples. Branches/commits/files are in the ledger. Source-built kernel, A-only/A-B,
virtual A/B and retrofit variants still need broader independently validated samples.

## Failure research and uncertainty

The twrpdtgen issue 209 contains a Soong GenerateBuildActions panic and an nsjail
warning. A nearby warning must not be declared the root cause of that panic. Soong's
README explains namespace dependencies. A normalized classifier may suggest module,
product, kernel/DTB, VINTF, linker, toolchain, host and resource problem classes, but
log-only matches are INFERRED, confidence limited; missing-tree findings require
static path evidence. Never automatically edit manifests or suppress dependencies.

## Conflicts, unavailable sources and licensing

The minimal manifest recommends ALLOW_MISSING_DEPENDENCIES; Secripts retains strict
missing-dependency checks. Several JDK projects coexist: no automatic Java choice.
The browser fetch for Lineage's build wiki returned 403; a separate bounded direct
retrieval succeeded and its hash is recorded. GNU CPIO and one Claude schema URL
were unavailable; corrected language-specific schema and billing browser retrievals are separately recorded.
Per-source availability is authoritative; search snippets are not implementation proof.
Tree-level licenses are not established by GitHub metadata for these samples;
individual source notices vary. Do not copy trees or redistribute firmware.
Upstream docs are references, not license grants for arbitrary source integration.

## AI authentication decision

OpenAI Responses, Anthropic Messages and DeepSeek chat support official API
authentication. Implement BYOK through provider-specific environment references,
fixed destinations, bounded structured context and explicit send consent.
Official Sign in with ChatGPT exists, but this private client's eligibility is not
established; proper implementation additionally requires PKCE, nonce/state, JWKS
validation, account-bound rotating credentials and terminal-event streaming. Do not
ship an incomplete flow or reuse Codex sessions. Mark subscription login BLOCKED
pending eligibility and a separately qualified credential lifecycle. Claude API
subscriber credits are distinct from extracting Claude Code subscription credentials.
No applicable general third-party subscription flow was established for DeepSeek.

## Implementation opportunities and risks

Proceed with guidance, acquisition planning, source-toolchain evidence, conservative
build diagnostics, protected AI advice, generated manuals and regression tests.
Defer speculative parser expansion, automatic downloads, additional backends, real
source synchronization and hardware actions. Prompt injection in research/logs/AI
output must never grant tools or change evidence states. Native parsers and existing
safety guards remain authoritative. Research gaps stay visible after productization.
