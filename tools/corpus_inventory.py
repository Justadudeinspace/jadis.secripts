"""Explicit local research job; raw corpus never enters the Git tree."""

import json
from secripts.corpus import inventory
from secripts.context import data_dir
from secripts.receipts import write_json

v = inventory(["/storage/emulated/0/TWRP2.zip", "/storage/emulated/0/TWRP3.zip"])
write_json(data_dir() / "research/corpus-inventory.json", v)
print(
    json.dumps(
        {
            k: v[k]
            for k in (
                "archives",
                "members",
                "bytes_streamed",
                "classifications",
                "families",
                "duplicates",
                "nested_containers",
            )
        },
        indent=2,
    )
)
print("Unresolved/bounded containers:", len(v["blockers"]))
