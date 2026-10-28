# Verification — Phase 4 / 0.4.0

## Baseline

Started on clean main at `51f57731b8403e812b25620df6755efaea51e680`. Local HEAD, origin/main
and independently queried remote main matched. Installed js was 0.3.0; stale JADIS sec absent;
unrelated /usr/bin/js remained Node. Baseline full gate passed: 138 tests, Ruff lint/format,
secret scan, documentation audit and package build. Repository architecture, source, parser/
workspace/receipt contracts, tests and attribution were inspected before extension.

## Applicable gate

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest -q
python tools/secret_scan.py
python tools/audit_docs.py
python -m build
```

`tools/qualify.py` records actual outcomes outside Git, tagged by release. The legacy validation
filenames remain compatible; a filename is not a claim that old evidence qualifies a new release.
Unit tests use local synthetic fixtures; optional installed avbtool/openssl tests are explicit
provider qualification, with locally generated ephemeral synthetic test keys. No corpus key is used.

Phase 4 additionally checks built-wheel metadata and the installed js **outside the checkout**;
short/long aliases, nested routing, JSON, completion, non-TTY/NO_COLOR and PTY behavior;
workspace refusals, source immutability, extracted component hashes, reconstruction and comparisons.
CLI aliases are metadata-normalized before the same registry/risk/receipt path. Recipes retain IDs.

## Differential and corpus evidence

- CORPUS_SAMPLE: two existing recovery test images, hashes recorded in phase4-evidence.json,
  each structurally inspected and byte-identically round-tripped. No sample was executed or committed.
- SYNTHETIC_UPSTREAM_TOOL_GENERATED: current pinned AOSP generates seven valid boot v0–v4/
  vendor_boot v3/v4 cases. Native extraction/rebuild and AOSP unpack/repack agree byte-for-byte.
  V4 includes NONE/PLATFORM/RECOVERY/DLKM fragments. These are not stock device firmware.
- INSTALLED_LIBRARY_ORACLE: 27 XXH32 cases and five compressed-block cases match installed
  libxxhash/liblz4. Those libraries are validation oracles, not runtime dependencies.
- UPSTREAM_FIXTURE_WRAPPED_FOR_TEST: AOSP small_blob.bin (21 bytes) is hash-identified,
  zero-padded to 4096 and wrapped in a locally signed synthetic AVB image. Native hash,
  optional provider signature/expected-public-key checks and vbmeta digest succeed. The tool
  rejected an unpadded 21-byte payload; that preparation limit is retained, not hidden.
- REAL HOST: aarch64 Linux/Termux interpreters, installed tools/provider versions and host constraints.
- REAL DEVICE: no qualification claimed; offline artifact work requires no device access.

Initial minimal v0/v1 fixtures had zero legacy IDs, which disagree with current AOSP's recomputed IDs;
a v2 fixture without a DTB was refused by current mkbootimg. These observations remain recorded.
The valid upstream-generated qualification cases did not overwrite those earlier findings.

## Capability limits

Canonical model equivalence is limited to implemented fields. Unknown bytes, vendor bindings,
extended DT table layouts, unsupported dictionaries/codecs and missing companions stay unresolved.
Legacy boot resizing/new arbitrary image authoring is unsupported. Modified signed/AVB-bearing
containers are refused. Chain verification/digests, FEC, FIT signature verification, device root
of trust and device rollback enforcement are not qualified.

Actual TWRP build remains BLOCKED on this host; hardware qualification remains UNTESTED. No flashing,
unlocking, wiping, rooting, security bypass or huge Android source synchronization was added/run.

CI retains a serial Python 3.11/3.13/3.14 matrix. It provisions only hash-pinned official avbtool
source explicitly for provider tests, uses synthetic fixtures and small AOSP oracle inputs, and
never needs the supplied ZIP archives. Exact final-commit CI evidence is reported after push;
local success or baseline CI never substitutes for the final commit's workflow result.

## Local release evidence

The expanded suite contains 265 tests. Both the Linux Python 3.13 and Termux Python
3.14 interpreters pass all 265, including explicit optional AVB provider tests. The
installed-wheel Phase 4 harness passes 98 checks from outside the checkout, using
isolated state. The retained general CLI harness records 31 checks. Expected safety
refusals and malformed-input failures are checked against their expected exit codes.

Seven pinned-AOSP-generated boot/vendor_boot cases agree with native reconstruction.
The two hash-identified corpus samples round-trip byte-identically; neither represents
modern-device qualification. Library oracles agree on 27 xxHash32 and five LZ4 block
cases. Final-commit GitHub Actions results are separate external evidence.

## Phase 5 product qualification

Starting main was bc943ec1c124b12235763df379bbf37883a371bd, installed 0.4.0,
87 operations / 22 categories / 26 recipes. The full 265-test baseline and all
quality gates passed before implementation. Research/gap gate preceded product code.

Phase 5 has 92 operations / 23 categories / 28 recipes and 364 tests. Coverage adds
guided/no-argument behavior, topic help, acquisition choices, source declarations,
conservative log classes, AI consent/context/redaction, per-provider request/response
contracts, missing/offline/oversized/malformed response refusal and typed tool limits.
No test performs paid AI inference. Mocked transport success is not live provider success.

The documentation gate checks internal links recursively, generated parser/recipe
references, alias coverage and 115 shell examples by parsing them without execution.
The final wheel must also pass tools/validate_phase5.py from outside the checkout,
plus retained Phase 4 image/alias smoke and optional pinned AOSP differential tests.
Normal TTY, non-TTY, JSON and NO_COLOR remain explicit validation modes.

Research metadata includes 69 records (63 hashed direct accesses, two browser-only
official accesses and four unavailable retrieval attempts) and six pinned device
trees. No full stock-firmware-to-known-good-local-recovery chain is established.
Source generation suggestions, tree candidates and build-failure classifications
remain review-only; no new recovery backend, compiler qualification or hardware claim.

Real-host compilation stays BLOCKED. Hardware qualification stays UNTESTED. AI live
inference and subscription authorization stay UNTESTED/BLOCKED respectively.

Initial Phase 5 CI on a1ec462 passed tests but failed the Python 3.11 generated
command-reference check. Reference syntax now derives directly from action metadata
instead of terminal/interpreter-dependent argparse formatting. Width-invariance and
AI input-growth tests cover the correction; final-commit CI remains the authority.

A follow-up CI diff isolated three optional positionals whose required attribute
differs on Python 3.11 despite accepting empty input. Reference requirements now
derive positional arity from nargs, preserving explicit option guards. A regression
reproduces the older metadata and checks identical reference output.

## Phase 6 boundaries

Composite architecture/configuration tests use synthetic declarations. The separately recorded
A51 tree and prebuilt hashes are real upstream inputs; they are not generated outputs.
Actual compilation remains BLOCKED. Hardware and live AI provider qualification are UNTESTED.
The source/configuration contract binds model, flags, dependency pins and actual output collection;
legacy workspaces do not gain retrospective model-bound evidence.
