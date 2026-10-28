"""Fast argparse CLI. Probes and recovery imports are lazy."""

import argparse
import json
from pathlib import Path
import sys
from secripts import __version__
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
    p = argparse.ArgumentParser(
        prog="js",
        description="JADIS // SECRIPTS — Personal Developer Operations Arsenal & Android Recovery Laboratory",
    )
    p.add_argument("--version", action="version", version=f"js {__version__}")
    sub = p.add_subparsers(dest="command")

    def add(name, help_text):
        item = sub.add_parser(name, help=help_text)
        item.add_argument("--json", action="store_true", help="Machine-readable output")
        return item

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
    completion = sub.add_parser(
        "completion", help="Generate Bash completion or list safe candidates"
    )
    completion.add_argument("shell", choices=["bash", "candidates"])
    completion.add_argument("words", nargs=argparse.REMAINDER)
    device = add("device", "Explicit read-only device inspection; identifiers omitted")
    device.add_argument("action", choices=["inspect", "transports", "fastboot"])
    device.add_argument("--device", help="Select one transport; not retained in evidence")
    for name in ("show", "explain"):
        add(name, "Inspect an operation contract and provenance").add_argument("operation")
    add("doctor", "Inspect host tools without changing configuration")
    r = add("run", "Execute a registered operation with a local receipt")
    r.add_argument("operation")
    r.add_argument("--dry-run", action="store_true")
    for name in ("tree", "artifact", "device"):
        r.add_argument("--" + name)
    add("recipes", "List guided workflows")
    recipe = add("recipe", "Inspect or execute a recipe")
    recipe.add_argument("action", choices=["show", "run"])
    recipe.add_argument("name")
    recipe.add_argument("--dry-run", action="store_true")
    recipe.add_argument("--network", action="store_true")
    for name in ("tree", "artifact", "device"):
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
        item = rs.add_parser(name, help=help_text)
        item.add_argument("--json", action="store_true")
        return item

    rec("doctor", "Check tools, workspace and unresolved hardware requirements")
    inspect = rec("inspect", "Inspect image headers or one authorized ADB device")
    inspect.add_argument("image", nargs="?", type=Path)
    inspect.add_argument("--device", action="store_true")
    tree = rec("tree", "Static device-tree evidence; never executes makefiles")
    tree.add_argument("action", choices=["audit", "inspect"])
    tree.add_argument("path", type=Path)
    init = rec("init", "Configure one isolated workspace; no source download")
    init.add_argument("device")
    for option in ("root", "tree"):
        init.add_argument(f"--{option}", required=True, type=Path)
    for option in ("manifest", "revision", "lunch"):
        init.add_argument(f"--{option}", required=True)
    init.add_argument(
        "--target", required=True, choices=["recoveryimage", "bootimage", "vendorbootimage"]
    )
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
    if cmd in (None, "doctor"):
        return w.recovery_doctor()
    if cmd == "tree":
        return audit_tree(a.path)
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
        return w.initialize(a.root, a.device, a.tree, a.manifest, a.revision, a.lunch, a.target)
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
            "guidance": "Inspect js recovery configure and local build receipts. Remove only individually reviewed build directories; js does not delete sources or artifacts automatically.",
        }


def dispatch(a):
    from secripts.registry import registry

    cmd = a.command
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
            a.operation, a.dry_run, {k: getattr(a, k) for k in ("tree", "artifact", "device")}
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
                {k: getattr(a, k) for k in ("tree", "artifact", "device")},
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
    a = p.parse_args(argv)
    if a.command is None:
        p.print_help()
        return 0
    try:
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
        if a.command == "recovery" and a.recovery_command in (
            "sync",
            "build",
            "boot",
            "inspect",
            "verify",
        ):
            from secripts.receipts import save

            try:
                evidence["receipt_id"] = save(
                    f"recovery.{a.recovery_command}",
                    "MUTATING" if a.recovery_command in ("sync", "build", "boot") else "READ_ONLY",
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
    except (OSError, ValueError, KeyError) as exc:
        emit({"error": f"Input/state error: {exc}", "exit_code": 1}, getattr(a, "json", False))
        return 1
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
