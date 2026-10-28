# DTB and DTBO

DTB is a flattened hardware-description tree. DTBO tables contain overlay blobs and
selection metadata. A well-formed tree does not prove a vendor binding is understood
or that a bootloader will select a particular overlay.

```sh
js insp DEVICE_TREE --json
js img model DEVICE_TREE --json
js dtbo insp DTBO --json
js dtbo ext DTBO --output NEW_WORKSPACE
js dtbo rb NEW_WORKSPACE --output NEW_DTBO
js dtbo cmp DTBO NEW_DTBO --json
```

Native FDT parsing supplies canonical comparison and bounds. Supported DTBO table
layouts preserve entries and shared blobs; unsupported extended metadata is refused
rather than discarded. Optional dtc/mkdtimg availability is distinct from differential
qualification. Vendor-property semantics and FIT signature trust remain partial.
[Full format support](image-intelligence.md).
