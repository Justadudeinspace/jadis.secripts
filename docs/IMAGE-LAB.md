# Image Laboratory

Start with content identification rather than extensions. Inspecting metadata does not
execute a payload. The engine is independent of TWRP.

```sh
js insp IMAGE --json
js img model IMAGE --json
js img upk IMAGE --output NEW_WORKSPACE
js img ws NEW_WORKSPACE --json
js img rb NEW_WORKSPACE --output NEW_IMAGE
js img cmp IMAGE NEW_IMAGE --json
js img rt IMAGE --json
js prov --json
```

Workspaces preserve source hashes and extraction geometry. New outputs never overwrite
sources. Signed modifications are refused. Boot v0–v2 preserves layout; modern unsigned
boot/vendor_boot resizing has narrower tested contracts. Read the [support matrix](image-intelligence.md),
[workspaces](image-workspaces.md), [round-trip evidence](roundtrip.md), [ramdisk](ramdisk.md),
[DTB/DTBO](DTB-DTBO.md) and [AVB](avb.md).
