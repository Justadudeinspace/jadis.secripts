# Qualification

SOURCE REVIEW, TREE REVIEW, BUILD SUCCESS, IMAGE STRUCTURE, CRYPTOGRAPHIC VALIDITY,
DEVICE BOOT and HARDWARE QUALIFICATION are different evidence stages.

This mission performs no flashing or device boot. No connected device means UNTESTED.
For a future explicit owner-authorized qualification session, record artifact hash,
source/tree revisions, exact device variant and explicit manual observations.
The existing `js ry test` records attestations for boot/display/touch/ADB/reboots,
backup/restore, sideload, filesystems/data decryption, MTP/OTG and other documented
areas. It never auto-passes them. `js ry report` keeps untested/blocked areas visible.

A report is not official TeamWin acceptance. Review upstream maintainer requirements
and local [safety](safety-model.md) before a future hardware mission.
