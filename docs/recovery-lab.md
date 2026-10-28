# Recovery Lab

Implemented: tool/workspace doctor, static tree evidence, image hashes and boot-header fields,
single authorized ADB device properties, explicit workspace configuration, source sync orchestration,
bounded TWRP build orchestration, artifact evidence and manual qualification reports.

Experimental: source/build integration. Environment-dependent: Android clients and source tools.
Hardware-dependent: every qualification result. Planned: validated temporary boot, multiple workspaces,
full ramdisk/AVB inspection and broader dependency resolution. Permanent flashing is intentionally absent.

Upstream reviewed 2026-10-28:

- [TeamWin compilation guidance](https://twrp.me/faq/howtocompiletwrp.html)
- [Minimal AOSP manifest, twrp-12.1](https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp/tree/twrp-12.1)
- [Manifest source organization](https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp/blob/twrp-12.1/default.xml)
- [TeamWin maintainer checks](https://twrp.me/faq/OfficialMaintainer.html)

The inspected manifest uses Android 12.1 platform sources. Its instructions choose recoveryimage,
bootimage or vendorbootimage according to the actual device layout; Secripts requires an explicit
choice. The upstream example enables missing dependencies; Secripts does not suppress them. Branch
selection is not a promise that a particular device or Android release works. Pin an appropriate
manifest revision and review the generated resolved source lock. No source updates happen during doctor.

Example preparation (replace every device-specific value):

```sh
sec recovery init example --root /work/twrp --tree /work/twrp/device/vendor/example \
  --manifest https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git \
  --revision twrp-12.1 --lunch twrp_example-eng --target vendorbootimage
sec recovery sync --dry-run
sec recovery tree audit /work/twrp/device/vendor/example --json
sec recovery build --dry-run
```

`sync` performs explicit repo init/sync and captures a revision-resolved manifest. It needs repo,
network and at least 40 GiB free; actual requirements may be higher. `build` requires an x86_64 host,
source checkout, local tree, resolved manifest and Git tree revision. It runs the trusted source build
system, limits jobs to two, captures bounded sanitized logs and collects only a newly produced artifact.
Build evidence is under the user data directory's `builds/<device>/<UTC-build-id>/` with build.json,
sources.lock.xml, tree-audit.json, build.log and hashes/images only when actually present.

The auditor parses declarations without make expansion. External includes, common/kernel dependencies
and undeclared partition layout remain UNRESOLVED. Recognized headers prove format fields only; no
architecture, AVB signature, decryption or hardware compatibility claim follows.

Qualification uses BLOCKING/MAJOR/MINOR severities inspired by TeamWin's checklist: display/touch,
backup/restore, system reboot and ADB are blocking. Extra local checks are extensions, not upstream
approval. Record explicit observations, including blocked/failed tests:

```sh
sec recovery test recovery.img --device owner-device
sec recovery test recovery.img --device owner-device --area touch --state BLOCKED --note 'No hardware available'
sec recovery report recovery.img --device owner-device --markdown
sec recovery report recovery.img --device owner-device --json
```

Records are artifact-hash and device-bound. No area starts PASS. A report can include a matching latest
build receipt; unrelated builds are not attached. Reports do not grant official TeamWin support.

The reviewed `twrp-12.1` manifest branch tip was
`6dc117d9cbd08430daa16db2013560e1c4017fa8` on 2026-10-28 (`git ls-remote`). This is a
reference observation, not a downloaded/qualified build. Every actual sync captures its own source lock.

Header layouts were checked against [AOSP bootimg.h](https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/include/bootimg/bootimg.h)
(blob `67ae349583e66424e5af0a3b7a386b42b6c958e0`) and
[AOSP vendor_boot layout](https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions).
Fields are independently parsed; upstream implementation code was not copied. Vendor header/page,
ramdisk/DTB/table/bootconfig bounds are checked; table entries are not unpacked or device-qualified.
