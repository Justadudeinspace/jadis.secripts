# Complete command reference — 0.5.0

Generated from the authoritative parser. Do not edit by hand.

All accepted aliases use the same parser, operation identity and guards. Defaults below are parser defaults; explicit user-state paths follow XDG/SECRIPTS_DATA_HOME. Commands are Linux/Termux scoped.

JSON: `--json` emits uncolored machine data where listed. Invocation success is separate from evidence status. Registry execution writes sanitized receipts; help/listing do not. Image transformations require new outputs. Recovery mutations retain their existing guards. AI never sends without `--send --approve SHA256`; catalog requests require `--network`. Failures: 1 operation, 2 usage, 3 prerequisite, 4 safety refusal, 5 unsupported platform. Related contracts: [operations](catalog.md), [recipes](RECIPES.md), [evidence](RECEIPTS-EVIDENCE.md), [safety](safety-model.md).

## js

JADIS // SECRIPTS 0.5.0 — Personal Developer Operations Arsenal & Android Recovery Laboratory

```text
js [COMMAND] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --version | show program's version number and exit | '==SUPPRESS==' | optional |

## js help

Topic orientation and links to the manual

Aliases: none.

```text
js help [TOPIC] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| topic | Positional topic | None | optional; image,recovery,device,evidence,ai |

## js guide

Guided entry; safe orientation without a TTY

Aliases: none.

```text
js guide [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js ai

Optional provider-neutral advice; preview before external transmission

Aliases: none.

```text
js ai [COMMAND] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js ai setup

Setup

Aliases: none.

```text
js ai setup [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |

## js ai prov

Providers

Aliases: providers.

```text
js ai prov [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |

## js ai models

Models

Aliases: none.

```text
js ai models [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --provider | Explicit provider selector | None | required; openai,claude,deepseek |
| --network | Explicit catalog request to the selected provider | False | optional |

## js ai context

Context

Aliases: none.

```text
js ai context [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --context | Explicit bounded saved JSON report | None | optional |

## js ai ask

Ask

Aliases: none.

```text
js ai ask QUESTION [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --provider | Explicit provider selector | None | required; openai,claude,deepseek |
| --context | Explicit bounded saved JSON report | None | optional |
| question | Positional question | None | required |
| --model | Explicit provider model ID; no default guessed | None | optional |
| --send | Transmit only after preview review and hash approval | False | optional |
| --approve | Exact SHA256 from context preview | None | optional |

## js ai tools

Tools

Aliases: none.

```text
js ai tools TOOL [ARGUMENT] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| tool | Positional tool | None | required; registry.search,registry.show,receipt.summary |
| argument | Positional argument | '' | optional |

## js img

Offline artifact engineering with explicit evidence states

Aliases: image.

```text
js img COMMAND [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js img insp

Inspect

Aliases: inspect.

```text
js img insp ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |
| --providers | Explicit providers selector | False | optional |

## js img model

Model

Aliases: none.

```text
js img model ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |

## js img upk

Unpack

Aliases: unpack.

```text
js img upk ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |
| --output | Explicit output selector | None | required |

## js img ws

Workspace

Aliases: workspace.

```text
js img ws WORKSPACE [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| workspace | Positional workspace | None | required |

## js img rb

Rebuild

Aliases: rebuild.

```text
js img rb WORKSPACE [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| workspace | Positional workspace | None | required |
| --output | Explicit output selector | None | required |

## js img cmp

Compare

Aliases: compare.

```text
js img cmp ARTIFACT OTHER [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |
| other | Positional other | None | required |

## js img rt

Roundtrip

Aliases: roundtrip.

```text
js img rt ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |
| --output | Explicit output selector | None | optional |

## js img prov

Providers

Aliases: providers.

```text
js img prov [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| --probe | Explicit bounded provider version probes | False | optional |

## js img diff

Differential

Aliases: differential.

```text
js img diff ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |
| --tools | Explicit tools selector | None | required |

## js ram

Offline artifact engineering with explicit evidence states

Aliases: ramdisk.

```text
js ram COMMAND [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js ram insp

Inspect

Aliases: inspect.

```text
js ram insp ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |

## js ram ext

Extract

Aliases: extract.

```text
js ram ext ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |
| --output | Explicit output selector | None | required |

## js ram pack

Pack

Aliases: none.

```text
js ram pack WORKSPACE [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| workspace | Positional workspace | None | required |
| --output | Explicit output selector | None | required |
| --compression | Explicit compression selector | None | optional; none,gzip,zlib,raw-deflate,xz,lzma-alone,bzip2,lz4 |

## js ram cmp

Compare

Aliases: compare.

```text
js ram cmp ARTIFACT OTHER [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |
| other | Positional other | None | required |

## js dtbo

Offline artifact engineering with explicit evidence states

Aliases: none.

```text
js dtbo COMMAND [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js dtbo insp

Inspect

Aliases: inspect.

```text
js dtbo insp ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |

## js dtbo ext

Extract

Aliases: extract.

```text
js dtbo ext ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |
| --output | Explicit output selector | None | required |

## js dtbo rb

Rebuild

Aliases: rebuild.

```text
js dtbo rb WORKSPACE [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| workspace | Positional workspace | None | required |
| --output | Explicit output selector | None | required |

## js dtbo cmp

Compare

Aliases: compare.

```text
js dtbo cmp ARTIFACT OTHER [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |
| other | Positional other | None | required |

## js avb

Offline artifact engineering with explicit evidence states

Aliases: none.

```text
js avb COMMAND [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js avb insp

Inspect

Aliases: inspect.

```text
js avb insp ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |

## js avb vfy

Verify

Aliases: verify.

```text
js avb vfy ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| artifact | Positional artifact | None | required |
| --key | Expected PEM public key only | None | optional |
| --partition | Explicit NAME=PATH companion image | [] | optional |

## js insp

Content-first Image Intelligence; no payload execution

Aliases: inspect.

```text
js insp PATH [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| path | Positional path | None | required |
| --dry-run | Explicit dry_run selector | False | optional |
| --providers | Explicitly invoke allowlisted installed metadata providers | False | optional |

## js prov

Inspect optional Image Lab providers; explicit version probes only

Aliases: providers.

```text
js prov [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| --probe | Explicit probe selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |

## js res

Bounded recursive corpus inventory; never executes members

Aliases: research.

```text
js res ARCHIVES [ARCHIVES ...] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| archives | Positional archives | None | required |

## js ls

List registered operations

Aliases: list.

```text
js ls [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js fd

Ranked operation and recipe search

Aliases: find.

```text
js fd [QUERY] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| query | Positional query | '' | optional |
| --category | Explicit category selector | None | optional |
| --risk | Explicit risk selector | None | optional; READ_ONLY,MUTATING,PRIVILEGED,DESTRUCTIVE |

## js dos

Collect cohesive local developer evidence; no network probes

Aliases: dossier.

```text
js dos [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| --devices | Explicitly enumerate transports; no device shell probing | False | optional |

## js comp

Generate Bash completion or list safe candidates

Aliases: completion.

```text
js comp SHELL [WORDS ...] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| shell | Positional shell | None | required; bash,candidates |
| words | Positional words | None | optional |

## js dce

Explicit read-only device inspection; identifiers omitted

Aliases: device.

```text
js dce ACTION [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| action | Positional action | None | required; inspect,transports,fastboot |
| --device | Select one transport; not retained in evidence | None | optional |

## js sh

Inspect an operation contract and provenance

Aliases: show.

```text
js sh OPERATION [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| operation | Positional operation | None | required |

## js exp

Inspect an operation contract and provenance

Aliases: explain.

```text
js exp OPERATION [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| operation | Positional operation | None | required |

## js doc

Inspect host tools without changing configuration

Aliases: doctor.

```text
js doc [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js run

Execute a registered operation with a local receipt

Aliases: none.

```text
js run OPERATION [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| operation | Positional operation | None | required |
| --dry-run | Explicit dry_run selector | False | optional |
| --tree | Explicit tree selector | None | optional |
| --artifact | Explicit artifact selector | None | optional |
| --device | Explicit device selector | None | optional |
| --model | Explicit model selector | None | optional |
| --output | Explicit output selector | None | optional |
| --other | Explicit other selector | None | optional |
| --workspace | Explicit workspace selector | None | optional |
| --compression | Explicit compression selector | None | optional |
| --key | Explicit key selector | None | optional |
| --tools | Explicit tools selector | None | optional |
| --have | Explicit have selector | None | optional |

## js rcps

List guided workflows

Aliases: recipes.

```text
js rcps [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js rcp

Inspect or execute a recipe

Aliases: recipe.

```text
js rcp ACTION NAME [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| action | Positional action | None | required; show,run |
| name | Positional name | None | required |
| --dry-run | Explicit dry_run selector | False | optional |
| --network | Explicit network selector | False | optional |
| --tree | Explicit tree selector | None | optional |
| --artifact | Explicit artifact selector | None | optional |
| --device | Explicit device selector | None | optional |
| --model | Explicit model selector | None | optional |
| --output | Explicit output selector | None | optional |
| --other | Explicit other selector | None | optional |
| --workspace | Explicit workspace selector | None | optional |
| --compression | Explicit compression selector | None | optional |
| --key | Explicit key selector | None | optional |
| --tools | Explicit tools selector | None | optional |
| --have | Explicit have selector | None | optional |

## js hist

Filter local receipts; no replay

Aliases: history.

```text
js hist [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| --operation | Explicit operation selector | None | optional |
| --failed | Explicit failed selector | False | optional |
| --result | Explicit result selector | None | optional |
| --since | Explicit since selector | None | optional |
| --limit | Explicit limit selector | None | optional |
| --artifact | Exact artifact path or SHA256 | None | optional |
| --summary | Explicit summary selector | False | optional |

## js rcpt

Read latest/ID or compare two sanitized receipts

Aliases: receipt, receipts.

```text
js rcpt ID [OTHER ...] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| id | Positional id | None | required |
| other | Positional other | None | optional |
| --failed | Explicit failed selector | False | optional |
| --summary | Explicit summary selector | False | optional |

## js 1337

Open the master operator console (preview without a TTY)

Aliases: none.

```text
js 1337 [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js arch

Inspect sanitized legacy lineage

Aliases: archaeology.

```text
js arch [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js scan

Scan explicit files for secret classes; prints paths only

Aliases: none.

```text
js scan PATHS [PATHS ...] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| paths | Positional paths | None | required |

## js ing

Inventory an untrusted ZIP without extracting contents

Aliases: ingest.

```text
js ing ARCHIVE [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| archive | Positional archive | None | required |
| --output | Explicit output selector | None | required |

## js ry

Android Recovery Laboratory (TWRP backend)

Aliases: recovery.

```text
js ry [COMMAND] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js ry acquire

Plan evidence acquisition; no firmware download or device extraction

Aliases: none.

```text
js ry acquire [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --have | Explicit have selector | 'identity' | optional; firmware,images,device,tree,recovery,kernel,identity |
| --artifact | Explicit artifact selector | None | optional |
| --tree | Explicit tree selector | None | optional |
| --model | Explicit model selector | None | optional |

## js ry source

Inspect manifest/toolchain declarations and researched generation options

Aliases: none.

```text
js ry source [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --workspace | Explicit workspace selector | None | optional |

## js ry failure

Conservative bounded build-log diagnosis; no automatic fixes

Aliases: none.

```text
js ry failure ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| artifact | Positional artifact | None | required |
| --tree | Explicit tree selector | None | optional |

## js ry doc

Check tools, workspace and unresolved hardware requirements

Aliases: doctor.

```text
js ry doc [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |

## js ry insp

Inspect image headers or one authorized ADB device

Aliases: inspect.

```text
js ry insp [IMAGE] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| image | Positional image | None | optional |
| --device | Explicit device selector | False | optional |

## js ry tree

Static device-tree evidence; never executes makefiles

Aliases: none.

```text
js ry tree ACTION [PATH] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| action | Positional action | None | required; audit,inspect,diagnose,derive |
| path | Positional path | None | optional |
| --device | Explicit model selector | None | optional |
| --output | Explicit output selector | None | optional |
| --dry-run | Explicit dry_run selector | False | optional |

## js ry plan

Build plan from model evidence; no source acquisition/build

Aliases: none.

```text
js ry plan MODEL [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| model | Positional model | None | required |

## js ry dce

Manage local evidence-backed recovery models

Aliases: device.

```text
js ry dce ACTION [NAME] [INPUTS ...] [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| action | Positional action | None | required; create,list,add-image,add-tree,add-metadata,inspect,report |
| name | Positional name | None | optional |
| inputs | Positional inputs | None | optional |

## js ry init

Configure one isolated workspace; no source download

Aliases: none.

```text
js ry init DEVICE [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| device | Positional device | None | required |
| --root | Explicit root selector | None | required |
| --tree | Explicit tree selector | None | required |
| --manifest | Explicit manifest selector | None | required |
| --revision | Explicit revision selector | None | required |
| --lunch | Explicit lunch selector | None | required |
| --target | Explicit target selector | None | required; recoveryimage,bootimage,vendorbootimage |

## js ry cfg

Show the explicit workspace configuration

Aliases: configure.

```text
js ry cfg [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |

## js ry sync

Explicit source synchronization

Aliases: none.

```text
js ry sync [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |

## js ry build

Compile trusted source; hardware remains untested

Aliases: none.

```text
js ry build [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |

## js ry vfy

Hash and statically inspect an artifact; no AVB qualification

Aliases: verify.

```text
js ry vfy ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| artifact | Positional artifact | None | required |

## js ry boot

Check temporary boot request; refuse unresolved support

Aliases: none.

```text
js ry boot ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| artifact | Positional artifact | None | required |

## js ry test

Record manual qualification evidence

Aliases: none.

```text
js ry test ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| artifact | Positional artifact | None | required |
| --device | Explicit device selector | None | required |
| --area | Explicit area selector | None | optional |
| --state | Explicit state selector | None | optional; PASS,FAIL,SKIPPED,BLOCKED,UNTESTED |
| --note | Explicit note selector | '' | optional |

## js ry report

Render artifact-bound qualification

Aliases: none.

```text
js ry report ARTIFACT [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| artifact | Positional artifact | None | required |
| --device | Explicit device selector | None | optional |
| --markdown | Explicit markdown selector | False | optional |
| --tree | Explicit tree selector | None | optional |
| --device-evidence | Explicit saved device dossier JSON; never collected implicitly | None | optional |

## js ry clean

Explain deliberate cleanup boundaries (no automatic deletion)

Aliases: none.

```text
js ry clean [options]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
