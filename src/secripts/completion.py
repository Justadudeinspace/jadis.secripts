"""Bash completion generated from parser, registry and recipes, without invoking probes."""


def candidates(words):
    from secripts.registry import registry
    from secripts.recipes import RECIPES
    from secripts.cli import parser
    import argparse

    root = parser()
    action = next(a for a in root._actions if isinstance(a, argparse._SubParsersAction))
    commands = list(action.choices)
    previous = words[-1] if words else ""
    if previous in ("run", "show", "explain") and (len(words) < 2 or words[-2] != "recipe"):
        return sorted(registry().operations)
    if len(words) >= 2 and words[-2] == "recipe" and previous in ("show", "run"):
        return sorted(RECIPES)
    if previous == "recipe":
        return ["show", "run"]
    if previous == "--risk":
        return ["READ_ONLY", "MUTATING", "PRIVILEGED", "DESTRUCTIVE"]
    if previous == "--category":
        return sorted({op.category for op in registry().search()})
    if previous == "recovery":
        return [
            "doctor",
            "device",
            "plan",
            "inspect",
            "tree",
            "init",
            "configure",
            "sync",
            "build",
            "verify",
            "boot",
            "test",
            "report",
            "clean",
        ]
    if previous == "tree":
        return ["audit", "inspect", "diagnose", "derive"]
    if previous == "device":
        return (
            ["inspect", "transports", "fastboot"]
            if "recovery" not in words
            else ["create", "list", "add-image", "add-tree", "add-metadata", "inspect", "report"]
        )
    return (
        commands
        if len(words) < 2
        else ["--json", "--dry-run", "--tree", "--artifact", "--device", "--network"]
    )


def bash():
    # Dynamic completion asks only the candidate endpoint, never doctor or device discovery.
    return """# JADIS // SECRIPTS completion; source this file in Bash.
_js_complete() {
    local current="${COMP_WORDS[COMP_CWORD]}"
    local -a items=()
    mapfile -t items < <(js completion candidates -- "${COMP_WORDS[@]:1:COMP_CWORD-1}")
    COMPREPLY=()
    local item
    for item in "${items[@]}"; do
        [[ "$item" == "$current"* ]] && COMPREPLY+=("$item")
    done
    if [[ "${COMP_WORDS[COMP_CWORD-1]}" == --tree || "${COMP_WORDS[COMP_CWORD-1]}" == --artifact ]]; then
        mapfile -t COMPREPLY < <(compgen -f -- "$current")
    fi
}
complete -o filenames -F _js_complete js
"""
