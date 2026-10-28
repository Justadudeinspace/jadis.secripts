# Legacy archaeology

The archive was read in place from the user-supplied Android storage path. It was not extracted.
153 file members comprise Markdown, text, Python, shell, images and small configuration files.
SHA256 groups identify 27 duplicate members. Secret matches override every other classification.
All archive entries receive a decision; only eight safe technical sources received intent review
for extraction into this release. Other candidate material retains metadata without production claims.

The bounded ZIP reader refuses encrypted members, members over 8 MiB, total declared contents over
256 MiB and more than 10,000 entries. Unsafe paths never reach the filesystem. It records no arbitrary
source excerpts. A separate explicit review step rejects ownership-bypass/offensive filenames and
separate project plans. Pattern classification alone does not authorize promotion.

Reproduce with `js ingest /path/to/archive.zip --output /private/inventory.json`, then review decisions.
`tools/review_legacy.py` records this release's curated decisions; it is not a generic automatic
promotion engine. Never commit the archive, extraction directories or historical credential values.
