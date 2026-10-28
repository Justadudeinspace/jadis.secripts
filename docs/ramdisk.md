# Ramdisk engine — schema 1

The reusable pipeline is codec detection → bounded decoder → native CPIO → canonical model → virtual
payload workspace → deterministic CPIO pack → encoder. Boot images consume the same decoder/parser;
there is no second boot-specific CPIO implementation.

`js ram insp`, `ext`, `pack` and `cmp` accept full aliases `inspect`, `extract` and `compare`.
`pack` accepts a virtual workspace or a regular directory. Existing output files are refused.
A workspace preserves supported source entry metadata/order. A plain directory is normalized to
sorted names, UID/GID/mtime zero and regular/directory/symlink metadata; no special host files are read.

CPIO newc/CRC parsing retains inode, mode/type, UID/GID, mtime, link count, device numbers, path, payload
size/hash, archive/order and alignment evidence. CRC means the format's additive 32-bit sum, not a
cryptographic CRC. Concatenated archives, zero padding and optional trailers are parsed under limits.
Packing emits explicit canonical trailers. Non-UTF8/control-character names are unsupported.

Extraction refuses traversal, absolute/drive-like paths and sensitive paths/content. Logical paths
never become host paths. Payload filenames are generated indices. Symlinks/device/FIFO/socket entries
remain metadata; links are never followed. This is an engineering representation, not a privileged
filesystem restoration tool. Metadata editing is constrained by pack validation and safe paths.

LZ4 standard frames validate descriptor, header checksum, block checksum and content checksum when
present. Compressed/uncompressed and dependent/independent blocks, concatenation/skippables and
legacy blocks are bounded. Missing dictionaries return BLOCKED_MISSING_DICTIONARY. The native encoder
emits deterministic uncompressed blocks with checksums; it does not promise compression ratio.
Legacy LZ4 has no defined frame checksums, so checksum evidence is explicitly absent.

Gzip verifies headers/checksums via bounded standard-library decoding and handles concatenated members.
Zlib verifies its format checksum; raw DEFLATE requires explicit context and has no format checksum.
XZ, LZMA-alone and bzip2 use bounded stdlib decoders. Output is capped at 32 MiB; boot inspection keeps
its smaller per-ramdisk/aggregate budgets. LZMA memory is separately capped. Compression encoders can
vary with implementation version; decompressed equivalence is not a claim of identical compressed bytes.

Comparison distinguishes ADDED, REMOVED, CONTENT_CHANGED, MODE_CHANGED, OWNER_CHANGED, SYMLINK_CHANGED,
METADATA_CHANGED, ORDER_CHANGED and COMPRESSION_CHANGED. A symlink target is data, not permission to
access that path. Hashes/checksums do not authenticate an archive or qualify its device behavior.
