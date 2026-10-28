# Verification evidence — 0.2.0, 2026-10-28

## Baseline

Started on clean `main` at `e7a6ec0521062d68e167b3e8c88c35ae30bff9b9`. Local HEAD,
origin/main and an independent SSH remote query matched. The full v0.1 gate passed before edits:
57 tests, Ruff lint/format, secret scan (52 files, zero findings), source distribution and wheel.
The repository inventory and complete source/tests/docs were inspected before extension.

After the owner authenticated gh in a side terminal, this process immediately gained API access;
no Termux restart was needed. GitHub confirmed `private: true`, visibility private, default branch main.
No visibility setting was changed. Baseline workflow
[40624253253](https://github.com/Justadudeinspace/jadis.secripts/actions/runs/40624253253)
completed successfully: both Python 3.11 and 3.13 jobs passed install/lint/format/tests/scan/build/smoke.
A separate baseline run was queued when queried. No billing/infrastructure cause was inferred.

## Local Phase 2 evidence

Linux aarch64; Debian Python 3.13.5 and the Termux Python 3.14.8 interpreter. The expanded suite passes
**104 tests on each interpreter**. This does not establish a complete native Termux/PRoot or hardware
qualification matrix. Tests never contact devices/services or download Android sources.

The canonical installed launcher is `js`; Python distribution/package remain jadis-secripts/secripts.
Regression tests check source and installed console-script metadata expose only js, deterministic
`usage: js`, help/error examples and Bash completion. Existing operation IDs and runtime receipts remain
valid. The previous pipx `sec` symlink was positively associated with jadis-secripts 0.1.0; migration uses
a normal uninstall/install of that distribution. The unrelated `/usr/bin/js` Node launcher is preserved.

Validation commands:

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest -q
python tools/secret_scan.py
python -m build
python tools/qualify.py
python tools/validate.py --devices --network
```

`tools/qualify.py` captures actual local gate outcomes outside Git.
`tools/validate.py` exercises an installed entry point, not a module invocation:

```sh
js --help
js --version
js list --json
js find android --json
js show android.sdk.validate --json
js explain python.environment --json
js doctor --json
js dossier --json
js 1337
js 1337 --json
js recovery doctor --json
js run git.health --json
js run python.environment --json
js run python.project --json
js run java.environment --json
js run android.sdk.validate --json
js recipe run git-review --dry-run --json
js history --operation git.status --limit 2 --summary --json
js receipt latest --json
js receipt latest --failed --json
js completion bash
js run adb.devices --json
js run fastboot.devices --json
js run github.repository --json
js run github.workflows --json
```

The harness also checks tree/image/report commands against explicitly synthetic, temporary fixtures.
It deliberately requests a nonexistent image and checks failed-receipt retrieval. An earlier empty
failure history correctly returned prerequisite code 3; no PASS was manufactured for that absence.
Raw tool output stays in sanitized local execution evidence; device identifiers do not enter Git.

Real local Git/Python/Java/SDK observations and authenticated read-only GitHub metadata were collected.
ADB and Fastboot versions/enumerations executed, both reporting zero transports. ADB daemons started
by our enumeration were stopped afterward. No device shell/getvar interrogation or modification was
performed against real hardware. Synthetic device responses only prove parser/control behavior.

A real NO_COLOR PTY session displayed the live dashboard, opened history, previewed a Python operation,
entered Recovery Lab, ran doctor, returned and quit through `js://1337 >`. Non-TTY and JSON snapshots
were separately checked without device probes. Installed-wheel checks run from outside the checkout;
editable installation alone is not counted as wheel proof.

## Tests and static validation

Coverage includes original safety/failure paths plus all-operation dry-run contracts, typed parameters,
ranked/filter/provenance discovery, dossier/network boundaries, doctor uncertainty, cockpit preview/
NO_COLOR, recipe receipts/network refusal, receipt filters/diffs, old identifier sanitation, ADB absent/
multiple/unauthorized/offline/malformed responses, Fastboot absence/getvar evidence, deadlines, SDK
conflicts, malformed pyproject, image bounds, init_boot inference, vendor fragments, decompression bombs,
CPIO traversal, AVB footer/header/descriptor ranges, dependency cycles, symlinks, huge files, XML entities,
combined reports, and launcher metadata. Build/source success tests remain fixtures, not real TWRP builds.

Ruff lint and format checks pass. The repository secret scanner reports zero findings. Native parsing
is tested without external image dependencies. Generated catalog is compared against registry metadata.
Ruby's installed YAML parser validates workflow syntax and the serial matrix setting. Bash `-n` validates
completion syntax. CI now targets Python 3.11/3.13/3.14 with max-parallel 1, plus CLI/dossier/non-TTY and
completion smoke. Final-commit external status is queried after push and reported separately; baseline
CI success is not proof of the new commit.

## Capability limits

| Area | Evidence status |
|---|---|
| CLI, registry, discovery, receipts, recipes, dossier, doctor | PASS locally |
| Cockpit | PASS local PTY/non-TTY/JSON checks |
| Bash completion | PASS syntax/candidate tests; other shell-specific completion NOT IMPLEMENTED |
| SDK/JVM/Python | PASS inspection paths; build compatibility UNKNOWN/UNTESTED |
| ADB/Fastboot/device dossier | PARTIAL: fixture-tested plus real zero-device enumeration |
| Tree intelligence | PARTIAL: bounded static graph, no full Android Make evaluation |
| Boot/vendor_boot/init_boot inspection | PARTIAL: structure and bounded ramdisk metadata, not bootability |
| AVB | PARTIAL: untrusted metadata only; crypto/trust/rollback verification UNTESTED |
| TWRP orchestration | PARTIAL: existing fixture-tested adapter; no real sync/build |
| Actual TWRP compilation | BLOCKED on this host |
| Hardware qualification | UNTESTED |
| Private visibility | PASS authenticated API evidence |
| Baseline external CI | PASS authenticated run/job evidence |
| New commit external CI | Reported separately after push |

Real TWRP builds remain blocked by ARM64 host architecture, roughly 15 GiB free (below the 40 GiB
floor), missing repo/build prerequisites and no selected complete source/device-tree checkout. No
large download was attempted. No temporary boot, flash, unlock, wipe, repartition, automatic root or
ownership/security bypass was performed or added.

Remaining priorities: qualify a pinned real build on suitable x86_64 hardware; resolve complete Android
checkout dependencies; integrate explicit trusted upstream unpacking/AVB verification; then record
owner-authorized real device observations and manual qualification. Multiple workspaces, Zsh/Fish
completion and unsupported ramdisk decompressors remain future work.
