"""One typed editor path for interactive and long-form recovery CLI routes."""

from secripts.recovery import flags
from secripts.safety import SecError


def dispatch(a):
    args = a.inputs
    if not args:
        return {
            "syntax": "js ry flags [ls|sh|set|unset|reset|diff|validate|export|import] MODEL [FLAG] [VALUE]",
            "profiles": "js ry flags profile save|apply|diff MODEL NAME; profile ls",
            "policy": "USER_OVERRIDE is never evidence; signing/rollback edits unavailable",
        }
    action = args[0]
    if action == "profile":
        if len(args) == 2 and args[1] in {"ls", "list"}:
            return flags.profile("list")
        if len(args) != 4 or args[1] not in {"save", "apply", "diff"}:
            raise SecError("Use flags profile save|apply|diff MODEL NAME", 2)
        return flags.profile(args[1], args[2], args[3], a.acknowledge_conflict)
    from secripts.commands import collision_audit

    actions = collision_audit(
        ["list", "show", "set", "unset", "reset", "diff", "validate", "export", "import"]
    )
    action = actions.get(action, action)
    if len(args) == 1:
        return flags.view(args[0])
    name = args[1]
    if action == "list" and len(args) == 2:
        return flags.view(name)
    if action == "show" and len(args) == 3:
        view = flags.view(name)
        if args[2] not in view["flags"]:
            raise SecError("Unknown build flag", 2)
        return view["flags"][args[2]]
    if action == "set" and len(args) == 4:
        return flags.change(
            name, args[2], args[3], reason=a.reason, acknowledge=a.acknowledge_conflict
        )
    if action in {"unset", "reset"} and len(args) == 3:
        return flags.change(
            name, args[2], action=action, reason=a.reason, acknowledge=a.acknowledge_conflict
        )
    if action == "validate" and len(args) == 2:
        return flags.validate(name)
    if action == "diff" and len(args) == 2:
        return {
            "schema": 1,
            "model": name,
            "overrides": {
                k: r for k, r in flags.view(name)["flags"].items() if r["user_override"] is not None
            },
        }
    if action == "export" and len(args) == 2:
        return flags.export(name, a.output, a.format)
    if action == "import" and len(args) == 3:
        return flags.import_profile(name, args[2], a.acknowledge_conflict)
    raise SecError("Invalid flag action/arguments; use js ry flags", 2)
