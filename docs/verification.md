# Verification evidence — 0.3.0, 2026-10-28

## Baseline

Started on clean main at `219b68cb3b894c644d3f6dc45e1a565c1d1e2030` (0.2.0).
Local HEAD, origin/main and independent SSH remote query matched. The complete existing
validation gate passed before edits: 104 tests, Ruff lint/format, secret scan and package build.
Canonical installed js was 0.2.0, stale JADIS sec absent, unrelated /usr/bin/js (Node) preserved.
Repository source/tests/docs and existing architecture were inspected before extension.
Repository visibility remains private; authenticated GitHub evidence is queried without changing it.

## Phase 3 validation

The source suite expands to **138 tests**. New cases cover content dispatch, boot generations,
LZ4 frame/legacy/skippable bounds, FDT/DTBO/ELF/uImage/FIT, historical vendor markers, cache context,
provider disagreement, nested ZIP duplicates/secrets/unsafe paths and byte caps, models/conflicts,
Make declarations/line locations, candidate provenance/no overwrite, manifest hazards, CLI paths,
credits/reference integrity and deterministic adversarial bytes. Existing safety tests remain intact.
Fixtures are synthetic; test results are not real hardware or firmware qualification.

Required gate:

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest -q
python tools/secret_scan.py
python tools/audit_docs.py
python -m build
```

`tools/qualify.py` captures this gate locally outside Git, tagged with the actual release.
`tools/validate.py --devices --network` exercises the installed launcher, local inspections,
read-only transport enumeration and explicit GitHub queries. `tools/validate_images.py`
exercises installed js on temporary **SYNTHETIC_FIXTURE** evidence in isolated state: generic
inspection/providers, discovery, model create/import/report, tree diagnosis/derivation,
planning, image recipe, artifact report and cockpit JSON. No fake models persist in normal state.

The installed wheel is also tested outside the checkout. Bash syntax, local YAML parsing,
source/wheel metadata, sole js entry point, documentation references, stale CLI examples,
repository size and accidental corpus inclusion are audited. CLI --help/list remain lazy;
ordinary inspection never downloads anything or probes hardware.

## Evidence categories

- REAL HOST: Linux aarch64, Python/Java/Git/tool state, disk/memory and source/tree configuration.
- CORPUS: read-only archive hashes and bounded recursive inventory; selected small attribution
  files reviewed statically. No corpus executable ran; no payload became a committed fixture.
- SYNTHETIC FIXTURE: image formats, malformed data, device responses, model conflicts,
  candidate generation and planner paths. Never described as real stock firmware or build evidence.
- REAL DEVICE: safe enumeration only when requested. Zero transports means NO DEVICE;
  passive detection cannot establish qualification.

## Honest limits

All new native formats have synthetic structure tests, not a comprehensive real-device corpus
qualification. Tree analysis is partial static resolution, not GNU Make evaluation. CPIO parsing
is bounded metadata inspection, not complete initramfs evaluation. LZ4 is structural only; native
decode/checksum validation is absent. FIT external data/signature evaluation and complete vendor
formats are absent. AVB metadata is not cryptographic, trusted-key or rollback verification.

Candidates deliberately retain TODOs. Models retain unknown/conflicting facts. Plans can be BLOCKED
while invocation succeeds. Actual TWRP compilation remains BLOCKED by the unqualified ARM64 path,
limited disk, missing prerequisites and incomplete source/device checkout. Hardware qualification
is UNTESTED. No huge sync, boot, flash, unlock, wipe, root or partition operation was performed.

CI uses a serial Python 3.11/3.13/3.14 matrix with no supplied archives. Local success is not external
CI proof; exact final-commit GitHub status is reported separately after push. No infrastructure
cause is inferred from missing workflow evidence.

Attribution auditing checks links/known names/provenance structure locally. Upstream retrieval
and explicit unavailable sources are recorded in research.json. Unestablished licenses remain
unestablished; no third-party source is incorporated, and credits never replace required notices.

## Completed local evidence

The final gate passed all seven commands, with **138 tests on Python 3.13.5**. The Termux Python 3.14.8 interpreter also exercises the full suite. This is interpreter evidence,
not complete PRoot/hardware platform qualification. The pipx installation was upgraded
from the built wheel to js 0.3.0; its sole console script is js. /usr/bin/js still resolves
to Node and no stale JADIS sec executable remains. All 15 isolated Image Lab installed-wheel
smoke invocations passed from /tmp, including model import, candidate derivation and a BLOCKED
plan. Source distribution includes CREDITS.md; wheel includes research metadata/native parsers
and no corpus payloads. Local YAML parsing confirms a serial CI matrix.

A 12,796-byte AIK-bundled ELF sample was read under a controlled temporary filename,
hash-checked against the inventory, structurally inspected and deleted without execution.
ELF structure passed; bootability/device compatibility remain UNTESTED. This CORPUS_SAMPLE
is separate from synthetic firmware fixtures and real host observations.

Before staging, 93 candidate source/documentation files total approximately 0.56 MiB,
with no .img/.zip/.pem/.pk8/.exe/.so/.jar payloads. Corpus archives remain outside Git.

The final 138-test suite also passed on Termux Python 3.14.8. A real NO_COLOR PTY
session displayed Image Lab/provider state, zero ADB/Fastboot transports and Recovery
Lab blockers, opened the Image Intelligence category, inspected operation context,
ran the read-only provider-availability operation and exited normally. Bash completion
syntax passed. The general installed-launcher harness completed 35 checks, including
the deliberate missing-image exit 3; all other invocations exited 0. Both transport
enumerations returned zero devices. The local ADB server started by probes was stopped.
Host planning is blocked by unqualified aarch64, free disk below 40 GiB, RAM below
the conservative 8 GiB floor, missing repo and no configured complete checkout/tree.
