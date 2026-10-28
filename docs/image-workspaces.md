# Artifact workspaces — schema 1

`js img upk IMAGE --output NEW_DIRECTORY` creates private source, extracted, model, rebuilt, reports
and evidence directories. The output and its parent must not be ambiguous: output is new; parent exists.
Creation uses private staging and exclusive destination reservation. Partial staging is removed on error.

The source snapshot is a regular file with read-only mode and a recorded SHA-256. Rebuild checks it.
This detects accidental changes; it is not cryptographic attestation against an owner who can replace
the entire workspace and its metadata. Never treat a workspace received from someone else as trusted.
Readers validate versions, bounded files, metadata contracts and symlink-free component paths.

Boot components use fixed numbered filenames with explicit offset/size/hash/name mapping in
`model/image.json`. Opaque gaps and trailers are components too, not discarded scaffolding. Vendor v4
fragments have separate files and retain order, names, types and 16 board IDs. Edit either whole vendor
ramdisk bytes or fragment payloads, never both. V4 resizing with fragments requires fragment edits.
Only complete contiguous fragment tables support fragment resizing.

`js img rb WORKSPACE --output NEW_IMAGE` refuses source overwrite, header/model tampering, opaque
byte edits and modified signed/AVB-bearing containers. Modern unsigned resizing updates known header
sizes, table offsets and alignment; nonzero opaque bytes block resizing. Legacy v0–v2 rebuild preserves
existing geometry and requires unchanged component lengths. Metadata editing/new-image authoring is
not an arbitrary configuration interface.

Ramdisk extraction is virtual: logical paths/modes/owners/device metadata stay in `model/ramdisk.json`;
`extracted/entry-NNNNN.bin` carries payload bytes. Neither archive symlinks nor device/FIFO/socket entries
are created on the host. Unsafe paths and likely sensitive material refuse extraction. DTBO workspaces
share one payload file for entries referring to the same blob, preventing extraction amplification.

New models use schema 1; the older inspection report schema remains compatible with additive fields.
Unknown schema versions are refused. Models contain hashes and metadata, not JSON-embedded firmware.
Canonical JSON keys and entry/provenance ordering are deterministic. Reports and receipts retain time;
those are execution evidence, not deterministic artifact bytes.
