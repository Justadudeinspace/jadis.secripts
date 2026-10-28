"""Fast argparse CLI. Probes and recovery imports are lazy."""

import argparse
import json
from pathlib import Path
import sys
from secripts import __version__
from secripts.commands import Parser, named, action_argument, normalize
from secripts.safety import SecError
from secripts.secrets import redact


def emit(value, machine=False):
    value = redact(value)
    if machine:
        print(json.dumps(value, indent=2, ensure_ascii=True, default=str))
    else:
        from secripts.ui.render import render

        print(render(value))


def parser() -> argparse.ArgumentParser:
    p = Parser(
        prog="js",
        description=f"JADIS // SECRIPTS {__version__} — Personal Developer Operations Arsenal & Android Recovery Laboratory",
        epilog="Short names are the working interface; descriptive names remain accepted aliases. See docs/cli.md for the complete map.",
    )
    p.add_argument("--version", action="version", version=f"js {__version__}")
    sub = p.add_subparsers(dest="command", metavar="<command>")

    def add(name, help_text):
        item = named(sub, name, dest="command", help_text=help_text)
        item.add_argument("--json", action="store_true", help="Machine-readable output")
        return item

    help_command = add("help", "Topic orientation and links to the manual")
    help_command.add_argument(
        "topic", nargs="?", choices=["image", "recovery", "device", "evidence", "ai"]
    )
    add("guide", "Guided entry; safe orientation without a TTY")
    ai = add("ai", "Optional provider-neutral advice; preview before external transmission")
    ais = ai.add_subparsers(dest="ai_action")
    for action in ("setup", "providers", "models", "context", "ask", "tools"):
        item = named(ais, action, dest="ai_action")
        item.add_argument("--json", action="store_true")
        if action in {"models", "ask"}:
            item.add_argument("--provider", choices=["openai", "claude", "deepseek"], required=True)
        if action == "models":
            item.add_argument(
                "--network",
                action="store_true",
                help="Explicit catalog request to the selected provider",
            )
        if action in {"context", "ask"}:
            item.add_argument("--context", type=Path, help="Explicit bounded saved JSON report")
        if action == "ask":
            item.add_argument("question")
            item.add_argument("--model", help="Explicit provider model ID; no default guessed")
            item.add_argument(
                "--send",
                action="store_true",
                help="Transmit only after preview review and hash approval",
            )
            item.add_argument("--approve", help="Exact SHA256 from context preview")
        if action == "tools":
            item.add_argument(
                "tool", choices=["registry.search", "registry.show", "receipt.summary"]
            )
            item.add_argument("argument", nargs="?", default="")
    engineering_commands = {
        "image": {
            "inspect": ("artifact",),
            "model": ("artifact",),
            "unpack": ("artifact",),
            "workspace": ("workspace",),
            "rebuild": ("workspace",),
            "compare": ("artifact", "other"),
            "roundtrip": ("artifact",),
            "providers": (),
            "differential": ("artifact",),
        },
        "ramdisk": {
            "inspect": ("artifact",),
            "extract": ("artifact",),
            "pack": ("workspace",),
            "compare": ("artifact", "other"),
        },
        "dtbo": {
            "inspect": ("artifact",),
            "extract": ("artifact",),
            "rebuild": ("workspace",),
            "compare": ("artifact", "other"),
        },
        "avb": {"inspect": ("artifact",), "verify": ("artifact",)},
    }
    for family, actions in engineering_commands.items():
        group = add(family, "Offline artifact engineering with explicit evidence states")
        actions_parser = group.add_subparsers(dest="engineering_action", required=True)
        for action, positional in actions.items():
            item = named(actions_parser, action, dest="engineering_action")
            item.add_argument("--json", action="store_true")
            item.add_argument("--dry-run", action="store_true")
            for parameter in positional:
                item.add_argument(parameter, type=Path)
            if action in {"unpack", "extract", "rebuild", "pack", "roundtrip"}:
                item.add_argument("--output", type=Path, required=action != "roundtrip")
            if family == "image" and action == "inspect":
                item.add_argument("--providers", action="store_true")
            if family == "image" and action == "differential":
                item.add_argument("--tools", type=Path, required=True)
            if family == "ramdisk" and action == "pack":
                item.add_argument(
                    "--compression",
                    choices=[
                        "none",
                        "gzip",
                        "zlib",
                        "raw-deflate",
                        "xz",
                        "lzma-alone",
                        "bzip2",
                        "lz4",
                    ],
                )
            if family == "avb" and action == "verify":
                item.add_argument("--key", type=Path, help="Expected PEM public key only")
                item.add_argument(
                    "--partition",
                    action="append",
                    default=[],
                    help="Explicit NAME=PATH companion image",
                )
            if family == "image" and action == "providers":
                item.add_argument(
                    "--probe", action="store_true", help="Explicit bounded provider version probes"
                )
    inspect = add("inspect", "Content-first Image Intelligence; no payload execution")
    inspect.add_argument("path", type=Path)
    inspect.add_argument("--dry-run", action="store_true")
    inspect.add_argument(
        "--providers",
        action="store_true",
        help="Explicitly invoke allowlisted installed metadata providers",
    )
    provider = add(
        "providers", "Inspect optional Image Lab providers; explicit version probes only"
    )
    provider.add_argument("--probe", action="store_true")
    provider.add_argument("--dry-run", action="store_true")
    corpus = add("research", "Bounded recursive corpus inventory; never executes members")
    corpus.add_argument("archives", nargs="+", type=Path)
    add("list", "List registered operations")
    find = add("find", "Ranked operation and recipe search")
    find.add_argument("query", nargs="?", default="")
    find.add_argument("--category")
    find.add_argument("--risk", choices=["READ_ONLY", "MUTATING", "PRIVILEGED", "DESTRUCTIVE"])
    dossier = add("dossier", "Collect cohesive local developer evidence; no network probes")
    dossier.add_argument(
        "--devices",
        action="store_true",
        help="Explicitly enumerate transports; no device shell probing",
    )
    completion = add("completion", "Generate Bash completion or list safe candidates")
    completion.add_argument("shell", choices=["bash", "candidates"])
    completion.add_argument("words", nargs=argparse.REMAINDER)
    device = add("device", "Explicit read-only device inspection; identifiers omitted")
    action_argument(device, "action", ["inspect", "transports", "fastboot"])
    device.add_argument("--device", help="Select one transport; not retained in evidence")
    for name in ("show", "explain"):
        add(name, "Inspect an operation contract and provenance").add_argument("operation")
    add("doctor", "Inspect host tools without changing configuration")
    r = add("run", "Execute a registered operation with a local receipt")
    r.add_argument("operation")
    r.add_argument("--dry-run", action="store_true")
    for name in (
        "tree",
        "artifact",
        "device",
        "model",
        "output",
        "other",
        "workspace",
        "compression",
        "key",
        "tools",
        "have",
    ):
        r.add_argument("--" + name)
    add("recipes", "List guided workflows")
    recipe = add("recipe", "Inspect or execute a recipe")
    action_argument(recipe, "action", ["show", "run"])
    recipe.add_argument("name")
    recipe.add_argument("--dry-run", action="store_true")
    recipe.add_argument("--network", action="store_true")
    for name in (
        "tree",
        "artifact",
        "device",
        "model",
        "output",
        "other",
        "workspace",
        "compression",
        "key",
        "tools",
        "have",
    ):
        recipe.add_argument("--" + name)
    hist = add("history", "Filter local receipts; no replay")
    hist.add_argument("--operation")
    hist.add_argument("--failed", action="store_true")
    hist.add_argument("--result")
    hist.add_argument("--since")
    hist.add_argument("--limit", type=int)
    hist.add_argument("--artifact", help="Exact artifact path or SHA256")
    hist.add_argument("--summary", action="store_true")
    receipt = add("receipt", "Read latest/ID or compare two sanitized receipts")
    receipt.add_argument("id")
    receipt.add_argument("other", nargs="*")
    receipt.add_argument("--failed", action="store_true")
    receipt.add_argument("--summary", action="store_true")
    add("1337", "Open the master operator console (preview without a TTY)")
    add("archaeology", "Inspect sanitized legacy lineage")
    scan = add("scan", "Scan explicit files for secret classes; prints paths only")
    scan.add_argument("paths", nargs="+", type=Path)
    ingest = add("ingest", "Inventory an untrusted ZIP without extracting contents")
    ingest.add_argument("archive", type=Path)
    ingest.add_argument("--output", required=True, type=Path)
    recovery = add("recovery", "Android Recovery Laboratory (TWRP backend)")
    rs = recovery.add_subparsers(dest="recovery_command")

    def rec(name, help_text):
        item = named(rs, name, dest="recovery_command", help_text=help_text)
        item.add_argument("--json", action="store_true")
        return item

    acquire = rec("acquire", "Plan evidence acquisition; no firmware download or device extraction")
    acquire.add_argument(
        "--have",
        choices=["firmware", "images", "device", "tree", "recovery", "kernel", "identity"],
        default="identity",
    )
    acquire.add_argument("--artifact", type=Path)
    acquire.add_argument("--tree", type=Path)
    acquire.add_argument("--model")
    source = rec(
        "source", "Inspect manifest/toolchain declarations and researched generation options"
    )
    source.add_argument("--workspace", type=Path)
    source.add_argument("inputs", nargs="*")
    source.add_argument("--lock", type=Path)
    for namespace in ("status", "graph", "fstab"):
        rec(namespace, "Evidence-backed recovery project " + namespace).add_argument("model")
    deps = rec("deps", "Reviewed pinned dependencies; acquisition requires --fetch")
    deps.add_argument("action", choices=["graph", "validate", "resolve"])
    deps.add_argument("model")
    deps.add_argument("--lock", type=Path)
    deps.add_argument("--root", type=Path)
    deps.add_argument("--fetch", action="store_true")
    deps.add_argument("--dry-run", action="store_true")
    flags = rec("flags", "Typed flag layers, overrides, validation and reusable profiles")
    flags.add_argument("inputs", nargs="*")
    flags.add_argument("--reason", default="")
    flags.add_argument("--acknowledge-conflict", action="store_true")
    flags.add_argument("--output", type=Path)
    flags.add_argument("--format", choices=["json", "make"], default="json")

    failure = rec("failure", "Conservative bounded build-log diagnosis; no automatic fixes")
    failure.add_argument("artifact", type=Path)
    failure.add_argument("--tree", type=Path)
    rec("doctor", "Check tools, workspace and unresolved hardware requirements")
    inspect = rec("inspect", "Inspect image headers or one authorized ADB device")
    inspect.add_argument("image", nargs="?", type=Path)
    inspect.add_argument("--device", action="store_true")
    tree = rec("tree", "Static device-tree evidence; never executes makefiles")
    action_argument(tree, "action", ["audit", "inspect", "diagnose", "derive"])
    tree.add_argument("path", type=Path, nargs="?")
    tree.add_argument("--device", dest="model")
    tree.add_argument("--output", type=Path)
    tree.add_argument("--dry-run", action="store_true")
    plan = rec("plan", "Build plan from model evidence; no source acquisition/build")
    plan.add_argument("model")
    device = rec("device", "Manage local evidence-backed recovery models")
    action_argument(
        device,
        "action",
        ["create", "list", "add-image", "add-tree", "add-metadata", "inspect", "report"],
    )
    device.add_argument("name", nargs="?")
    device.add_argument("inputs", nargs="*")
    init = rec("init", "Configure one isolated workspace; no source download")
    init.add_argument("device")
    for option in ("root", "tree"):
        init.add_argument(f"--{option}", required=True, type=Path)
    for option in ("manifest", "revision", "lunch"):
        init.add_argument(f"--{option}", required=True)
    init.add_argument(
        "--target",
        required=True,
        action="append",
        choices=["recoveryimage", "bootimage", "vendorbootimage", "initbootimage"],
    )
    init.add_argument("--model")
    rec("configure", "Show the explicit workspace configuration")
    for name in ("sync", "build"):
        item = rec(
            name,
            "Explicit source synchronization"
            if name == "sync"
            else "Compile trusted source; hardware remains untested",
        )
        item.add_argument("--dry-run", action="store_true")
    rec("verify", "Hash and statically inspect an artifact; no AVB qualification").add_argument(
        "artifact", type=Path
    )
    rec("boot", "Check temporary boot request; refuse unresolved support").add_argument(
        "artifact", type=Path
    )
    for name in ("test", "report"):
        item = rec(
            name,
            "Record manual qualification evidence"
            if name == "test"
            else "Render artifact-bound qualification",
        )
        item.add_argument("artifact", type=Path)
        item.add_argument("--device", required=name == "test")
        if name == "test":
            item.add_argument("--area")
            item.add_argument("--state", choices=["PASS", "FAIL", "SKIPPED", "BLOCKED", "UNTESTED"])
            item.add_argument("--note", default="")
        else:
            item.add_argument("--markdown", action="store_true")
            item.add_argument("--tree", type=Path)
            item.add_argument(
                "--device-evidence",
                type=Path,
                help="Explicit saved device dossier JSON; never collected implicitly",
            )
    rec("clean", "Explain deliberate cleanup boundaries (no automatic deletion)")
    return p


def recovery_dispatch(a):
    from secripts.context import host

    if host()["platform"] == "unsupported":
        raise SecError("Recovery Lab supports Linux and Termux hosts only", 5)
    from secripts.recovery import workspace as w
    from secripts.recovery.inspection import audit_tree, inspect_image
    from secripts.recovery.qualification import record, report, markdown
    from secripts.receipts import save
    from secripts.safety import Risk

    cmd = a.recovery_command
    if cmd == "flags":
        from secripts.recovery.flag_cli import dispatch as flag_dispatch

        return flag_dispatch(a)
    if cmd == "status":
        from secripts.recovery.projects import status

        return status(a.model)
    if cmd in {"graph", "fstab"}:
        from secripts.recovery import model, flags, architecture, fstab

        device = model.report(a.model)
        return (
            architecture.graph(device, flags.view(a.model))
            if cmd == "graph"
            else fstab.report(device)
        )
    if cmd == "deps":
        from secripts.recovery import dependencies

        if a.lock:
            selected = dependencies.select(a.model, a.lock, a.dry_run)
            if a.dry_run:
                return selected
        if a.action == "graph":
            return dependencies.graph(a.model)
        if a.action == "validate":
            return dependencies.validate(a.model)
        return dependencies.resolve(a.model, root=a.root, fetch=a.fetch, dry_run=a.dry_run)
    if cmd == "source" and a.inputs:
        from secripts.recovery.dependencies import source

        action = a.inputs[0] if a.inputs[0] in {"resolve", "validate"} else "inspect"
        inputs = a.inputs[1:] if action != "inspect" else a.inputs
        if len(inputs) != 1:
            raise SecError("Use source [resolve|validate] MODEL [--lock FILE]", 2)
        return source(inputs[0], action, a.lock)
    if cmd in {"acquire", "failure", "source"}:
        from secripts.operations import execute

        if (
            cmd == "acquire"
            and a.have == "identity"
            and not a.json
            and sys.stdin.isatty()
            and sys.stdout.isatty()
        ):
            from secripts.recovery.guidance import INPUTS

            for i, (_key, (title, why)) in enumerate(INPUTS.items(), 1):
                print(f"[{i}] {title}\n    {why}")
            choice = input("Evidence number (blank for identity guidance) > ").strip()
            if choice:
                if not choice.isdecimal() or not 1 <= int(choice) <= len(INPUTS):
                    raise SecError("Choose a displayed evidence number", 2)
                a.have = list(INPUTS)[int(choice) - 1]
        keys = {
            "acquire": ("have", "artifact", "tree", "model"),
            "failure": ("artifact", "tree"),
            "source": ("workspace",),
        }[cmd]
        return execute(
            {
                "acquire": "recovery.acquire",
                "failure": "recovery.build.diagnose",
                "source": "recovery.source",
            }[cmd],
            parameters={k: str(getattr(a, k)) for k in keys if getattr(a, k, None) is not None},
        )
    if cmd in (None, "doctor"):
        return w.recovery_doctor()
    if cmd == "device":
        from secripts.recovery import model

        if a.action == "list":
            return model.catalog()
        if not a.name:
            raise SecError("Device model name required", 2)
        if a.action == "create":
            return model.create(a.name)
        if a.action in ("inspect", "report"):
            return model.report(a.name)
        if a.action == "add-image" and len(a.inputs) == 2:
            return model.add_image(a.name, a.inputs[0], Path(a.inputs[1]))
        if a.action == "add-tree" and len(a.inputs) == 1:
            return model.add_tree(a.name, Path(a.inputs[0]))
        if a.action == "add-metadata" and len(a.inputs) == 1:
            return model.add_metadata(a.name, Path(a.inputs[0]))
        raise SecError("Invalid device evidence arguments; use --help", 2)
    if cmd == "plan":
        from secripts.operations import execute

        return execute("recovery.plan", parameters={"model": a.model})
    if cmd == "tree":
        from secripts.recovery.planner import derive, diagnose

        if a.action == "derive":
            if not a.model or not a.output:
                raise SecError("Derivation requires --device MODEL --output PATH", 2)
            return derive(a.model, a.output, a.dry_run)
        if a.path is None:
            raise SecError("Tree path required", 2)
        return diagnose(a.path) if a.action == "diagnose" else audit_tree(a.path)
    if cmd in ("inspect", "verify"):
        if cmd == "inspect" and a.device:
            if a.image:
                raise SecError("Choose image or --device", 2)
            from secripts.recovery.device import inspect_device

            value = inspect_device()
        else:
            path = a.image if cmd == "inspect" else a.artifact
            if path is None:
                raise SecError("Image path or --device required", 2)
            value = inspect_image(path)
        receipt = save(
            f"recovery.{cmd}",
            Risk.READ_ONLY,
            value.get("commands", []),
            result="PASS",
            evidence=value,
        )
        return {**value, "receipt_id": receipt["receipt_id"]}
    if cmd == "init":
        print(
            "PLAN: create local workspace configuration; no download. "
            "Review the explicit arguments supplied to init.",
            file=sys.stderr,
        )
        return w.initialize(
            a.root,
            a.device,
            a.tree,
            a.manifest,
            a.revision,
            a.lunch,
            a.target[0],
            targets=a.target,
            model=a.model,
        )
    if cmd == "configure":
        return w.load_workspace()
    if cmd == "sync":
        print(
            "PLAN: repo init and sync the explicitly configured source; network and disk writes. "
            "Use --dry-run to preview arguments.",
            file=sys.stderr,
        )
        return w.sync(a.dry_run)
    if cmd == "build":
        print(
            "PLAN: execute trusted source build scripts, write output and collect evidence; "
            "hardware remains UNTESTED. Use --dry-run to preview.",
            file=sys.stderr,
        )
        return w.build(a.dry_run)
    if cmd == "boot":
        inspect_image(a.artifact)
        raise SecError(
            "Temporary boot refused: device-specific fastboot boot support and image compatibility are UNRESOLVED. No boot command was sent.",
            4,
        )
    if cmd == "test":
        if bool(a.area) != bool(a.state):
            raise SecError("--area and --state must be supplied together", 2)
        return record(a.artifact, a.device, a.area, a.state, a.note)
    if cmd == "report":
        value = report(a.artifact, a.device, tree=a.tree, device_evidence=a.device_evidence)
        return markdown(value) if a.markdown else value
    if cmd == "clean":
        return {
            "result": "NO_ACTION",
            "guidance": "Inspect js ry cfg and local build receipts. Remove only individually reviewed build directories; js does not delete sources or artifacts automatically.",
        }


def dispatch(a):
    from secripts.registry import registry

    cmd = a.command
    if cmd in {"help", "guide"}:
        from secripts.ui.guide import topic

        return topic(a.topic) if cmd == "help" else topic()
    if cmd == "ai":
        from secripts.ai import providers, context, tools, service

        if a.ai_action in {None, "setup", "providers"}:
            return providers.catalog()
        if a.ai_action == "context":
            return context.preview(a.context)
        if a.ai_action == "models":
            if not a.network:
                return {
                    "status": "UNTESTED",
                    "guidance": "Use --network for an explicit authenticated model catalog request; no inference occurs",
                }
            return context.clean(providers.transport(providers.provider(a.provider), listing=True))
        if a.ai_action == "tools":
            return context.preview(value=tools.invoke(a.tool, a.argument))
        return service.ask(
            a.question,
            provider=a.provider,
            model=a.model,
            path=a.context,
            send=a.send,
            expected=a.approve,
        )
    if cmd == "providers":
        from secripts.images.providers import inventory

        return {"planned": "Provider inspection"} if a.dry_run else inventory(probe=a.probe)
    if cmd in {"image", "ramdisk", "dtbo", "avb"}:
        from secripts.operations import execute

        if cmd == "image" and a.engineering_action == "providers":
            from secripts.images.providers import inventory

            return inventory(probe=a.probe)
        parameters = {
            name: str(getattr(a, name))
            for name in ("artifact", "other", "workspace", "output", "compression", "key", "tools")
            if getattr(a, name, None) is not None
        }
        if cmd == "avb" and a.engineering_action == "verify" and a.partition and not a.dry_run:
            from secripts.images.avbmodel import verify

            companions = {}
            for specification in a.partition:
                if "=" not in specification:
                    raise SecError("Companion must be NAME=PATH", 2)
                name, path = specification.split("=", 1)
                if name in companions:
                    raise SecError("Duplicate companion name", 2)
                companions[name] = Path(path)
            return verify(a.artifact, expected_key=a.key, partitions=companions)
        return execute(cmd + "." + a.engineering_action, a.dry_run, parameters)
    if cmd == "inspect":
        from secripts.images.engine import inspect, inspection_failed
        from secripts.receipts import save

        if a.dry_run:
            from secripts.operations import execute

            return execute("image.inspect", True, {"artifact": str(a.path)})
        value = inspect(a.path, providers=a.providers)
        receipt = save(
            "image.inspect",
            "READ_ONLY",
            [],
            result="FAIL" if inspection_failed(value) else "PASS",
            file_sha256=value["sha256"],
            parser_version=value["parser_version"],
            evidence=value,
            warnings=value["warnings"],
            unresolved=value["qualification"],
        )
        return {
            **value,
            "receipt_id": receipt["receipt_id"],
            "exit_code": 1 if inspection_failed(value) else 0,
        }
    if cmd == "research":
        from secripts.corpus import inventory
        from secripts.context import data_dir
        from secripts.receipts import write_json, save

        value = inventory(a.archives)
        output = data_dir() / "research/corpus-inventory.json"
        write_json(output, value)
        receipt = save(
            "research.inventory",
            "READ_ONLY",
            [],
            result="PASS",
            artifacts=[{"path": str(output)}],
            warnings=["No corpus contents imported or executed"],
        )
        return {k: v for k, v in value.items() if k != "components"} | {
            "receipt_id": receipt["receipt_id"]
        }
    if cmd == "dossier":
        from secripts.dossier import dossier

        return dossier(devices=a.devices)
    if cmd == "completion":
        from secripts.completion import bash, candidates

        return (
            bash()
            if a.shell == "bash"
            else "\n".join(candidates([w for w in a.words if w != "--"]))
        )
    if cmd == "device":
        from secripts.operations import execute

        if a.action == "transports":
            return {"adb": execute("adb.devices"), "fastboot": execute("fastboot.devices")}
        return execute(
            "adb.inspect" if a.action == "inspect" else "fastboot.inspect",
            parameters={"device": a.device},
        )
    if cmd == "list":
        return [o.metadata() for o in registry().search()]
    if cmd == "find":
        from secripts.recipes import RECIPES

        return {
            "operations": [
                o.metadata() for o in registry().search(a.query, category=a.category, risk=a.risk)
            ],
            "recipes": {
                k: v
                for k, v in RECIPES.items()
                if all(w in str((k, v)).lower() for w in a.query.lower().split())
                and (
                    not a.category
                    or any(registry().get(op).category == a.category for op in v["operations"])
                )
                and (not a.risk or all(registry().get(op).risk == a.risk for op in v["operations"]))
            },
        }
    if cmd in ("show", "explain"):
        metadata = registry().get(a.operation).metadata()
        if cmd == "explain":
            from importlib.resources import files

            records = json.loads(files("secripts").joinpath("data/operations.json").read_text())
            metadata["provenance"] = next(
                r for r in records["operations"] if r["operation"] == a.operation
            )
        return metadata
    if cmd == "doctor":
        from secripts.doctor import doctor

        return doctor()
    if cmd == "run":
        from secripts.operations import execute

        return execute(
            a.operation,
            a.dry_run,
            {
                k: getattr(a, k)
                for k in (
                    "tree",
                    "artifact",
                    "device",
                    "model",
                    "output",
                    "other",
                    "workspace",
                    "compression",
                    "key",
                    "tools",
                    "have",
                )
            },
        )
    if cmd in ("recipes", "recipe"):
        from secripts.recipes import RECIPES, get, run

        return (
            RECIPES
            if cmd == "recipes"
            else get(a.name)
            if a.action == "show"
            else run(
                a.name,
                a.dry_run,
                {
                    k: getattr(a, k)
                    for k in (
                        "tree",
                        "artifact",
                        "device",
                        "model",
                        "output",
                        "other",
                        "workspace",
                        "compression",
                        "key",
                        "tools",
                        "have",
                    )
                },
                network=a.network,
            )
        )
    if cmd in ("history", "receipt"):
        from secripts.receipts import history, load, latest, summary, compare

        if cmd == "history":
            rows = history(
                operation=a.operation,
                failed=a.failed,
                limit=a.limit,
                since=a.since,
                result=a.result,
                artifact=a.artifact,
            )
            return [summary(row) for row in rows] if a.summary else rows
        if a.id == "diff":
            if len(a.other) != 2:
                raise SecError("Use js receipt diff ID1 ID2", 2)
            return compare(*a.other)
        if a.other:
            raise SecError("Unexpected receipt arguments", 2)
        value = latest(failed=a.failed) if a.id == "latest" else load(a.id)
        return summary(value) if a.summary else value
    if cmd == "archaeology":
        from secripts.provenance import packaged

        return packaged()
    if cmd == "ingest":
        from secripts.provenance import ingest

        value = ingest(a.archive, a.output)
        return {k: v for k, v in value.items() if k != "artifacts"}
    if cmd == "scan":
        from secripts.secrets import scan_paths

        if any(not p.is_file() for p in a.paths):
            raise SecError("Scan inputs must be existing regular files", 2)
        findings = scan_paths(a.paths)
        return {"findings": findings, "exit_code": 1 if findings else 0}
    if cmd == "recovery":
        return recovery_dispatch(a)


def main(argv=None) -> int:
    p = parser()
    arguments = list(sys.argv[1:] if argv is None else argv)
    # Namespace entry is useful without weakening required arguments for its actual actions.
    if len(arguments) == 1 and arguments[0] in {"img", "image", "ram", "ramdisk", "avb", "dtbo"}:
        try:
            p.parse_args([*arguments, "--help"])
        except SystemExit as exc:
            return int(exc.code)
    if arguments in (["ry"], ["recovery"]) and sys.stdin.isatty() and sys.stdout.isatty():
        return main(["ry", "acquire"])
    a = normalize(p.parse_args(arguments))
    if a.command is None:
        if sys.stdin.isatty() and sys.stdout.isatty():
            from secripts.ui.guide import guide

            return guide(emit)
        p.print_help()
        return 0
    try:
        if a.command == "guide" and not a.json:
            from secripts.ui.guide import guide

            return guide(emit)
        if a.command == "1337":
            from secripts.ui.console import console, dashboard

            if a.json:
                emit(dashboard(devices=False), True)
                return 0
            return console(emit)
        value = dispatch(a)
        emit(value, getattr(a, "json", False))
        return value.get("exit_code", 0) if isinstance(value, dict) else 0
    except SecError as exc:
        evidence = {"error": str(exc), "exit_code": exc.code}
        if a.command == "inspect" or (
            a.command == "recovery"
            and a.recovery_command
            in (
                "sync",
                "build",
                "boot",
                "inspect",
                "verify",
            )
        ):
            from secripts.receipts import save

            try:
                evidence["receipt_id"] = save(
                    "image.inspect" if a.command == "inspect" else f"recovery.{a.recovery_command}",
                    "MUTATING"
                    if getattr(a, "recovery_command", None) in ("sync", "build", "boot")
                    else "READ_ONLY",
                    [],
                    result="REFUSED" if exc.code == 4 else "FAIL",
                    warnings=[str(exc)],
                )["receipt_id"]
            except OSError:
                evidence["receipt_warning"] = (
                    "Could not persist failure receipt; inspect state-directory permissions/free space"
                )
        emit(evidence, getattr(a, "json", False))
        return exc.code
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        emit({"error": f"Input/state error: {exc}", "exit_code": 1}, getattr(a, "json", False))
        return 1
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
