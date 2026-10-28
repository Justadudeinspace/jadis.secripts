"""Registry dispatch with preconditions, dry-run and failed-operation receipts."""

import shutil
from secripts.context import host
from secripts.doctor import doctor, path_analysis
from secripts.receipts import save
from secripts.registry import registry
from secripts.runner import run_command
from secripts.safety import authorize, SecError


def execute(name: str, dry_run: bool = False, parameters: dict | None = None) -> dict:
    op = registry().get(name)
    from secripts.evidence import Collector
    from secripts.inspectors import HANDLERS
    from secripts.devices import adb_inspect, fastboot_inspect, transport_summary

    parameters = {k: v for k, v in (parameters or {}).items() if v is not None}
    allowed = {p.name for p in op.parameters}
    if set(parameters) - allowed:
        raise SecError("Parameters not supported by this operation", 2)
    for parameter in op.parameters:
        if parameter.required and not parameters.get(parameter.name):
            raise SecError(f"Required parameter: --{parameter.name}", 2)
    collector = Collector()
    commands, warnings, preconditions = collector.commands, [], []
    result, code = "FAIL", 1
    try:
        if host()["platform"] not in op.platforms:
            raise SecError("Unsupported host platform", 5)
        authorize(op.risk, op.effect, dry_run=dry_run)
        for tool in op.requires:
            present = bool(shutil.which(tool))
            preconditions.append({"tool": tool, "status": "PASS" if present else "MISSING"})
            if not present and not dry_run:
                raise SecError(f"Missing prerequisite: {tool}", 3)
        if op.handler == "command":
            command = run_command(list(op.argv), dry_run=dry_run)
            commands.append(command)
            result = command["result"]
            code = 0 if result in ("PASS", "DRY_RUN") else 3 if result == "MISSING" else 1
            data = command
        else:
            handlers = {
                "host": lambda c, **kw: host(),
                "doctor": lambda c, **kw: doctor(),
                "path": lambda c, **kw: path_analysis(),
                **HANDLERS,
                "adb_inspect": adb_inspect,
                "fastboot_inspect": fastboot_inspect,
                "adb_transports": lambda c, **kw: transport_summary(c, "adb"),
                "fastboot_transports": lambda c, **kw: transport_summary(c, "fastboot"),
            }
            data = (
                {
                    "planned": op.summary,
                    "parameters": {
                        k: "[REDACTED_IDENTIFIER]" if k == "device" else str(v)
                        for k, v in parameters.items()
                    },
                }
                if dry_run
                else handlers[op.handler](collector, **parameters)
            )
            result, code = ("DRY_RUN" if dry_run else "PASS"), 0
    except (OSError, ValueError) as exc:
        warnings.append(str(exc))
        data, code = {"error": str(exc)}, 1
    except SecError as exc:
        warnings.append(str(exc))
        data, code = {"error": str(exc)}, exc.code
    receipt = (
        save(
            op.id,
            op.risk,
            commands,
            result=result,
            preconditions=preconditions,
            warnings=warnings,
            arguments={
                k: "[REDACTED_IDENTIFIER]" if k == "device" else str(v)
                for k, v in parameters.items()
            },
            data=data,
            effect=op.effect,
            hardware_qualification="UNTESTED",
        )
        if op.receipt
        else None
    )
    return {
        "operation": op.id,
        "result": result,
        "data": data,
        "receipt_id": receipt["receipt_id"] if receipt else None,
        "exit_code": code,
    }
