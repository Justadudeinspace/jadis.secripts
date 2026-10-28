# Recovery Laboratory

Start with `js ry acquire`: select what you actually have, understand why it matters,
and receive command templates. This does not download or unpack firmware, extract
protected device partitions, or declare support. Optional artifact/tree/model selectors
inspect explicit local evidence through existing engines.

```sh
js ry acquire --have identity --json
js ry acquire --have images --artifact boot.img --json
js ry source --json
js ry failure build.log --tree /path/to/tree --json
```

`js ry` in a TTY starts acquisition; non-TTY `js ry` keeps its existing doctor behavior.
Review the [beginner build path](BUILD-A-RECOVERY.md), [models](device-model.md),
[trees](DEVICE-TREES.md) and [TWRP workspace contract](TWRP-BUILD.md).
The detailed backend/reference material remains in [Recovery Lab architecture](recovery-lab.md).
