# Security

Historical credentials are treated as compromised and retired. No historical content is shipped;
secret-bearing members have opaque names and metadata only. Rotate any credentials you previously
used in these notes through their providers. Do not submit credentials in issues or reports.

Report vulnerabilities privately to the repository owner using GitHub private vulnerability reporting
if enabled, otherwise request a private contact channel without publishing exploit details or secrets.

`sec` does not unlock, wipe or flash devices. Temporary boot is deliberately refused until support
and compatibility can be established. Source checkouts and tools on PATH are executable trusted inputs:
review them before building. Static tree inspection never executes makefiles.

Receipts are sanitized best-effort pattern-based evidence, not a guarantee that arbitrary tool output
contains no personal information. They are local, private by default, and may include host names,
repository paths, device identifiers and command output. Review before sharing. Secret scanning is
conservative, cannot identify every credential, and must accompany human review.
