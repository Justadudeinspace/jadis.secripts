# Provenance

`src/secripts/data/legacy.json` remains the canonical metadata-only legacy inventory: safe names,
opaque IDs, SHA256 hashes, duplicate groups, classifications, reasons and modern replacements.
No source contents are shipped. Secret-bearing entries have opaque names. Only modern launcher
references changed in Phase 2; historical hashes and classification decisions remain intact.
`js archaeology` exposes lineage; `js explain ID` includes operation-specific evidence.

PROMOTE means reviewed source suitable for hardening; EXTRACT means rewritten intent; ARCHIVE retains
safe context; REJECT excludes unsuitable/duplicate/unrelated material; SECRET excludes contents.
No original source was promoted verbatim. New Phase 2 operations are independently engineered,
not fictitiously attributed to legacy sources. There are still eight reviewed extraction artifacts.

`src/secripts/data/operations.json` records release-specific operation verification. Generation reads
actual local validation records for the matching release. Without matching successful gate evidence,
shared-test verification is UNTESTED. Environment execution is populated only from matching-release
smoke observations, never inferred from unit tests. Fixture tests do not become hardware evidence.

Use `python tools/qualify.py`, then installed-launcher `python tools/validate.py`, then
`python tools/provenance.py`. Evidence records are local runtime state, not Git. Public metadata
contains no captured outputs or device identifiers. Operation IDs and old receipts survive the CLI
namespace migration unchanged; historical runtime receipts are not rewritten.

## Research and attribution provenance — 0.3.0

`src/secripts/data/research.json` records public source IDs, retrieval dates, topics, influence,
confidence, license observations and failed access attempts. Image reports attach source IDs
and observed header offsets/version; model facts link source hashes/locations. Candidate
configuration has per-line evidence and explicit review requirements. The sanitized corpus
summary is separate from private local inventory. [CREDITS.md](../CREDITS.md) is the human
project-level view; it cannot replace source license/notice obligations. Every externally
influenced capability requires attribution/licensing review before completion.

## Phase 4 transformations and verification

Canonical models and comparison records use explicit schema versions. Every transformation records
source/output hashes, component metadata, operation/parameters, native/provider identity, timestamp,
warnings and unresolved state in sanitized receipts. Detailed local models/workspaces remain separate
from bounded receipt views. Model/receipt history is not rewritten to adopt new shorthand.

Pinned AOSP mkbootimg and AVB revisions, source SHA-256 values, targeted corpus test artifacts and
upstream fixture preparation are in research.json and phase4-evidence.json. Provider/native disagreement
is retained rather than silently selecting a winner. New xxHash/zlib technical lineage is credited.
