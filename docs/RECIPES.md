# Recipes — 0.5.0

28 recipes compose 92 available operations across 23 categories.

Inspect with `js rcp sh NAME`; preview `js rcp run NAME --dry-run`. Each step uses operation IDs, normal risk guards and linked receipts. Network steps require --network. Failure stops the recipe; a parent receipt keeps partial evidence. See [CLI](CLI-GUIDE.md).

## android-dev

Inspect SDK, runtimes and ADB before changing your environment.

Operations: `environment.runtimes`, `android.sdk.validate`, `adb.version`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## git-review

Inspect changes, branches, remotes and history before synchronization.

Operations: `git.status`, `git.branches`, `git.remotes`, `git.log`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## termux-check

Identify host boundaries and missing runtimes; no package upgrades.

Operations: `termux.inspect`, `environment.path`, `environment.runtimes`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## debian-check

Inspect build packages and runtimes before installing anything.

Operations: `debian.packages`, `environment.runtimes`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## device-diagnostic

Enumerate ADB and Fastboot transports without device modification.

Operations: `adb.devices`, `fastboot.devices`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## developer-environment

Inspect host, runtimes, filesystem and PATH before making changes.

Operations: `diagnostics.system`, `filesystem.capacity`, `python.environment`, `java.environment`, `environment.path`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## repository-health

Inspect worktree, divergence, object storage and submodules.

Operations: `git.health`, `git.objects`, `git.submodules`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## repository-release-readiness

Review tracked changes, untracked files, tags and Python build metadata. This does not authorize publishing.

Operations: `git.health`, `git.changed`, `git.untracked`, `git.tags`, `python.project`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## github-readiness

Explicit network checks for authentication, repository permissions and workflows.

Operations: `github.auth`, `github.repository`, `github.workflows`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## python-dev

Inspect interpreter isolation, project metadata, editables and dependency consistency.

Operations: `python.environment`, `python.project`, `python.editables`, `python.dependencies`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## android-sdk-health

Inspect SDK components and Java, then platform-tool versions without license acceptance.

Operations: `android.sdk.validate`, `java.environment`, `adb.version`, `fastboot.version`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## adb-diagnostics

Inspect client and sanitized transports; no device shell commands.

Operations: `adb.version`, `adb.devices`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## fastboot-diagnostics

Inspect client and sanitized bootloader enumeration without modifying a device.

Operations: `fastboot.version`, `fastboot.devices`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## android-device-dossier

Enumerate transports and collect allowlisted observations from one authorized device.

Operations: `adb.devices`, `adb.inspect`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## proot-dev

Inspect Linux and Termux context plus filesystem evidence without claiming native-host access.

Operations: `linux.environment`, `termux.inspect`, `filesystem.capacity`, `environment.path`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## recovery-readiness

Inspect host/build prerequisites, SDK and JDK; no source synchronization.

Operations: `recovery.doctor`, `android.sdk.validate`, `java.environment`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## twrp-tree-review

Audit a supplied tree and inspect the host without running makefiles.

Operations: `recovery.tree`, `recovery.doctor`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## twrp-build-readiness

Combine supplied-tree audit, build prerequisites, Java and disk evidence.

Operations: `recovery.tree`, `recovery.doctor`, `java.environment`, `filesystem.capacity`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## post-build-verification

Inspect an artifact and current workspace evidence; hardware qualification remains independent.

Operations: `recovery.image`, `recovery.doctor`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## image-analysis

Inspect image structures and optional-provider availability; no providers executed.

Operations: `image.inspect`, `image.providers`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## recovery-tree-diagnosis

Audit and explain unresolved tree/source dependencies.

Operations: `recovery.tree`, `recovery.diagnose`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## recovery-build-plan

Inspect model conflicts, host evidence and build blockers.

Operations: `recovery.model`, `recovery.host`, `recovery.plan`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## recovery-tree-derivation

Review model and generate a new traceable candidate, never a build-ready claim.

Operations: `recovery.model`, `recovery.derive`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## artifact-roundtrip

Model, reconstruct and compare offline artifacts; no compatibility claim.

Operations: `image.model`, `image.roundtrip`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## ramdisk-review

Inspect bounded CPIO/compression evidence alongside provider capability.

Operations: `ramdisk.inspect`, `image.providers`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## avb-evidence

Parse native metadata then explicitly verify with optional avbtool; device trust remains unknown.

Operations: `avb.inspect`, `avb.verify`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## recovery-onramp

Plan acquisition, inspect source declarations and qualify host constraints without a source download.

Operations: `recovery.acquire`, `recovery.source`, `recovery.host`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.

## build-failure-review

Correlate a bounded build log with current source intelligence; symptoms remain hypotheses.

Operations: `recovery.build.diagnose`, `recovery.source`.

Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.
