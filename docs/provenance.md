# Provenance

`src/secripts/data/legacy.json` is the canonical packaged inventory. It contains source hashes,
opaque IDs, safe basenames, duplicate groups, classifications, reasons and modern replacements.
It contains no source contents. Secret-bearing artifacts use opaque names. `sec archaeology` exposes
this metadata; `sec explain ID` exposes the source IDs used by that operation.

PROMOTE means reviewed source suitable for hardening. EXTRACT means rewritten technical intent.
ARCHIVE retains metadata for historical context. REJECT excludes duplicates, unsuitable or unrelated
work. SECRET excludes all contents even if some knowledge could have been useful. No original source
was promoted verbatim. Classification is a review decision, not a claim of technical validity.

Operation-specific review and verification records live under `src/secripts/data/operations.json`.
Independent tests verify contracts and failure behavior. Environment validation applies only to
commands actually exercised here. Hardware remains UNTESTED. Do not change that state based on
unit tests or tool presence.
