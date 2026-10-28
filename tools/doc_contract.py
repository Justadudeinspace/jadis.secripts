"""Parse documented shell examples without executing commands or expanding a shell."""

from contextlib import redirect_stderr, redirect_stdout
import io
import re
import shlex
from secripts.cli import parser
from secripts.commands import inventory


def audit_examples(root):
    errors = []
    checked = 0
    cli = parser()
    paths = [root / "README.md", *sorted((root / "docs").rglob("*.md"))]
    for path in paths:
        text = path.read_text()
        for language, block in re.findall(r"```([^\n]*)\n(.*?)```", text, re.S):
            if language.strip() not in {"sh", "bash", "shell"}:
                continue
            block = block.replace("\\\n", " ")
            for line in block.splitlines():
                line = line.strip().removeprefix("$ ")
                if not line.startswith("js "):
                    continue
                try:
                    words = shlex.split(line, comments=True)
                    # Redirections are shell syntax, never evaluated; operands beyond them aren't CLI arguments.
                    boundary = next(
                        (i for i, w in enumerate(words) if w in {">", ">>", "|", "&&"}), len(words)
                    )
                    words = words[:boundary]
                    with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                        try:
                            cli.parse_args(words[1:])
                        except SystemExit as exc:
                            if exc.code:
                                raise ValueError("Arguments do not parse") from None
                    checked += 1
                except (ValueError, TypeError):
                    errors.append(f"{path.relative_to(root)}: invalid example: {line}")
    reference = (root / "docs/COMMAND-REFERENCE.md").read_text()
    for row in inventory(cli):
        if not row["scope"] and f"## js {row['canonical']}" not in reference:
            errors.append("Undocumented root command: " + row["canonical"])
    return {"checked": checked, "errors": errors}
