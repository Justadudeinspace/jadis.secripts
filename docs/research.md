# Phase 3 research and corpus archaeology

Historical tooling is evidence, not authority. Public primary specifications guide
independent bounded parsers; old tool integration supplies questions and format lineage.
[Machine-readable research provenance](../src/secripts/data/research.json) records
retrieval date, topic, role, confidence, licensing observations and unavailable sources.
[CREDITS.md](../CREDITS.md) is the human project-level view. No third-party corpus code,
binary, key, certificate or firmware is incorporated.

The supplied TWRP2.zip/TWRP3.zip are read-only inputs outside Git. The recursive
inventory streams members into private anonymous/spooled files, never archive filenames.
It rejects traversal/absolute/drive paths, symlinks and special files for promotion;
scans secret/key patterns without printing values; hashes safe-readable members; tracks
identical content; and recursively reads ZIP/JAR and TAR-family archives. Unsupported
RAR/7z are explicitly uninspected. It does not run any member.

Default bounds: 100,000 members, depth 6, 512 MiB/member, 4 GiB cumulative expanded
processing. Duplicated nested archives consume the budget again: coverage is bounded,
not a claim of unlimited recursive completeness. Full sanitized inventory stays in
private local state, not Git. `js research PATH... --json` is an explicit potentially
expensive operation; normal CLI startup never inventories the corpus.

Taxonomy: REFERENCE, EXTRACT_KNOWLEDGE, REIMPLEMENT, OPTIONAL_PROVIDER,
FIXTURE_CANDIDATE, ARCHIVE_ONLY, OBSOLETE, UNSAFE, SECRET, UNKNOWN. Automatic
recommendations are review hints and never permission to copy code. Secret/key paths
become opaque exclusions. Unknown licensing remains unknown. Cap/unsupported-format
blockers and per-class counts are recorded in the sanitized corpus summary below.

## Attribution review

Small source attribution files were inspected statically after secret screening:
AIK authors.txt, MTK header tooling, Loki headers and Rockchip README. This established
AIK's integration role and underlying projects; their hashes are retained in the
corpus summary. Historical implementation research did not import their source.
Loki is a recognition-only historical marker; exploit/patch behavior is excluded.
Root/unlock/flash-oriented corpus projects are not promoted. Unrelated projects remain
archive-only/rejected candidates, never runtime code.

The requested Darwin website and XDA thread retrievals failed; upstream file COPYING
and AIK authors.txt were used instead where appropriate. No inaccessible discussion
is claimed as reviewed. See research.json for exact links and access limitations.

## Corpus results

The completed local inventory summary is tracked in `legacy/provenance/recovery-corpus.json`.
It includes archive byte sizes/SHA-256, recursive member/classification/duplicate counts,
family counts, caps and blockers. Only sanitized aggregate metadata belongs in Git;
opaque sensitive exclusions and full local member details are not republished.

| Archive | Bytes | SHA-256 |
|---|---:|---|
| TWRP2.zip | 394210432 | `709b6ab48d0af5791e52fb87e2562580a26aed154abac3416c4e11a4ba3bf7a9` |
| TWRP3.zip | 309299696 | `6de8c08236365cf18cceb4ed4a47972e5db2089cb4f093b1a8215bb513349d2e` |

67,194 recursive non-directory members; 188 nested containers; 23,468 duplicate
members; 4,294,967,170 streamed bytes. Coverage is **PARTIAL**: 19 byte-budget
exclusions, three malformed ZIP containers, two unsupported compressed/non-TAR
containers and one unsupported RAR/7z container. TWRP2: 40,443 members hashed;
TWRP3: 26,751 members, 26,732 hashed. These are automated heuristic classifications:

| Classification | Count |
|---|---:|
| REFERENCE | 39182 |
| EXTRACT_KNOWLEDGE | 1268 |
| REIMPLEMENT | 1703 |
| OPTIONAL_PROVIDER | 516 |
| FIXTURE_CANDIDATE | 0 |
| ARCHIVE_ONLY | 23290 |
| OBSOLETE | 0 |
| UNSAFE | 94 |
| SECRET | 1122 |
| UNKNOWN | 19 |

SECRET includes conservative key/certificate exclusions and pattern hits; it is
not a count of confirmed live credentials. OPTIONAL_PROVIDER is a historical binary
review category, not approval to use it. No corpus executable became a runtime provider.

## Capability influence matrix

| Capability | Corpus evidence family | Modern relevance | Implementation strategy |
|---|---|---|---|
| Boot containers | mkbootimg/unpack tooling; AIK | High | Independent AOSP-based v0–v4 parser |
| vendor_boot/init_boot | TWRP/Android source context | High | AOSP layout; role remains inferred |
| CPIO/ramdisk | AIK, compression/signing tools | High | Linux documented format; bounded native metadata |
| LZ4 | Compression sources | High | Primary specification; structure only |
| DTB/DTBO | Device-tree and recovery files | High | FDT/AOSP primary formats |
| AVB | AVB and historical signing projects | High | Native untrusted metadata; optional avbtool |
| ELF | Sony/ELF tooling families | Medium/high | Independent Linux UAPI metadata parser |
| MTK | mkmtkhdr/AIK attribution | Device-specific | Legacy wrapper bounds only |
| Rockchip/Loki/ChromeOS | AIK integration and historical tooling | Historical/device-specific | Marker-only recognition; no service actions |
| U-Boot/FIT | mkimage/tooling references | Broader image lab | Primary U-Boot/FDT metadata |
| TWRP trees | Recovery/common/manifests/fstab families | High | Non-executing static resolution and planning |

A corpus family count is not implementation support. Source licenses, correctness
and real device relevance need separate review. No corpus payload serves as a CI
fixture; all newly committed image fixtures are generated synthetic structures.

## Phase 4 targeted follow-up

The Phase 3 inventory was reused, not blindly rescanned. Only two non-secret public recovery
project test images were read from selected nested ZIP members, with inventory hashes verified:

| Component | Bytes | SHA-256 | Observation |
|---|---:|---|---|
| Recovery project boot test image | 783655 | `c5eac632addba77fc76afb95b51e35f15ab02ba9c14ce799fba3aec87f4aead0` | BYTE_IDENTICAL reconstruction |
| Recovery project recovery test image | 529707 | `455684ae541a4fa15634ed459c173f69b8bb4555c1582e0f30a7502b400d0a2f` | BYTE_IDENTICAL reconstruction |

Neither artifact was executed or redistributed. Their licensing/stock-device provenance is not
established. They are corpus test artifacts, not real-device qualification. Phase 3's recursive
coverage limitations remain; this follow-up does not turn the original 4 GiB pass into complete coverage.

Current AOSP mkbootimg/unpack_bootimg/header/tests/helper sources were studied alongside generic boot,
vendor_boot and DTBO documentation. The fixed source commit and exact executable source hashes are
recorded in research.json. Seven small valid AOSP-generated fixtures match native round trips and
upstream unpack/repack. Earlier zero-ID/missing-DTB synthetic disagreements remain evidence.

AOSP AVB small_blob.bin is a 21-byte upstream test payload with SHA-256
`d30fca4adc515ea718f2193c38fd9acb78dc1a5b472eb937e7e09f415ef53b55`.
It was zero-padded to 4096 and wrapped in locally generated synthetic AVB data to exercise real
signature, expected-public-key, native descriptor hash and digest checks. No upstream test signing
key was downloaded. No binary fixture is committed when redistribution licensing is unestablished.

LZ4 frame/block and xxHash specifications informed independent native implementations. Twenty-seven
XXH32 and five LZ4 block cases matched installed system libraries. zlib's manual/license informed the
stdlib compression path. Devicetree and current U-Boot references informed canonical FDT/FIT/hash/CRC
interpretation. These are intellectual influences, not imported source implementations.

[Phase 4 fixture evidence](../src/secripts/data/phase4-evidence.json),
[research source records](../src/secripts/data/research.json) and [CREDITS.md](../CREDITS.md) retain
source roles, dates, hashes, confidence and licensing boundaries. No research archive, firmware image,
key/certificate, extracted corpus tree or unknown executable belongs in this repository.

One pinned Gitiles fetch returned HTTP 503 during qualification. A later fetch of the exact
pinned revision succeeded and all seven oracle cases passed. Explicit development fetchers
may retry the official main reference after transport failure, but only identical pinned
SHA-256 content is accepted and the actual retrieval URL is retained. No hash check is relaxed.

## Phase 6

The [audit/gap gate](research/phase6-gap-matrix.md), [primary-source ledger](research/phase6-sources.json)
and [real A51 input evidence](research/phase6-a51-evidence.json) record target selection, hashes,
source generations and known blockers. No corpus-wide rescan, stock firmware import or
transitive source sync was performed. Public prebuilts are not evidence of a local build.
