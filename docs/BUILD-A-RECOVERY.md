# I want to build a recovery for my phone. Where do I start?

Start with the exact **device variant and evidence**, not a build command. Recovery is
a small Android service environment used for repair/update workflows. Its kernel,
hardware support, partition layout and encryption integration must match the device.
A similarly named phone or a newer Android release is not a compatibility guarantee.

## 1. Learn the pieces

| Piece | Why it matters |
|---|---|
| boot | Kernel and, depending on generation, ramdisk; parsing does not determine partition role alone |
| vendor_boot | Vendor ramdisk, DTB and possibly typed vendor ramdisk fragments / bootconfig |
| init_boot | Generic ramdisk context in newer launch architectures; a kernel-less v4 file alone is insufficient identity |
| recovery | May be dedicated; other arrangements put recovery resources into boot/vendor_boot |
| A/B | Slot-based update architecture; not a synonym for recovery-as-boot |
| virtual A/B | Snapshot-based updates with dynamic partitions; not two independent full system copies |
| super / dynamic partitions | Container for logical partition allocation; static sizes and mapper names need evidence |
| vbmeta | AVB metadata and descriptors; signatures do not independently prove device trust |
| DTB / DTBO | Hardware description and overlays; kernel and bootloader relationships matter |
| kernel / modules | Hardware and filesystem drivers; prebuilt/source and vendor module strategies vary |
| fstab | Mount/partition/encryption declarations; guessing block paths can be dangerous |
| device tree | Build configuration, dependencies, kernel/DT references and recovery resources |
| recovery source | The selected TWRP/Android build generation and implementation |
| build host | Qualified Linux machine, enough storage/RAM and exact source toolchain |

Metadata encryption protects filesystem metadata; FBE protects file contents. A
decryption flag does not supply a working hardware/keymaster integration. Do not
copy security-bypass flags or signing keys from an example tree.

## 2. Say what you have

```sh
js help recovery
js ry acquire --have identity --json
js ry acquire --have images --json
js ry acquire --have tree --json
```

If you have firmware, preserve its original hash and source/device/build provenance.
Obtain it lawfully; do not execute its bundled tools. This release does not unpack
arbitrary firmware packages or download OEM files for you. Prefer reviewed extracted
partition images. If you only have a device, `js dce transports` and explicit authorized
read-only inspection may supplement evidence; no root or protected partition extraction.
Kernel source should have revision/config/licensing provenance, plus module/DT requirements.

## 3. Inspect and build an evidence model

```sh
js insp boot.img --json
js img model vendor_boot.img --json
js ry dce create example
js ry dce add-image example boot boot.img
js ry dce add-image example vendor_boot vendor_boot.img
js ry dce report example --json
```

Attach only files you have, with reviewed roles. Models store observations and their
source hashes. USER_SUPPLIED metadata remains an assertion. If architecture, recovery
arrangement or partition evidence conflicts, collect more evidence; do not vote away
the conflict. No model can synthesize the stock firmware you do not have.

## 4. Decide the recovery arrangement

- **Dedicated recovery:** an evidenced partition and matching tree can suggest
  recoveryimage. A filename or Android version does not establish it.
- **Recovery-as-boot:** inspect ramdisk and tree arrangement evidence; bootimage is
  a candidate only when that arrangement is supported.
- **Vendor_boot recovery:** review fragment types, ordering, DTB and vendor module
  requirements; vendorbootimage is a candidate, not automatically compatible.
- **Init_boot present:** keep its generic ramdisk role separate. Do not automatically
  select init_boot as a TWRP output target; this backend has no such target contract.
- **A/B, virtual A/B, dynamic partitions:** inspect these independently and reconcile
  fstab, common tree, super and metadata declarations. Retrofit arrangements need
  their own evidence; a launch-version shortcut is insufficient.

## 5. Review or derive a tree

```sh
js ry tree diag /path/to/tree --json
js ry dce add-tree example /path/to/tree
js ry tree derive --device example --output /existing/parent/candidate --dry-run
```

Derivation requires unambiguous architecture. Run without --dry-run only after
reviewing the proposed new output. A candidate intentionally leaves kernel, fstab,
partition sizes, common/vendor dependencies and source compatibility unresolved when
unknown. Read candidate.json, generated-line provenance and REVIEW.md. It is not a
working-device generator. Never run an untrusted Makefile merely to understand it.

## 6. Select source and host deliberately

```sh
js ry source --json
js ry doc --json
js ry plan example --json
```

Current researched TWRP sources include AOSP 12.1/11 and older Omni generations.
Choose using image/tree/kernel/encryption constraints and the exact branch README,
not the phone's installed Android version. JDK prebuilts in a manifest are declarations;
several can coexist. Inspect local build configuration for the active JDK/Python.
A modern host Java version does not qualify an old source branch.

For an external host, use x86_64 Linux with appropriate glibc, Git/Repo, Python,
branch-selected JDK and native build dependencies. Current full AOSP guidance uses
400 GB free disk and 64 GB RAM; reduced recovery checkouts vary. JS's early
40 GiB/8 GiB rejection floors are not a sufficient build-machine specification.
Review case-sensitive filesystem semantics, output mount, source revisions, device
tree revision, common/vendor/kernel dependencies and available memory. ARM64/PRoot
remains unqualified here. No huge source sync is needed merely to obtain a plan.

## 7. Configure, preview, then build only on the qualified host

Use [TWRP Build](TWRP-BUILD.md) for the explicit workspace contract and arguments.
`js ry sync --dry-run` shows source acquisition; `js ry build --dry-run` shows the
trusted-checkout build invocation. Real sync/build executes upstream source scripts
and consumes substantial resources. There is no implicit sync or dependency bypass.
Do not start a build while the plan remains blocked.

If a build fails:

```sh
js ry failure /path/to/build.log --tree /path/to/tree --json
```

Classification is a bounded symptom-based hypothesis. A nearby nsjail warning is
not proof of a Soong panic's root cause. Resolve exact missing modules/paths and
source revisions, rather than enabling missing-dependency suppression. Do not
disable SELinux, encryption or verification as an automatic diagnosis response.

## 8. Verify the artifact, then stop

```sh
js insp recovery.img --json
js img rt recovery.img --json
js ry report recovery.img --markdown
```

Use the artifact that actually exists; it may instead be boot.img/vendor_boot.img.
Build receipts capture revisions/logs/hashes, not proof of boot. Review AVB metadata
and explicit provider evidence separately. Hardware tests require a future explicit
owner-authorized mission. Do not flash or boot a phone under this workflow.

| Blocker | Next evidence |
|---|---|
| NO DEVICE | Continue offline; do not manufacture device evidence |
| UNKNOWN architecture / role | Inspect additional stock images and reviewed tree declarations |
| CONFLICT | Compare sources/revisions and variant identity |
| Missing common/vendor/kernel | Resolve dependency manifests and exact upstream revisions |
| Unknown Java/source | Inspect source manifests/build configuration and branch README |
| Host BLOCKED | Prepare suitable external host; retain a reproducible workspace contract |
| Candidate not build-ready | Complete every review item and re-audit |
| Crypto provider absent | Metadata remains inspectable; signature validity remains unavailable |
| Build succeeded | Inspect artifact; hardware still UNTESTED |

[Qualification boundaries](QUALIFICATION.md) explain the evidence required after a build.
