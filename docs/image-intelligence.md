# Image Intelligence — 0.3.0

`js inspect PATH --json` identifies content, not an extension. `js run image.inspect
--artifact PATH` uses the same engine through the operation registry. `js inspect
PATH --providers` explicitly requests installed external evidence; ordinary inspection
executes no payload or external decoder.

The independent `secripts.images` package owns identification, Android containers,
compression/ramdisks, FDT/DTBO, ELF/uImage/vendor markers, AVB metadata and optional
providers. Recovery Lab consumes this engine through compatibility facades.

## Supported scope

| Family | Native inspection | Limits |
|---|---|---|
| Android boot v0–v4 | Header, alignment, bounded section ranges, recovery DTBO/DTB/signature regions | No bootability or partition identity proof |
| vendor_boot v3/v4 | Ramdisk, DTB, v4 fragment table/types/names/board IDs, bootconfig ranges | Fragment contents may need unsupported decoding |
| init_boot | Probable role from v4/no-kernel/ramdisk plus contextual evidence | Never authoritative from filename alone |
| gzip, bzip2, XZ, LZMA-alone | Bounded native decompression and CPIO metadata where supported | No extraction or execution; cap failure remains partial |
| LZ4 | Frame/legacy/skippable structure, descriptors, blocks, checksum presence | No native decompression or checksum validation |
| CPIO newc/CRC | Counts, bounded paths, executable/link counts, indicators, fstab flags, CRC sums | Symlinks never followed; unsafe paths reported; not a complete initramfs concatenation evaluator |
| FDT v17 | Header/region/reservation bounds, token hierarchy, allowlisted properties | No complete hardware interpretation |
| DTBO v0/v1 | Table, entry ranges and native embedded FDT | Compressed entries remain partial |
| ELF32/64 | Both byte orders, architecture, entry point, program/section ranges | Never loaded/executed |
| uImage | Header and payload fields/CRC checks | CRC is not cryptographic verification |
| FIT | FDT `/images` and `/configurations` recognition and bounded metadata | External data and signature verification not implemented |
| AVB | Footer/vbmeta fields and bounded descriptors | Metadata only; no cryptographic verification |
| MTK legacy | 512-byte wrapper recognition and payload range | Device-specific compatibility unresolved |
| Rockchip, Loki, ChromeOS | Historical marker recognition | Partial identification only |

A content report separates `structure_status`, identification evidence,
provider agreement and qualification. `PASS` on structure means only that the
implemented checks passed. Header version observations include byte offsets and
research source IDs. Source IDs resolve through
[research.json](../src/secripts/data/research.json) and [credits](../CREDITS.md).

## Hostile-input bounds

Default native non-Android inspection reads at most 32 MiB (oversized files are
stream-hashed and reported partial). Android headers use bounded seeks for declared
regions; ramdisk input/output is separately capped. Generic parsers cap entries
20,000, FDT nodes 4,096/properties 16,000, strings 4,096 bytes and nesting 64.
CPIO and decompression have their own smaller limits. No filesystem extraction
occurs. Traversal, malformed lengths, overlaps, table limits and truncated data
produce refusals/findings. This is defensive parsing, not a claim of formal proof.

SHA-256 is streamed. Immutable native results are cached by content hash and parser
version below the local data directory, with per-invocation filename context and
providers added afterward. Changes during inspection are refused. Raw ramdisk
contents, bootconfig, AVB property values and firmware payloads are not receipts.

`file` and `avbtool info_image` are optional explicit fixed-argv evidence calls with
timeouts. `dtc`, `lz4`, `unlz4` and `cpio` are availability observations only. Nothing
is downloaded. Corpus executables are not providers. Disagreement is retained.

Structural inspection != cryptographic verification != trusted key verification
!= rollback enforcement != bootability != device compatibility.
