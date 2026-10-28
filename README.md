# JADIS // SECRIPTS

**Personal Developer Operations Arsenal & Android Recovery/Image Laboratory**

CLI: **`js`** · Cockpit: **`js 1337`** · Recovery engineering: **`js ry`**

Secripts turns scattered commands and recovery-development knowledge into typed,
inspectable operations. Use it to understand a development environment, take Android
images apart safely, compare reconstructions, collect recovery evidence, and discover
what prevents a defensible build. It is Christopher Osburn / JADIS's independent
personal project, not an Outer Void universal CLI or control plane.

```text
                      JADIS // SECRIPTS
                             js
                              |
        +---------------------+---------------------+
        |                     |                     |
   DEV ARSENAL            IMAGE LAB            RECOVERY LAB
        |                     |                     |
        +---------------------+---------------------+
                              |
                       EVIDENCE / RECEIPTS
                              |
                   OPTIONAL AI EXPLANATION
```

**For beginners:** start with `js` in a terminal, or `js help recovery`.
**For Android developers:** inspect images, model conflicts, review trees and build plans.
**For advanced users:** use shorthand, JSON, registry contracts and explicit provider oracles.

## Install and start

Linux, Termux and Debian/PRoot are the supported host scope; runtime uses Python 3.11+
and the standard library. AOSP/TWRP compilation needs a separately suitable build host.

```sh
pipx install .
js --version
js --help
js guide
js doc
js dos
js fd recovery
js rcps
js 1337
```

For development, use `python -m pip install -e '.[dev]'`. Ensure the pipx bin directory
precedes unrelated system commands named `js`; `/usr/bin/js` may belong to Node.
Secripts installs only `js`, never a `sec` compatibility launcher.

## Three laboratories, one contract

- **Developer Arsenal:** Git/GitHub, Python/JVM, SDK, Termux/PRoot, SSH, host and local
  networking diagnostics. No automatic dependency upgrades or remote mutation.
- **Image Lab:** bounded boot v0–v4/vendor_boot, ramdisk/compression, DTB/DTBO, AVB and
  U-Boot intelligence; safe workspaces, reconstruction and comparisons.
- **Recovery Lab:** guided acquisition, source-linked device models, conflict detection,
  static tree diagnosis, review-only candidate derivation, source/host planning and
  conservative build-log diagnosis. TWRP is the only implemented build backend.
- **AI advice:** optional OpenAI, Claude and DeepSeek BYOK transports explain a bounded
  report after preview/hash approval. Models cannot run shell commands or upgrade facts.

```sh
js ry acquire --have images --json
js insp boot.img --json
js img rt boot.img --json
js ry tree diag /path/to/device-tree --json
js ry failure /path/to/build.log --json
js hist --summary --limit 10
```

Use actual local paths in these examples. Full descriptive spellings remain aliases:
`js inspect`, `js image roundtrip`, `js recovery`, `js doctor`, `js dossier`.

## What the evidence means

A command can complete successfully while its report contains BLOCKED, UNKNOWN, CONFLICT
or UNTESTED findings. Receipts answer what ran, with sanitized arguments, results and
artifact hashes. They are local execution evidence, not independent attestation.

Parsing is not verification. Reconstruction is not bootability. Compilation is not
hardware qualification. AI output is not evidence.

No flashing, unlocking, wiping, rooting or bypass is provided by this phase. Modified
signed images are refused. AVB chain/FEC and FIT signature verification remain partial.
Real TWRP compilation is blocked on the current ARM64 host; physical qualification is
untested. Synthetic fixtures and upstream oracle agreement do not change those states.

## Read the manual

| Start here | Continue here |
|---|---|
| [Getting Started](docs/GETTING-STARTED.md) | [CLI Guide](docs/CLI-GUIDE.md) and [complete generated reference](docs/COMMAND-REFERENCE.md) |
| [Recovery Guide](docs/RECOVERY-LAB.md) | [Build a Recovery](docs/BUILD-A-RECOVERY.md), [device models](docs/device-model.md), [trees](docs/DEVICE-TREES.md) |
| [Image Lab](docs/IMAGE-LAB.md) | [Ramdisk](docs/ramdisk.md), [AVB](docs/avb.md), [DTB/DTBO](docs/DTB-DTBO.md) |
| [AI](docs/AI.md) | [Evidence](docs/RECEIPTS-EVIDENCE.md) and [Safety](docs/safety-model.md) |
| [Architecture](docs/architecture.md) | [Development](docs/DEVELOPMENT.md) and [Research](docs/RESEARCH.md) |
| [Credits](CREDITS.md) | [Changelog](CHANGELOG.md) and [verification](docs/verification.md) |

Current counts are generated in the [operation catalog](docs/catalog.md) and
[recipe manual](docs/RECIPES.md). Research includes six pinned representative device
trees; these are research samples, not a device support list. See the
[Phase 5 gap gate](docs/research/phase5-gap-matrix.md) for unresolved coverage/licensing.
