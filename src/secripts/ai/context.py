"""Explicit bounded, redacted JSON context. No filesystem or environment harvesting."""

import hashlib
import json
import os
import re
from pathlib import Path
from secripts.safety import SecError
from secripts.secrets import sanitize_evidence
from secripts.receipts import bounded_evidence

LIMIT = 12000


def clean(value):
    """Remove terminal controls and exact configured secrets in addition to pattern redaction."""
    value = sanitize_evidence(value)
    secrets = [
        v
        for k, v in os.environ.items()
        if re.search(r"API_KEY$|ACCESS_TOKEN$|PASSWORD$", k) and len(v) >= 4
    ]

    def visit(item):
        if isinstance(item, dict):
            return {visit(str(k)): visit(v) for k, v in item.items()}
        if isinstance(item, list):
            return [visit(v) for v in item]
        if isinstance(item, str):
            for secret in sorted(secrets, key=len, reverse=True):
                item = item.replace(secret, "[REDACTED]")
            item = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", item)
            item = "".join(c for c in item if c in "\n\t" or (ord(c) >= 32 and ord(c) != 127))
            # Local paths and networking/device identifiers are not useful inference credentials.
            item = re.sub(r"/(?:home|storage|data/data)/[^\s\"']+", "[LOCAL_PATH]", item)
            return item
        return item

    return visit(value)


def preview(path=None, question="", value=None):
    if path is not None:
        p = Path(path)
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 256 * 1024:
            raise SecError("Context must be an explicit regular JSON file below 256 KiB", 2)
        try:
            value = json.loads(p.read_text())
        except (ValueError, RecursionError) as exc:
            raise SecError("Malformed or excessively nested JSON context", 2) from exc
    try:
        value, truncated = bounded_evidence(clean(value if value is not None else {}), LIMIT // 2)
        text = json.dumps(
            {"question": clean(question)[:2000], "evidence": value},
            sort_keys=True,
            ensure_ascii=True,
        )
    except (RecursionError, TypeError) as exc:
        raise SecError("Context shape unsupported", 2) from exc
    if len(text.encode()) > LIMIT:
        raise SecError("Redacted context still exceeds 12 KiB; select a smaller report", 2)
    return {
        "schema": 1,
        "kind": "AI_CONTEXT_PREVIEW",
        "payload": json.loads(text),
        "bytes": len(text.encode()),
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "truncated": truncated,
        "external_transmission": False,
        "notice": "Review all fields before --send. Redaction cannot establish that a report contains no private information.",
    }
