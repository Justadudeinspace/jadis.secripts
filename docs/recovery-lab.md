# Recovery Lab

`js recovery` retains the backend protocol and one real backend, TWRP. Doctor, inspection, tree audit,
workspace configuration, source/build dry-run, fixture-tested orchestration, manual qualification and
combined reports are implemented. Real source sync/build remains experimental and unqualified here.

## Static intelligence

`js recovery tree audit TREE --json` inventories bounded local files without evaluating Make. The graph
records products, architecture, A/B and virtual A/B, dynamic partitions, recovery/vendor_boot layouts,
kernel/DTB/DTBO references, fstab, encryption/metadata partitions, AVB and dependency/manifest hints.

Evidence distinguishes DIRECTLY_DECLARED, STATICALLY_RESOLVED/INFERRED, EXTERNALLY_DEPENDENT and
UNRESOLVED. LOCAL_DIR and literal references within the audited inventory can resolve; arbitrary
Make expansion, conditional evaluation and external checkout traversal cannot. Cycles are reported.
Symlinks are not followed. DTD/entity/NUL XML is refused. Limits: 10,000 entries and 1 MiB per parsed file.
The graph is explicitly incomplete. A declaration is never a hardware PASS.

## Images and AVB

`js recovery inspect IMAGE --json` and `verify IMAGE` hash and statically parse, not certify, an image.
Android boot v0–v4 and vendor_boot v3/v4 layouts have bounded header/kernel/ramdisk/DTB/DTBO/signature/
bootconfig/table sections. Vendor fragment ranges are checked for overflow and overlap. A v4 ramdisk-only
image is an INFERRED init_boot candidate. Boot versus recovery partition role remains unresolved.

Gzip, bzip2 and XZ ramdisks can be decoded in memory; raw newc/CRC CPIO metadata is inspected without
extracting files or exposing payloads. LZ4 and Zstd magic is recognized; decompression remains optional
future tooling. Compressed regions over 16 MiB are not decoded; output is capped at 16 MiB per decode,
32 MiB per image, with a 64 MiB XZ decoder memory limit. CPIO names/entries are bounded. Only counts and
allowlisted boot/recovery marker names are returned. CRC checks and concatenated compression streams
are not validated; trailing data is reported.

Native AVB inspection recognizes end footers and standalone vbmeta, validates declared block and
descriptor ranges, and reports untrusted algorithm/rollback/flags and hash-descriptor partition names.
Other descriptor types remain tagged metadata. Signature validity, signer trust, rollback enforcement,
full descriptor semantics and compatibility are UNTESTED. A footer is never a VERIFIED image.
`avbtool` and `unpack_bootimg` are optional detected capabilities, not automatically invoked/installed.

## Devices and reports

`js recovery inspect --device` uses the same privacy-preserving dossier as `js device inspect`.
An explicit selection or sole authorized transport is required; root is not requested. Serials,
CPU serial fields and package names are omitted from returned evidence and captured commands.
This inspection does not infer device ownership or qualify recovery behavior.

```sh
js recovery test recovery.img --device OWNER_CHOSEN_ALIAS
js recovery test recovery.img --device OWNER_CHOSEN_ALIAS --area touch --state BLOCKED --note 'No hardware available'
js recovery report recovery.img --tree /path/to/tree --json
js recovery report recovery.img --markdown
```

Reports do not invent or auto-pass qualification records. They combine current workspace/tree audit,
dependency findings, image/hash/AVB evidence, a hash-matched successful recorded build and existing manual
attestations. `--device-evidence FILE` explicitly attaches a bounded saved JSON device dossier; it never
launches an implicit device probe. User-supplied evidence is labeled as such. Use an owner-chosen alias
for manual qualification, not a serial. Current tree evidence is not proof of historical build inputs.

SOURCE selection/lock, STATIC TREE REVIEW, BUILD SUCCESS, IMAGE STRUCTURE, DEVICE OBSERVATIONS and
DEVICE QUALIFICATION have separate states. BUILD SUCCESS never passes a hardware area. Reports remain
JSON/Markdown. TeamWin-inspired BLOCKING/MAJOR/MINOR areas require explicit evidence notes; no official
TeamWin qualification is asserted.

## TWRP workspace and source boundaries

```sh
js recovery init example --root /work/twrp --tree /work/twrp/device/vendor/example \
  --manifest https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git \
  --revision twrp-12.1 --lunch twrp_example-eng --target vendorbootimage
js recovery sync --dry-run
js recovery build --dry-run
```

Every value above is a device-specific example, not a recommended target. Source selection and build
partition target must be explicit. Sync uses repo init/sync and captures a resolved lock. No source
updates happen during doctor. Real sync/build needs repo, network, sufficient disk (40 GiB floor only),
a qualified x86_64 host, complete sources and a valid device tree. Source code is executable trusted
input. Missing dependencies are not suppressed. Workspace locking prevents concurrent mutations;
build and sync each limit jobs to two.

Existing artifact collection remains under the user-data directory's `builds/<device>/<build-id>/`:
actual new target image, hashes, build.json, sources.lock.xml, tree-audit.json and bounded sanitized log.
A source lock does not record arbitrary uncommitted changes across an entire Android checkout.
Temporary boot refuses unresolved device support/compatibility. Flash, unlock, wipe and repartition
remain absent. Multiple-workspace selection is not implemented.

## Upstream references and observed revisions

Reviewed format definitions, independently implemented; upstream code was not copied:

- [TeamWin compilation guidance](https://twrp.me/faq/howtocompiletwrp.html)
- [Minimal TWRP manifest](https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp/tree/twrp-12.1)
- [TeamWin maintainer checks](https://twrp.me/faq/OfficialMaintainer.html)
- [AOSP boot image layout](https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/include/bootimg/bootimg.h)
- [AVB footer](https://android.googlesource.com/platform/external/avb/+/refs/heads/main/libavb/avb_footer.h)
- [AVB vbmeta header](https://android.googlesource.com/platform/external/avb/+/refs/heads/main/libavb/avb_vbmeta_image.h)
- [AVB hash descriptor](https://android.googlesource.com/platform/external/avb/+/refs/heads/main/libavb/avb_hash_descriptor.h)

The manifest twrp-12.1 tip observed on 2026-10-28 was
`6dc117d9cbd08430daa16db2013560e1c4017fa8`; bootimg.h blob was
`67ae349583e66424e5af0a3b7a386b42b6c958e0`; vbmeta header blob was
`f9cbac447d0941429d813ca0aadef4401e7ec8d7`. These reference observations do not prove a downloaded,
compiled or device-tested recovery. No large Android checkout was downloaded for this release.
