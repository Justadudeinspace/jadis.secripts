# TWRP build workspace contract

The only implemented recovery backend is TWRP. OrangeFox/Lineage/AOSP were researched
to separate generic Android knowledge from TWRP flags; they are not selectable backends.

Before configuration, record device/model, source manifest URL + explicit revision,
tree path/revision, common/vendor/kernel dependencies, lunch product and evidenced
output target. Retain local modifications separately: a repo lock does not attest
the entire checkout is unmodified.

```sh
js ry init example --root /work/twrp --tree /work/twrp/device/vendor/example --manifest https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git --revision twrp-12.1 --lunch twrp_example-eng --target recoveryimage
js ry cfg
js ry sync --dry-run
js ry build --dry-run
```

This is a syntax example, not a supported device target. Choose recoveryimage, bootimage
or vendorbootimage only from the arrangement evidence. The root/tree relationship is
guarded; output is isolated; workspace locking rejects concurrent mutations; jobs are
limited to two. Real source execution is explicit trusted input and must be reviewed.

Build output includes only actual artifacts, source lock, tree audit, bounded sanitized
log and hashes. Failed builds attach conservative symptom diagnosis. The current host
remains BLOCKED; no real TWRP compilation is claimed. See [Build a Recovery](BUILD-A-RECOVERY.md)
and [backend details](recovery-lab.md).
