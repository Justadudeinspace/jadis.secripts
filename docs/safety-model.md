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
