# Contributing

This is Christopher Osburn / JADIS's personal project. Keep work focused on developer operations
and recovery development. Preserve the Apache-2.0 license and source authorship where code is reused.

Use Python 3.11+ on Linux. Install with `python -m pip install -e '.[dev]'` in a virtual environment.
Run `ruff check .`, `ruff format --check .`, `pytest -q`, `python tools/secret_scan.py`, and
`python -m build`. Regenerate `docs/catalog.md` with `python tools/catalog.py` when metadata changes.

Register operations with complete intent, prerequisites, risk and provenance. Avoid arbitrary shell
execution, credential arguments, guessed device partitions and automatic privilege escalation.
Tests must prove failure behavior without downloading source trees or touching devices. Synthetic
secret test values must be clearly invalid and assembled from fragments. Record environment and
hardware limitations honestly. No agent fan-out or more than two background processes.

Phase 2 uses `js` as its sole canonical launcher. Keep the distribution jadis-secripts and package
secripts; do not reintroduce a compatibility alias or rename operation IDs. Run `python tools/qualify.py`
for the local gate and `python tools/validate.py` with the installed launcher on PATH. Device/network
smoke must be explicit (`--devices`, `--network`); unit tests must mock both. Regenerate release provenance
only from matching-release evidence. Build and exercise the wheel outside the checkout before claiming
the entry point works. The repository is intended to remain private.

Meaningful externally influenced capabilities require review of upstream authorship, licenses and
notices. Update CREDITS.md and detailed research provenance before considering them complete.
Do not guess names/licenses, substitute credits for notices, or use corpus binaries as providers.
Run `python tools/audit_docs.py` and installed-launcher `python tools/validate_images.py` for
Image Lab changes; the latter uses temporary synthetic fixtures and isolated runtime state.

CLI names are contracts in secripts.commands. Favor unambiguous 2–4 character working forms,
preserve full names, check scoped collisions, regenerate tools/cli_map.py and test alias/guard parity.
Do not duplicate registry operations for spellings. Keep js 1337 permanent. New parser/model schema
changes need explicit versions, malformed-input tests, provenance and credits/license review.
Optional oracle qualification is explicit; never execute research-corpus programs or download keys.

For optional cryptographic tests, an explicitly provisioned pinned provider can be prepared with
`python tools/prepare_avb_provider.py --output /new/private/provider`; add that directory to PATH
only for the test invocation. `python tools/validate_phase4.py` must use an installed js.
Never confuse synthetic signing-key tests with production/device root-of-trust qualification.
