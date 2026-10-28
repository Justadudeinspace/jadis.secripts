# Complete command reference — 0.5.0

Generated from the authoritative parser. Do not edit by hand.

All accepted aliases use the same parser, operation identity and guards. Defaults below are parser defaults; explicit user-state paths follow XDG/SECRIPTS_DATA_HOME. Commands are Linux/Termux scoped.

JSON: `--json` emits uncolored machine data where listed. Invocation success is separate from evidence status. Registry execution writes sanitized receipts; help/listing do not. Image transformations require new outputs. Recovery mutations retain their existing guards. AI never sends without `--send --approve SHA256`; catalog requests require `--network`. Failures: 1 operation, 2 usage, 3 prerequisite, 4 safety refusal, 5 unsupported platform. Related contracts: [operations](catalog.md), [recipes](RECIPES.md), [evidence](RECEIPTS-EVIDENCE.md), [safety](safety-model.md).

## js

JADIS // SECRIPTS 0.5.0 — Personal Developer Operations Arsenal & Android Recovery Laboratory

```text
usage: js [-h] [--version] <command> ...
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --version | show program's version number and exit | '==SUPPRESS==' | optional |

## js help

Topic orientation and links to the manual

Aliases: none.

```text
usage: js help [-h] [--json] [{image,recovery,device,evidence,ai}]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| topic | Positional topic | None | image,recovery,device,evidence,ai |

## js guide

Guided entry; safe orientation without a TTY

Aliases: none.

```text
usage: js guide [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js ai

Optional provider-neutral advice; preview before external transmission

Aliases: none.

```text
usage: js ai [-h] [--json] {setup,prov,providers,models,context,ask,tools} ...
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js ai setup

Setup

Aliases: none.

```text
usage: js ai setup [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |

## js ai prov

Providers

Aliases: providers.

```text
usage: js ai prov [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |

## js ai models

Models

Aliases: none.

```text
usage: js ai models [-h] [--json] --provider {openai,claude,deepseek}
                    [--network]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --provider | Explicit provider selector | None | openai,claude,deepseek |
| --network | Explicit catalog request to the selected provider | False | optional |

## js ai context

Context

Aliases: none.

```text
usage: js ai context [-h] [--json] [--context CONTEXT]
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
usage: js ai ask [-h] [--json] --provider {openai,claude,deepseek}
                 [--context CONTEXT] [--model MODEL] [--send]
                 [--approve APPROVE]
                 question
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --provider | Explicit provider selector | None | openai,claude,deepseek |
| --context | Explicit bounded saved JSON report | None | optional |
| question | Positional question | None | required |
| --model | Explicit provider model ID; no default guessed | None | optional |
| --send | Transmit only after preview review and hash approval | False | optional |
| --approve | Exact SHA256 from context preview | None | optional |

## js ai tools

Tools

Aliases: none.

```text
usage: js ai tools [-h] [--json]
                   {registry.search,registry.show,receipt.summary} [argument]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| tool | Positional tool | None | registry.search,registry.show,receipt.summary |
| argument | Positional argument | '' | optional |

## js img

Offline artifact engineering with explicit evidence states

Aliases: image.

```text
usage: js img [-h] [--json]
              {insp,inspect,model,upk,unpack,ws,workspace,rb,rebuild,cmp,compare,rt,roundtrip,prov,providers,diff,differential} ...
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js img insp

Inspect

Aliases: inspect.

```text
usage: js img insp [-h] [--json] [--dry-run] [--providers] artifact
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
usage: js img model [-h] [--json] [--dry-run] artifact
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
usage: js img upk [-h] [--json] [--dry-run] --output OUTPUT artifact
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
usage: js img ws [-h] [--json] [--dry-run] workspace
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
usage: js img rb [-h] [--json] [--dry-run] --output OUTPUT workspace
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
usage: js img cmp [-h] [--json] [--dry-run] artifact other
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
usage: js img rt [-h] [--json] [--dry-run] [--output OUTPUT] artifact
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
usage: js img prov [-h] [--json] [--dry-run] [--probe]
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
usage: js img diff [-h] [--json] [--dry-run] --tools TOOLS artifact
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
usage: js ram [-h] [--json] {insp,inspect,ext,extract,pack,cmp,compare} ...
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js ram insp

Inspect

Aliases: inspect.

```text
usage: js ram insp [-h] [--json] [--dry-run] artifact
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
usage: js ram ext [-h] [--json] [--dry-run] --output OUTPUT artifact
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
usage: js ram pack [-h] [--json] [--dry-run] --output OUTPUT
                   [--compression {none,gzip,zlib,raw-deflate,xz,lzma-alone,bzip2,lz4}]
                   workspace
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --dry-run | Explicit dry_run selector | False | optional |
| workspace | Positional workspace | None | required |
| --output | Explicit output selector | None | required |
| --compression | Explicit compression selector | None | none,gzip,zlib,raw-deflate,xz,lzma-alone,bzip2,lz4 |

## js ram cmp

Compare

Aliases: compare.

```text
usage: js ram cmp [-h] [--json] [--dry-run] artifact other
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
usage: js dtbo [-h] [--json]
               {insp,inspect,ext,extract,rb,rebuild,cmp,compare} ...
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js dtbo insp

Inspect

Aliases: inspect.

```text
usage: js dtbo insp [-h] [--json] [--dry-run] artifact
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
usage: js dtbo ext [-h] [--json] [--dry-run] --output OUTPUT artifact
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
usage: js dtbo rb [-h] [--json] [--dry-run] --output OUTPUT workspace
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
usage: js dtbo cmp [-h] [--json] [--dry-run] artifact other
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
usage: js avb [-h] [--json] {insp,inspect,vfy,verify} ...
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js avb insp

Inspect

Aliases: inspect.

```text
usage: js avb insp [-h] [--json] [--dry-run] artifact
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
usage: js avb vfy [-h] [--json] [--dry-run] [--key KEY]
                  [--partition PARTITION]
                  artifact
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
usage: js insp [-h] [--json] [--dry-run] [--providers] path
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
usage: js prov [-h] [--json] [--probe] [--dry-run]
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
usage: js res [-h] [--json] archives [archives ...]
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
usage: js ls [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js fd

Ranked operation and recipe search

Aliases: find.

```text
usage: js fd [-h] [--json] [--category CATEGORY]
             [--risk {READ_ONLY,MUTATING,PRIVILEGED,DESTRUCTIVE}]
             [query]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| query | Positional query | '' | optional |
| --category | Explicit category selector | None | optional |
| --risk | Explicit risk selector | None | READ_ONLY,MUTATING,PRIVILEGED,DESTRUCTIVE |

## js dos

Collect cohesive local developer evidence; no network probes

Aliases: dossier.

```text
usage: js dos [-h] [--json] [--devices]
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
usage: js comp [-h] [--json] {bash,candidates} ...
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| shell | Positional shell | None | bash,candidates |
| words | Positional words | None | optional |

## js dce

Explicit read-only device inspection; identifiers omitted

Aliases: device.

```text
usage: js dce [-h] [--json] [--device DEVICE] {insp,transports,fastboot}
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| action | Positional action | None | inspect,transports,fastboot |
| --device | Select one transport; not retained in evidence | None | optional |

## js sh

Inspect an operation contract and provenance

Aliases: show.

```text
usage: js sh [-h] [--json] operation
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
usage: js exp [-h] [--json] operation
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
usage: js doc [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js run

Execute a registered operation with a local receipt

Aliases: none.

```text
usage: js run [-h] [--json] [--dry-run] [--tree TREE] [--artifact ARTIFACT]
              [--device DEVICE] [--model MODEL] [--output OUTPUT]
              [--other OTHER] [--workspace WORKSPACE]
              [--compression COMPRESSION] [--key KEY] [--tools TOOLS]
              [--have HAVE]
              operation
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
usage: js rcps [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js rcp

Inspect or execute a recipe

Aliases: recipe.

```text
usage: js rcp [-h] [--json] [--dry-run] [--network] [--tree TREE]
              [--artifact ARTIFACT] [--device DEVICE] [--model MODEL]
              [--output OUTPUT] [--other OTHER] [--workspace WORKSPACE]
              [--compression COMPRESSION] [--key KEY] [--tools TOOLS]
              [--have HAVE]
              {sh,run} name
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |
| action | Positional action | None | show,run |
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
usage: js hist [-h] [--json] [--operation OPERATION] [--failed]
               [--result RESULT] [--since SINCE] [--limit LIMIT]
               [--artifact ARTIFACT] [--summary]
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
usage: js rcpt [-h] [--json] [--failed] [--summary] id [other ...]
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
usage: js 1337 [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js arch

Inspect sanitized legacy lineage

Aliases: archaeology.

```text
usage: js arch [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js scan

Scan explicit files for secret classes; prints paths only

Aliases: none.

```text
usage: js scan [-h] [--json] paths [paths ...]
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
usage: js ing [-h] [--json] --output OUTPUT archive
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
usage: js ry [-h] [--json]
             {acquire,source,failure,doc,doctor,insp,inspect,tree,plan,dce,device,init,cfg,configure,sync,build,vfy,verify,boot,test,report,clean} ...
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Machine-readable output | False | optional |

## js ry acquire

Plan evidence acquisition; no firmware download or device extraction

Aliases: none.

```text
usage: js ry acquire [-h] [--json]
                     [--have {firmware,images,device,tree,recovery,kernel,identity}]
                     [--artifact ARTIFACT] [--tree TREE] [--model MODEL]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| --have | Explicit have selector | 'identity' | firmware,images,device,tree,recovery,kernel,identity |
| --artifact | Explicit artifact selector | None | optional |
| --tree | Explicit tree selector | None | optional |
| --model | Explicit model selector | None | optional |

## js ry source

Inspect manifest/toolchain declarations and researched generation options

Aliases: none.

```text
usage: js ry source [-h] [--json] [--workspace WORKSPACE]
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
usage: js ry failure [-h] [--json] [--tree TREE] artifact
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
usage: js ry doc [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |

## js ry insp

Inspect image headers or one authorized ADB device

Aliases: inspect.

```text
usage: js ry insp [-h] [--json] [--device] [image]
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
usage: js ry tree [-h] [--json] [--device MODEL] [--output OUTPUT] [--dry-run]
                  {audit,insp,diag,derive} [path]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| action | Positional action | None | audit,inspect,diagnose,derive |
| path | Positional path | None | optional |
| --device | Explicit model selector | None | optional |
| --output | Explicit output selector | None | optional |
| --dry-run | Explicit dry_run selector | False | optional |

## js ry plan

Build plan from model evidence; no source acquisition/build

Aliases: none.

```text
usage: js ry plan [-h] [--json] model
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
usage: js ry dce [-h] [--json]
                 {create,ls,add-image,add-tree,add-metadata,insp,report}
                 [name] [inputs ...]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| action | Positional action | None | create,list,add-image,add-tree,add-metadata,inspect,report |
| name | Positional name | None | optional |
| inputs | Positional inputs | None | optional |

## js ry init

Configure one isolated workspace; no source download

Aliases: none.

```text
usage: js ry init [-h] [--json] --root ROOT --tree TREE --manifest MANIFEST
                  --revision REVISION --lunch LUNCH
                  --target {recoveryimage,bootimage,vendorbootimage}
                  device
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
| --target | Explicit target selector | None | recoveryimage,bootimage,vendorbootimage |

## js ry cfg

Show the explicit workspace configuration

Aliases: configure.

```text
usage: js ry cfg [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |

## js ry sync

Explicit source synchronization

Aliases: none.

```text
usage: js ry sync [-h] [--json] [--dry-run]
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
usage: js ry build [-h] [--json] [--dry-run]
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
usage: js ry vfy [-h] [--json] artifact
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
usage: js ry boot [-h] [--json] artifact
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
usage: js ry test [-h] [--json] --device DEVICE [--area AREA]
                  [--state {PASS,FAIL,SKIPPED,BLOCKED,UNTESTED}] [--note NOTE]
                  artifact
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
| artifact | Positional artifact | None | required |
| --device | Explicit device selector | None | required |
| --area | Explicit area selector | None | optional |
| --state | Explicit state selector | None | PASS,FAIL,SKIPPED,BLOCKED,UNTESTED |
| --note | Explicit note selector | '' | optional |

## js ry report

Render artifact-bound qualification

Aliases: none.

```text
usage: js ry report [-h] [--json] [--device DEVICE] [--markdown] [--tree TREE]
                    [--device-evidence DEVICE_EVIDENCE]
                    artifact
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
usage: js ry clean [-h] [--json]
```

| Argument / option | Purpose | Default | Required / choices |
|---|---|---|---|
| -h, --help | show this help message and exit | '==SUPPRESS==' | optional |
| --json | Explicit json selector | False | optional |
