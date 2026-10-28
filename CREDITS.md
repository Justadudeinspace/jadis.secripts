# JADIS // SECRIPTS — Credits & Attribution

JADIS // SECRIPTS is original personal developer operations software and an
Android Recovery/Image Laboratory. These credits identify material technical
lineage, rather than a list of everything encountered in an archive.

Research was reviewed on 2026-10-28. Detailed capability relationships and
access limitations are recorded in [research provenance](src/secripts/data/research.json)
and [corpus archaeology](docs/research.md). Specifications, historical research,
implementation influence and optional providers are distinguished below.
No third-party source or executable from the Phase 3 corpus is incorporated or
adapted in this release. Existing Secripts code was reorganized within the project.

## Core research & technical foundations

### Android Open Source Project

**Role:** Primary format and architecture reference for Android boot v0–v4,
vendor_boot v3/v4, init_boot context, DTBO and AVB metadata. The native parsers
are independent bounded implementations of documented structures.
**Upstream:** [boot image header](https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/include/bootimg/bootimg.h),
[DTBO header](https://android.googlesource.com/platform/system/libufdt/+/refs/heads/main/utils/src/dt_table.h),
[AVB](https://android.googlesource.com/platform/external/avb/).
**License:** Per-file upstream notices apply; Apache-2.0 was verified on the DTBO
header. This is not a project-wide licensing assertion.

### Team Win Recovery Project

**Role:** Recovery backend, build-source organization and device-tree research.
TWRP conventions inform static diagnosis; neither a parsed tree nor a build
plan establishes device support.
**Upstream:** [TeamWin recovery source](https://github.com/TeamWin/android_bootable_recovery).
**License:** See upstream per-file licenses. No recovery implementation is bundled.

### Android Image Kitchen — osm0sis

**Role:** Important historical integration/research source for content identification,
boot-image interoperability, ramdisks and vendor wrapper families. No bundled AIK
binary, script, signing key or certificate is trusted or shipped by Secripts.
**Upstream:** [Android Image Kitchen](https://github.com/osm0sis/Android-Image-Kitchen),
[authors.txt](https://raw.githubusercontent.com/osm0sis/Android-Image-Kitchen/master/authors.txt),
[original XDA thread](https://xdaforums.com/t/tool-android-image-kitchen-unpack-repack-kernel-ramdisk-win-android-linux-mac.2073775/).
**License:** An overall repository license was not established; bundled components
retain independent licenses. No AIK source was copied.

AIK's attribution identifies underlying projects rather than attributing every
utility to osm0sis. Relevant research lineage includes CyanogenMod's early
mkbootimg integration, srl3gx's elftool, tobiaswaldvogel's and_boot_tools/unpackelf,
OmniROM's MTK tooling, djrbliss's Loki, Rockchip tooling and U-Boot dumpimage.
These are historical format/integration references, not incorporated utilities.
The supplied XDA thread was inaccessible during review; no claim to have reviewed
its full discussion is made.

### file(1) / libmagic

**People:** Ian F. Darwin (original work), Christos Zoulas (maintainer), and the
contributors identified in upstream COPYING.
**Role:** Optional installed `file` evidence provider, with disagreements retained.
libmagic is not a required library and its classification database is not bundled.
**Upstream:** [file project](https://github.com/file/file),
[COPYING](https://raw.githubusercontent.com/file/file/master/COPYING).
**License:** BSD-style two-condition notice verified in COPYING. The supplied
Darwin website was unavailable; upstream attribution was checked instead.

### LZ4 — Yann Collet and contributors

**Role:** Primary frame-format reference for independent recognition and bounded
structural inspection of standard, legacy and skippable streams. Checksum
presence is inspected; checksum correctness and decompression are separate,
unimplemented native capabilities. Installed LZ4 tools are detected, not bundled.
**Upstream:** [LZ4](https://lz4.org/),
[frame specification](https://github.com/lz4/lz4/blob/dev/doc/lz4_Frame_format.md),
[license distinctions](https://github.com/lz4/lz4/blob/dev/LICENSE).
**License:** Library BSD-2-Clause; other source/programs GPL-2.0-or-later unless
specified otherwise. The specification has its own redistribution notice.

### Das U-Boot project and contributors

**Role:** Primary references for independent legacy uImage parsing and FDT-based
FIT identification. CRC checks do not establish signature validity or key trust.
**Upstream:** [official FIT documentation](https://docs.u-boot-project.org/en/latest/usage/fit/index.html),
[image interface](https://github.com/u-boot/u-boot/blob/master/include/image.h).
**License:** The referenced image header carries GPL-2.0+; no header is copied.
See upstream for documentation and other file licenses.

### Devicetree Specification contributors

**Role:** Primary reference for independent FDT header, token, strings and region
validation. FIT uses this shared parser.
**Upstream:** [Flattened Devicetree format](https://devicetree-specification.readthedocs.io/en/stable/flattened-format.html).
**License:** See upstream documentation license; no specification text is reproduced.

### Linux kernel contributors

**Role:** Linux UAPI ELF definitions inform bounded ELF metadata parsing.
The early-userspace buffer-format document, credited upstream to **Al Viro and
H. Peter Anvin**, informs newc/CRC CPIO inspection. Payloads are not executed or
extracted and no kernel source is incorporated.
**Upstream:** [ELF interface](https://github.com/torvalds/linux/blob/master/include/uapi/linux/elf.h),
[initramfs buffer format](https://www.kernel.org/doc/Documentation/early-userspace/buffer-format.txt).
**License:** ELF header GPL-2.0 WITH Linux-syscall-note; see upstream for the
buffer-format document's applicable licensing.

## Recovery development research

### lopestom

**Role:** Public recovery-development research and device-tree/firmware notes
inform the separation of dependencies, generation context and unresolved device
requirements. Community observations are research evidence, not format authority
or proof that a particular target builds.
**Upstream:** [lopestom public gists](https://gist.github.com/lopestom).
**License:** Not established for individual notes; no text or code copied.

### XDA Developers community

**Role:** Historical dissemination of Android recovery and image-tool research,
including AIK. Individual technical authors are credited only where upstream
attribution establishes their contribution. The supplied TWRP discussion and AIK
thread could not be retrieved; their contents are not claimed as verified sources.
**References:** [AIK thread](https://xdaforums.com/t/tool-android-image-kitchen-unpack-repack-kernel-ramdisk-win-android-linux-mac.2073775/),
[TWRP discussion supplied for research](https://xdaforums.com/t/dev-how-to-compile-twrp-touch-recovery.1943625/page-215#post-79086262).
**License:** See original authors and site terms; no posts reproduced.

### Cygwin project

**Role:** Portability/path and POSIX compatibility boundary research. This does
not establish Windows or Cygwin platform support in Secripts.
**Upstream:** [Cygwin](https://cygwin.com/), [licensing](https://cygwin.com/licensing.html).
**License:** Cygwin API LGPLv3-or-later with an exception; other tools have their
own licenses. No Cygwin components are redistributed.

## Historical Android image tooling

### OmniROM / MTK header tooling

**Role:** Historical header-layout research, traced through AIK to OmniROM and
AOSP, with osm0sis's later tooling. Secripts recognizes a bounded legacy MTK
header; it does not patch or flash it.
**Upstream evidence:** [mkmtkhdr source attribution](https://github.com/osm0sis/mkmtkhdr/blob/master/mkmtkhdr.c).
**License:** Not established for the complete historical tool; no source copied.

### Loki — djrbliss (Dan Rosenberg)

**Role:** Historical marker/layout reference only. No exploit, patch, unlock or
flash behavior is implemented or imported.
**Upstream:** [Loki](https://github.com/djrbliss/loki).
**License:** BSD-2-Clause verified in upstream [LICENSE.txt](https://github.com/djrbliss/loki/blob/master/LICENSE.txt),
which identifies Dan Rosenberg. No source incorporated.

### Rockchip tooling contributors

**Role:** AIK's upstream attribution and corpus README informed recognition of
historical Rockchip wrapper families. Marker recognition is explicitly partial,
not a complete Rockchip firmware parser or service tool.
**Upstream:** [Rockchip rkflashtool](https://github.com/rockchip-linux/rkflashtool).
**License:** The corpus version's complete license was not established. The historical
Rockchip upstream URL returned 404 during review; attribution is retained from AIK and
the corpus README, not from a currently retrievable repository.

## Optional external providers

Installed `file` and `avbtool` may be invoked only by explicit provider requests,
using fixed argument vectors and timeouts. `dtc`, `lz4`, `unlz4` and `cpio`
availability is reported without implying a working decode/verification adapter.
Provider tools are not bundled. Their upstream licensing remains independent.
A tool's presence does not establish successful verification.

## Research corpus

The supplied TWRP2.zip and TWRP3.zip archives were treated as untrusted read-only
research input. Hashes, bounded recursive coverage and classification counts are
recorded in [the corpus report](docs/research.md). Deeper sanitized attribution
records remain separate from these project-level credits. Corpus inclusion does
not imply incorporation, endorsement, authorship, redistribution or current
technical validity. Private key material is excluded; no signing keys are used.

## Licensing note

Secripts has its own [project license](LICENSE). Third-party projects retain their
copyrights and licenses. Credit changes neither project's license. If third-party
code is incorporated or adapted later, required source notices, license texts and
other obligations must be preserved separately; **this file is not a substitute**.
No attribution here is guessed. Unestablished licensing is identified explicitly.

## Attribution corrections and maintenance

Correct incomplete attribution when reliable upstream evidence becomes available.
Every meaningful capability influenced by identifiable outside work requires an
attribution and licensing review before it is complete. Update this human view
alongside the authoritative machine-readable research/capability provenance.

### Corpus integrity identifiers

- TWRP2.zip SHA-256: `709b6ab48d0af5791e52fb87e2562580a26aed154abac3416c4e11a4ba3bf7a9`
- TWRP3.zip SHA-256: `6de8c08236365cf18cceb4ed4a47972e5db2089cb4f093b1a8215bb513349d2e`
