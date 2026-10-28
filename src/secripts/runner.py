"""Argument-safe subprocess runner. Raw output never crosses this boundary."""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from secripts.secrets import SENSITIVE, contains_secret, redact, mask_identifiers
from secripts.safety import SecError

MAX_CAPTURE = 128 * 1024


def run_command(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout: float = 30,
    dry_run: bool = False,
    identifiers: tuple[str, ...] = (),
) -> dict:
    if not argv or any(not isinstance(a, str) or "\0" in a for a in argv):
        raise SecError("Invalid argument vector", 2)
    if any(contains_secret(a) or (a.startswith("--") and SENSITIVE.search(a)) for a in argv):
        raise SecError("Secret-like argument refused; use the tool's secure credential store.", 4)
    result = {
        "executable": argv[0],
        "arguments": redact(argv[1:]),
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "duration": 0,
        "result": "DRY_RUN",
    }
    if dry_run:
        return mask_identifiers(result, identifiers)
    start = time.monotonic()
    # File-backed capture avoids unbounded in-memory output. Temporary files are private/unlinked.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
            process = subprocess.Popen(
                argv, cwd=cwd, stdout=out, stderr=err, env=env, start_new_session=True
            )
            try:
                result["exit_code"] = process.wait(timeout=timeout)
                result["result"] = "PASS" if process.returncode == 0 else "FAIL"
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                import signal

                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                if isinstance(exc, KeyboardInterrupt):
                    raise
                result.update(result="TIMEOUT", exit_code=124)
        except FileNotFoundError:
            result.update(result="MISSING", exit_code=127)
        except OSError as exc:
            result.update(result="FAIL", exit_code=1, stderr=redact(str(exc)))
        for name, stream in (("stdout", out), ("stderr", err)):
            stream.seek(0)
            value = stream.read(MAX_CAPTURE + 1)
            if len(value) > MAX_CAPTURE:
                # Discard a partial final line so a cut-off credential prefix cannot evade scanning.
                value = (
                    value[:MAX_CAPTURE].rsplit(b"\n", 1)[0] if b"\n" in value[:MAX_CAPTURE] else b""
                )
                result[name] += "\n[TRUNCATED]"
            if value:
                result[name] = redact(value.decode("utf-8", errors="replace")) + result[name]
    result["duration"] = round(time.monotonic() - start, 4)
    return mask_identifiers(result, identifiers)
