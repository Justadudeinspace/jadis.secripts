# Image Intelligence — 0.4.0

`js insp PATH --json` (`js inspect`) identifies content rather than trusting an extension.
`js img insp` uses the same command path. Registry IDs retain their full stable names.
The [CLI map](cli.md) lists every shorthand and descriptive alias.

`secripts.images` now separates bounded reading, codecs/LZ4/XXH32, CPIO, canonical ramdisks,
Android image models, workspaces, comparisons, DT tables, AVB models and explicit oracles.
The recovery compatibility facades remain. Android ramdisk inspection consumes the shared
codec/CPIO engine; it does not maintain an independent boot-specific implementation.

| Capability | Inspect | Extract | Rebuild | Compare | Verification actually provided |
|---|---|---|---|---|---|
| Boot v0–v2 | Native | Components/opaque bytes | Exact geometry | Bytes/known fields | Reparse, hashes, byte identity; no signature trust |
| Boot v3/v4 | Native | Components/signature region | Exact; constrained unsigned resize | Bytes/fields/decoded ramdisk evidence | Reparse, bounds, hashes; edits to signed images refused |
| vendor_boot v3/v4 | Native | Whole ramdisk, DTB, v4 fragments/table/bootconfig | Exact; constrained unsigned resize | Bytes/known fragment metadata | Ordering/types/names/board IDs preserved |
| init_boot | V4 structure | As boot container | As supported boot container | Structure/context separate | Partition role remains inferred |
| LZ4 frame/legacy | Native | Bounded decode | Deterministic uncompressed-block frames | Decoded bytes/CPIO | Standard-frame XXH32 checksums; legacy checksums absent |
| gzip/zlib/DEFLATE | Native/contextual | Bounded decode | Stdlib encoders; normalized gzip header | Content vs encoding separate | Format checksums where defined; raw DEFLATE has none |
| CPIO newc/CRC | Native | Virtual numbered payloads | Canonical pack | Entry semantics | Bounds and CRC additive sums; not authenticity |
| DTB/FDT | Native | Model only | Standalone DTB authoring unsupported | Canonical property hashes/reserves | Structural bounds; arbitrary bindings unverified |
| DTBO v0/v1 | Native | Entries, shared blobs | Canonical known layouts | Entry/geometry evidence | Documented zlib/gzip checksums and nested FDT bounds |
| ELF | Native | Unsupported | Unsupported | Opaque byte evidence only | No load/execute behavior |
| uImage | Native | Unsupported | Unsupported | Header/payload | Header/data CRC; not signature authenticity |
| FIT | Native FDT | Unsupported | Unsupported | Canonical model | Embedded supported hash checks; signatures unverified |
| AVB | Native | No signing-key extraction | No signing/bypass | Metadata/trust states | Explicit optional avbtool; see AVB documentation |
| Historical vendor wrappers | Recognition/bounded metadata | Unsupported | Unsupported | Opaque evidence | No compatibility/service claims |

## Evidence and bounds

PARSER_VERSION 4.0.2 invalidates old immutable native-analysis caches. Canonical image/ramdisk/
DTBO/AVB/comparison models use schema 1. Older inspection-report schemas retain compatible additive
fields. Unsupported model versions are refused; no historical runtime receipt/model is rewritten.

Native non-Android inspection uses a 32 MiB window. Explicit artifact workspaces cap inputs at
128 MiB; compression/ramdisk output is capped at 32 MiB. Boot inspection retains smaller aggregate
budgets. Models cap serialized metadata at 8 MiB. Entry/node/property/depth/string/stream limits
are enforced before allocation/use. FDT paths and canonical metadata have independent budgets.
Shared DTBO blobs avoid payload-copy/extraction amplification. Expected malformed inputs return
structured CLI failures. Deterministic mutation tests are evidence, not a formal parser audit.

The engine never executes a payload. Command-line/header bytes are preserved as artifact components,
not dumped into receipts. Raw firmware data, private keys and complete ramdisk contents do not enter
receipts. Receipt evidence is sanitized, bounded and explicitly marked when truncated.

Optional providers report availability/path/capability/version and actual invocation evidence.
`js prov --probe` is explicit; ordinary help/list/dossier do not spawn version or network probes.
Native/provider disagreements remain evidence. `dtc`/`mkdtimg` are detected but complete adapters
remain unimplemented. AOSP differential tools require exact pinned source hashes and private quarantine.

See [workspaces](image-workspaces.md), [round trips](roundtrip.md), [ramdisks](ramdisk.md),
[AVB trust](avb.md), [research provenance](research.md) and [credits](../CREDITS.md).
