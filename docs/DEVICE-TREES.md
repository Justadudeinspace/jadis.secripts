# Device-tree review

A recovery tree is build configuration, not a hardware support certificate. JS analyzes
Make assignments/includes/inherited products, dependency declarations and configuration
without executing them. Conditions, external variables and checkout dependencies remain
explicitly unresolved.

```sh
js ry tree audit TREE --json
js ry tree diag TREE --json
js ry tree derive --device MODEL --output NEW_TREE --dry-run
```

Review products, architecture, kernel/prebuilt relationships, DTB/DTBO, recovery layout,
fstab, encryption/metadata, AVB, rootdir/init/VINTF, common/vendor dependencies and
missing paths. Static graph completion does not prove build-system evaluation.
Generated candidates keep line provenance plus RESOLVED/INFERRED/CONFLICT/UNKNOWN/
BLOCKED/REQUIRES_REVIEW summaries; unknown partition paths/sizes are not invented.

Six [pinned research trees](research/phase5-sources.json) illustrate configurations
across several platforms. They are not templates to copy blindly or a supported-device
list. Their full-tree redistribution licenses were not established; no trees are bundled.
