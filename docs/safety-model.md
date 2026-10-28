# Safety model

| Risk | Enforcement |
|---|---|
| READ_ONLY | Inspect state; no intended configuration changes. ADB enumeration may start its daemon. |
| MUTATING | Show explicit effects/configuration and offer dry-run for source sync and build. |
| PRIVILEGED | Require an already privileged environment; never run sudo automatically. |
| DESTRUCTIVE | Require a TTY and exact action/device-bound phrase; no bypass flag. |

No production destructive operation is registered. The guard is tested independently. `recovery boot`
refuses unresolved support, `clean` explains manual scope without deleting, and flashing is absent.
Builds execute the selected checkout's code; static auditing does not certify that code safe.

Exit codes: 0 successful invocation (diagnostics can contain WARN/UNKNOWN); 1 operation or state
failure; 2 invalid usage/metadata/ID; 3 missing prerequisite; 4 safety refusal; 5 unsupported platform
or backend; 130 interrupted. Inspect diagnostic states separately from command exit status.

Secret-class patterns detect provider token prefixes, assignments, bearer strings, private keys and
credential-bearing URLs. Arguments matching them are refused. Outputs, receipts and public rendering
are redacted. Raw command captures are temporary and never copied into the repository. Arbitrary
personal data and unknown credential formats remain a human review responsibility.

Phase 2 preserves those controls. Typed tree/artifact/device parameters are never arbitrary subprocess
arguments. Network recipes require `--network`; explicit individual network operations identify that
behavior in their metadata. Dossier does not probe the network. Interactive cockpit enumeration is
explicit local transport evidence; non-TTY/JSON cockpit snapshots leave device counts UNTESTED.

Device identifiers are masked before receipt persistence and returned evidence. Enumerations retain
states/counts, not serials; package lists retain only counts; CPU serial fields are discarded. Legacy
receipts with named identifier fields are sanitized on read without rewriting stored history. Unknown
personal identifiers in arbitrary external output still require human review before sharing.

Image decoding is bounded and non-extracting. Unsupported compression and unresolved Make expansion
remain unresolved/partial evidence, never silently accepted as verified functionality. AVB declarations
are untrusted; no signature, key trust, rollback or hardware claim follows. Receipt comparisons do not
execute or replay commands. Current tree snapshots do not certify historical build inputs.

## Phase 3 hostile input and derivation

Archive members are never executed or extracted to archive-controlled names. Streamed inventory
has member/total/depth caps; paths, symlinks, special files and likely keys are classified and
excluded from promotion. Corpus signing keys are never used. [Research](research.md).

Image parsers impose independent region/count/string/decompression limits, never execute payloads
or follow CPIO links. Reports omit raw firmware contents and identifier-bearing bootconfig.
Optional providers require explicit invocation with fixed argv/timeouts. Candidate trees require
a new directory, safe names and source-linked architecture; TODOs remain unresolved. Model facts
and plans preserve uncertainty. Neither model import nor derivation changes a connected device.
