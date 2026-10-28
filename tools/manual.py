"""Generate complete parser argument reference; reject documentation drift with --check."""

import argparse
from pathlib import Path
import sys
from secripts.cli import parser
from secripts import __version__


def required(action):
    # Python 3.11 marks some zero-arity positionals required in metadata even
    # though parsing accepts zero values. Options still use their explicit guard.
    return (
        bool(action.required)
        if action.option_strings
        else action.nargs not in ("?", "*", argparse.REMAINDER, 0)
    )


def syntax(p, route):
    """Canonical syntax from contracts, independent of argparse terminal layout/version."""
    tokens = [*route]
    for action in p._actions:
        if isinstance(action, argparse._SubParsersAction):
            tokens.append("COMMAND" if action.required else "[COMMAND]")
        elif not action.option_strings:
            operand = action.dest.upper()
            if action.nargs in ("*", argparse.REMAINDER):
                operand = "[" + operand + " ...]"
            elif action.nargs == "?":
                operand = "[" + operand + "]"
            elif action.nargs == "+":
                operand += " [" + operand + " ...]"
            tokens.append(operand)
    if any(action.option_strings for action in p._actions):
        tokens.append("[options]")
    return " ".join(tokens)


def reference():
    lines = [
        f"# Complete command reference — {__version__}",
        "",
        "Generated from the authoritative parser. Do not edit by hand.",
        "",
        "All accepted aliases use the same parser, operation identity and guards. Defaults below are parser defaults; explicit user-state paths follow XDG/SECRIPTS_DATA_HOME. Commands are Linux/Termux scoped.",
        "",
        "JSON: `--json` emits uncolored machine data where listed. Invocation success is separate from evidence status. Registry execution writes sanitized receipts; help/listing do not. Image transformations require new outputs. Recovery mutations retain their existing guards. AI never sends without `--send --approve SHA256`; catalog requests require `--network`. Failures: 1 operation, 2 usage, 3 prerequisite, 4 safety refusal, 5 unsupported platform. Related contracts: [operations](catalog.md), [recipes](RECIPES.md), [evidence](RECEIPTS-EVIDENCE.md), [safety](safety-model.md).",
        "",
    ]

    def walk(p, route):
        lines.extend(
            ["## " + " ".join(route), "", p.description or "Canonical command interface.", ""]
        )
        c = getattr(p, "command_name", None)
        if c:
            lines.extend(["Aliases: " + (", ".join(c.aliases) or "none") + ".", ""])
        lines.extend(
            [
                "```text",
                syntax(p, route),
                "```",
                "",
                "| Argument / option | Purpose | Default | Required / choices |",
                "|---|---|---|---|",
            ]
        )
        children = []
        for a in p._actions:
            if isinstance(a, argparse._SubParsersAction):
                seen = set()
                for child in a.choices.values():
                    if id(child) not in seen:
                        children.append(child)
                        seen.add(id(child))
                continue
            name = ", ".join(a.option_strings) or a.dest
            detail = a.help or (
                "Positional " + a.dest
                if not a.option_strings
                else "Explicit " + a.dest + " selector"
            )
            default = repr(a.default)
            choices = "required" if required(a) else "optional"
            if a.choices:
                choices += "; " + ",".join(str(s) for s in a.choices)
            lines.append(
                "| "
                + " | ".join(
                    str(s).replace("|", "/").replace("\n", " ")
                    for s in (name, detail, default, choices)
                )
                + " |"
            )
        lines.append("")
        for child in children:
            walk(child, route + [child.command_name.canonical])

    walk(parser(), ["js"])
    return "\n".join(lines).rstrip() + "\n"


def recipes_reference():
    from secripts.recipes import RECIPES, get
    from secripts.registry import registry

    ops = registry().search()
    lines = [
        f"# Recipes — {__version__}",
        "",
        f"{len(RECIPES)} recipes compose {len(ops)} available operations across {len({op.category for op in ops})} categories.",
        "",
        "Inspect with `js rcp sh NAME`; preview `js rcp run NAME --dry-run`. Each step uses operation IDs, normal risk guards and linked receipts. Network steps require --network. Failure stops the recipe; a parent receipt keeps partial evidence. See [CLI](CLI-GUIDE.md).",
        "",
    ]
    for name in RECIPES:
        row = get(name)
        lines.extend(
            [
                "## " + name,
                "",
                row["summary"],
                "",
                "Operations: " + ", ".join("`" + op + "`" for op in row["operations"]) + ".",
                "",
                "Prerequisites and risk: inspect the constituent operation contracts with js sh; required selectors are the union shown by js rcp sh. Missing prerequisites stop execution; no installs occur.",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "docs/COMMAND-REFERENCE.md"
    text = reference()
    recipes = target.parent / "RECIPES.md"
    recipe_text = recipes_reference()
    if "--check" in sys.argv:
        if (
            not target.is_file()
            or target.read_text() != text
            or not recipes.is_file()
            or recipes.read_text() != recipe_text
        ):
            raise SystemExit("Command reference drift: run python tools/manual.py")
    else:
        target.write_text(text)
        recipes.write_text(recipe_text)
