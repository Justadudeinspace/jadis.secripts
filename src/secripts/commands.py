"""Authoritative CLI spelling contracts. Names normalize to stable internal identities before dispatch."""

from dataclasses import asdict, dataclass
import argparse
import difflib
import re

PREFERRED = {
    "recovery": "ry",
    "doctor": "doc",
    "dossier": "dos",
    "find": "fd",
    "explain": "exp",
    "recipe": "rcp",
    "recipes": "rcps",
    "device": "dce",
    "inspect": "insp",
    "history": "hist",
    "image": "img",
    "ramdisk": "ram",
    "receipt": "rcpt",
    "list": "ls",
    "show": "sh",
    "providers": "prov",
    "workspace": "ws",
    "compare": "cmp",
    "rebuild": "rb",
    "unpack": "upk",
    "roundtrip": "rt",
    "extract": "ext",
    "diagnose": "diag",
    "differential": "diff",
    "archaeology": "arch",
    "research": "res",
    "completion": "comp",
    "ingest": "ing",
    "configure": "cfg",
    "verify": "vfy",
}
EXTRA_ALIASES = {"receipt": ("receipts",)}


@dataclass(frozen=True)
class CommandName:
    identity: str
    canonical: str
    aliases: tuple[str, ...] = ()
    display_name: str = ""

    @property
    def tokens(self):
        return (self.canonical, *self.aliases)


def name(identity):
    short = PREFERRED.get(identity, identity)
    return CommandName(
        identity,
        short,
        ((identity,) if short != identity else ()) + EXTRA_ALIASES.get(identity, ()),
        identity.replace("-", " ").title(),
    )


def collision_audit(identities):
    owners = {}
    for identity in identities:
        contract = name(identity) if isinstance(identity, str) else identity
        for token in contract.tokens:
            if token in owners:
                raise ValueError(f"CLI name collision: {token}")
            owners[token] = contract.identity
    return owners


def resolve(token, identities):
    owners = collision_audit(identities)
    if token not in owners:
        raise ValueError("Unknown command spelling")
    return owners[token]


def named(subparsers, identity, *, dest, help_text=None):
    contract = name(identity)
    for spelling in contract.tokens:
        if spelling in subparsers.choices:
            raise ValueError(f"CLI name collision: {spelling}")
    aliases = ", ".join(contract.aliases)
    help_line = (help_text or contract.display_name) + (f" [{aliases}]" if aliases else "")
    parser = subparsers.add_parser(
        contract.canonical,
        aliases=list(contract.aliases),
        help=help_line,
        description=help_text or contract.display_name,
        epilog=f"Canonical: {contract.canonical}. Aliases: {aliases or 'none'}.",
    )
    parser.set_defaults(**{dest: identity})
    parser.command_name = contract
    return parser


def action_argument(parser, destination, identities):
    contracts = tuple(identities)
    collision_audit(contracts)
    parser.add_argument(
        destination,
        type=lambda spelling: resolve(spelling, contracts),
        choices=contracts,
        metavar="{" + ",".join(name(identity).canonical for identity in contracts) + "}",
    )
    parser.epilog = (
        (parser.epilog or "")
        + " Action aliases: "
        + "; ".join(
            f"{name(identity).canonical} [{', '.join(name(identity).aliases)}]"
            for identity in contracts
            if name(identity).aliases
        )
    )
    parser.positional_names = contracts


class Parser(argparse.ArgumentParser):
    def error(self, message):
        match = re.search(r"invalid choice: '([^']+)'", message)
        if match:
            choices = []
            for action in self._actions:
                if isinstance(action, argparse._SubParsersAction):
                    choices.extend(action.choices)
            close = difflib.get_close_matches(match.group(1), choices, n=1, cutoff=0.55)
            if close:
                for action in self._actions:
                    if (
                        isinstance(action, argparse._SubParsersAction)
                        and close[0] in action.choices
                    ):
                        contract = action.choices[close[0]].command_name
                        message += "\nDid you mean: " + ", ".join(contract.tokens) + "?"
                        break
        super().error(message)


def inventory(parser):
    """Full scoped map; aliases refer to the same parser object and implementation identity."""
    rows = []

    def walk(current, scope):
        for action in current._actions:
            if isinstance(action, argparse._SubParsersAction):
                unique = {id(child): child for child in action.choices.values()}
                for child in unique.values():
                    contract = child.command_name
                    rows.append({"scope": list(scope), **asdict(contract), "kind": "command"})
                    walk(child, (*scope, contract.identity))
        if not hasattr(current, "positional_names"):
            for action in current._actions:
                if (
                    action.choices
                    and not action.option_strings
                    and not isinstance(action, argparse._SubParsersAction)
                ):
                    for identity in action.choices:
                        rows.append(
                            {
                                "scope": list(scope),
                                **asdict(name(str(identity))),
                                "kind": "enumeration",
                            }
                        )
        if hasattr(current, "positional_names"):
            for identity in current.positional_names:
                rows.append({"scope": list(scope), **asdict(name(identity)), "kind": "action"})

    walk(parser, ())
    return rows


# Convenience paths normalize into existing command identities, not duplicate operations.
ROUTES = {
    ("image", "inspect"): ("inspect", {"path": "artifact"}),
    ("image", "providers"): ("providers", {}),
}


def normalize(namespace):
    route = ROUTES.get(
        (getattr(namespace, "command", None), getattr(namespace, "engineering_action", None))
    )
    if route:
        identity, attributes = route
        namespace.command = identity
        for destination, source in attributes.items():
            setattr(namespace, destination, getattr(namespace, source))
    return namespace
