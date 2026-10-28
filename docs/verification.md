# Verification evidence — 2026-10-28

Baseline: `main`, clean working tree, commit `16e31ccce2a2f9f3b2e20ca3964dbf0a30621440`.
Origin SSH remote is `Justadudeinspace/jadis.secripts`; its main initially matched the baseline.
Repository visibility could not be established: unauthenticated GitHub access returned 404 and
`gh` had no authentication. No visibility setting was changed.

## Local evidence

Linux aarch64, Debian Python 3.13.5; installed editable using a virtual environment. Distribution
wheel installed separately with pipx and its registered `sec` entry point. A Python 3.14.8 Termux
interpreter also received the wheel for cross-interpreter checks inside the same Linux environment;
both interpreter suites passed 57 tests. This does not establish a full native Termux or PRoot qualification matrix. Newer Android OS reporting was explicitly regression-tested.

Commands executed:

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest -q
python tools/secret_scan.py
python -m build
pipx install --python /usr/bin/python3 dist/jadis_secripts-0.1.0-py3-none-any.whl
sec --help
sec --version
sec list --json
sec find android
sec doctor --json
sec 1337
sec recovery doctor --json
sec run git.status --json
sec run environment.path --json
sec run android.sdk.validate --json
sec run adb.version --json
sec run fastboot.version --json
sec run adb.devices --json
sec run fastboot.devices --json
```

The reproducible smoke set is `python tools/validate.py` with the installed entry point on PATH.
Full sanitized captures live in local runtime state, not Git. CLI smoke invocations above exited 0;
this means the inspections ran, not that all diagnosed prerequisites passed. SDK configuration and
individual tools may be missing. ADB and Fastboot version commands executed successfully; device
counts were both zero. The ADB daemon started by enumeration was stopped after the check.

A real PTY session exercised the described 1337 menu → Recovery Lab → doctor → back → quit path.
Unit tests separately exercise category selection, operation dry-run, archaeology and Recovery Lab.
The test suite has 57 cases, covering registry contracts, invalid IDs, safe argv handling, missing
executables, command failure/timeout, secret refusal/redaction, failed and corrupted receipts,
destructive confirmation and noninteractive refusal, missing Android clients, disconnected devices,
archive duplicates/secrets/unsafe paths/size limits, workspace validation/concurrency, tree findings,
image bounds, unavailable-network sync failure, insufficient disk, build failure/artifact collection
and qualification states. Recovery source/build tests use fixtures and mocks only.

## Limits and matrix

| Area | Evidence status |
|---|---|
| Architecture, package, CLI, registry, search, explain | PASS locally |
| Runner, risk guards, dry-run, receipts, redaction | PASS locally |
| Legacy classification and sanitized archaeology | PASS metadata workflow; eight intent reviews |
| Doctor and console/menu descriptions | PASS locally; full native Termux/PRoot UNTESTED |
| Recovery backend contract and doctor | PASS locally |
| Tree auditor | PARTIAL: static evidence; external make/dependencies unresolved |
| Image inspection | PARTIAL: hashes/headers/bounds; no ramdisk/AVB qualification |
| TWRP source workflow | PARTIAL: upstream reviewed and mocked workflow tested; no real sync |
| TWRP build | BLOCKED for real compilation; fixture orchestration tested |
| Hardware qualification | UNTESTED; no connected device |
| Recipes | PASS five diagnostic/preparation workflows; automated bootstrap not provided |
| Lint, tests, repository secret-class scan | PASS locally |
| CI | UNVERIFIED externally; workflow supplied, not claimed green |
| README | Matched against implemented command surface |

Real TWRP compilation is blocked by the ARM64 host, roughly 15 GiB free (below the 40 GiB floor),
missing repo/build prerequisites, and absence of a selected device tree/source checkout. No enormous
checkout was downloaded to manufacture evidence. No device was booted/flashed/unlocked/wiped.
Successful mocked artifact collection proves the collector, not a usable recovery image.

CI workflow syntax has been manually reviewed. Local YAML-parser validation was unavailable
(PyYAML was absent); external GitHub Actions results were not observed. Local success is independent
of GitHub billing/account infrastructure.

Priorities remaining: qualify the source/build adapter on a suitable x86_64 host with a real pinned
device tree; audit complete source dependencies; validate artifacts with upstream unpacking/AVB tools;
then perform owner-authorized manual hardware qualification. Only after that evidence should temporary
boot support be added. Completion, multiple workspaces and richer tree resolution come afterward.
