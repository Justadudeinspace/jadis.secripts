"""Bash completion generated from parser, registry and recipes, without invoking probes."""


def candidates(words):
    from secripts.registry import registry
    from secripts.recipes import RECIPES
    from secripts.cli import parser
    from secripts.commands import name, resolve
    import argparse

    current = parser()
    path = []
    action_identity = None
    positionals = 0
    previous = words[-1] if words else ""
    for token in words:
        child_action = next(
            (a for a in current._actions if isinstance(a, argparse._SubParsersAction)), None
        )
        if child_action and token in child_action.choices:
            current = child_action.choices[token]
            path.append(current.command_name.identity)
            positionals = 0
            continue
        if hasattr(current, "positional_names") and any(
            token in name(identity).tokens for identity in current.positional_names
        ):
            action_identity = resolve(token, current.positional_names)
            continue
        if not token.startswith("-"):
            positionals += 1
    if path == ["recovery", "flags"] and not positionals:
        return [
            "ls",
            "sh",
            "set",
            "unset",
            "reset",
            "diff",
            "validate",
            "export",
            "import",
            "profile",
            "list",
            "show",
        ]
    if path == ["recovery", "flags"] and positionals >= 2:
        from secripts.recovery.flags import CATALOG

        return sorted(CATALOG)
    if previous == "--risk":
        from secripts.safety import Risk

        return [risk.value for risk in Risk]
    if previous == "--category":
        return sorted({op.category for op in registry().search()})
    for option in current._actions:
        if previous in option.option_strings and option.choices:
            return list(option.choices)
    if len(path) == 1 and path[0] in {"run", "show", "explain"} and not positionals:
        return sorted(registry().operations)
    if path == ["recipe"] and action_identity in {"show", "run"} and not positionals:
        return sorted(RECIPES)
    child_action = next(
        (a for a in current._actions if isinstance(a, argparse._SubParsersAction)), None
    )
    if child_action:
        unique = {id(child): child for child in child_action.choices.values()}
        contracts = [child.command_name for child in unique.values()]
        return [contract.canonical for contract in contracts] + [
            alias for contract in contracts for alias in contract.aliases
        ]
    if hasattr(current, "positional_names") and action_identity is None:
        contracts = [name(identity) for identity in current.positional_names]
        return [contract.canonical for contract in contracts] + [
            alias for contract in contracts for alias in contract.aliases
        ]
    if not positionals:
        for action in current._actions:
            if (
                action.choices
                and not action.option_strings
                and not isinstance(action, argparse._SubParsersAction)
            ):
                return list(action.choices)
    return list(
        dict.fromkeys(option for action in current._actions for option in action.option_strings)
    )


def bash():
    # Dynamic completion asks only the candidate endpoint, never doctor or device discovery.
    return """# JADIS // SECRIPTS completion; source this file in Bash.
_js_complete() {
    local current="${COMP_WORDS[COMP_CWORD]}"
    local -a items=()
    mapfile -t items < <(js comp candidates -- "${COMP_WORDS[@]:1:COMP_CWORD-1}")
    COMPREPLY=()
    local item
    for item in "${items[@]}"; do
        [[ "$item" == "$current"* ]] && COMPREPLY+=("$item")
    done
    if [[ "${COMP_WORDS[COMP_CWORD-1]}" == --tree || "${COMP_WORDS[COMP_CWORD-1]}" == --artifact || "${COMP_WORDS[COMP_CWORD-1]}" == --output || "${COMP_WORDS[COMP_CWORD-1]}" == --workspace || "${COMP_WORDS[COMP_CWORD-1]}" == --tools ]]; then
        mapfile -t COMPREPLY < <(compgen -f -- "$current")
    fi
}
complete -o filenames -F _js_complete js
"""
