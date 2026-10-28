# Receipts and evidence

Receipts are local sanitized JSON execution records under the user data directory.
Operation IDs survive shorthand aliases; historical records remain readable.

```sh
js hist --summary --limit 20
js hist --operation image.roundtrip --json
js hist --failed --json
js rcpt latest --json
js rcpt latest --failed --json
```

Result records describe invocation, preconditions, commands, exit codes, artifacts,
hashes and bounded evidence. A successful collector can report BLOCKED/UNKNOWN/
CONFLICT/UNTESTED findings. There is no arbitrary replay or independent attestation.
AI receipts omit conversation bodies. Sharing any report requires privacy review.
See [provenance](provenance.md), [safety](safety-model.md) and [verification](verification.md).
