"""Registry dispatch with preconditions, dry-run and failed-operation receipts."""

import shutil
from secripts.context import host
from secripts.doctor import doctor, sdk, path_analysis
from secripts.receipts import save
from secripts.registry import registry
from secripts.runner import run_command
from secripts.safety import authorize, SecError


def execute(name: str, dry_run: bool = False) -> dict:
    op = registry().get(name)
    commands, warnings, preconditions = [], [], []
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
            data = (
                {"planned": op.summary}
                if dry_run
                else {"host": host, "doctor": doctor, "sdk": sdk, "path": path_analysis}[
                    op.handler
                ]()
            )
            result, code = ("DRY_RUN" if dry_run else "PASS"), 0
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
            arguments=[],
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
