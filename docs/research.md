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
