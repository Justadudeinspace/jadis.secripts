# Round-trip and comparison evidence

```sh
js img rt boot.img --json
js img rt boot.img --output /existing/parent/workspace --json
js img cmp original.img rebuilt.img --json
```

Without output, a temporary workspace is discarded after analysis; the receipt retains hashes and
findings, not a promise that temporary artifact paths remain available. Persistent output is explicit.

The pipeline parses source, models sections, extracts disjoint bytes, reconstructs from extracted
components, reparses output and compares. Exact Android reconstruction does not merely copy the source
snapshot; headers, payloads and opaque regions are reassembled under a validated model. Signed images
may round-trip unchanged; modifications are refused, not re-signed or stripped.

Comparison schema 1 separates byte identity, structural equivalence, semantic equivalence, component
equivalence, metadata equivalence, cryptographic state and unresolved differences. Difference records
carry class, component/location, values/hashes, interpretation, expectedness, severity and possible
compatibility impact. Output is bounded and truncation is explicit.

BYTE_IDENTICAL proves identical bytes. CONTENT_EQUIVALENT identifies demonstrated component content.
STRUCTURALLY_EQUIVALENT is limited to the modeled structure. SEMANTICALLY_EQUIVALENT covers the specific
supported canonical model, not arbitrary Android behavior. Unknown bytes/differences remain unresolved.
For modern boot ramdisks, different compressed representations can have equal decoded entry semantics.
CPIO compares content, mode, UID/GID, link target, metadata, order and compression separately.

CPIO packing emits canonical headers, alignment and trailers; original optional trailer/padding or
compressor metadata may differ. Directory packing normalizes ordering, owners and timestamps. DTBO
packing uses canonical 32-byte headers/entries, 4-byte blob alignment and sharing of identical blobs.
Extended/unknown table metadata is not silently discarded: reconstruction is unsupported.

AOSP differential verification is explicit:

```sh
js img diff boot.img --tools /path/to/reviewed-pinned-aosp-source --json
python tools/validate_oracles.py --fetch-upstream
```

Only exact pinned packer/unpacker/helper source hashes are accepted. Sources are copied into a private
quarantine. Returned reconstruction arguments are tokenized, allowlisted and path-checked, never sent
to a shell. Provider agreement and disagreement remain separate from native evidence. AOSP-oracle
absence does not invalidate a native inspection; it leaves differential verification unavailable.

No byte identity, canonical-model equality, checksum or signature result proves device compatibility,
bootability, hardware qualification or recovery decryption/backup behavior.
