"""Conservative pattern-based detection; never return matched credentials."""

import re
from pathlib import Path

PATTERNS = [
    re.compile(r"\b(?:sk-(?:proj-)?|gh[pousr]_|github_pat_|hf_)[A-Za-z0-9_-]{12,}"),
    re.compile(
        r"(?im)(?:api[_ -]?key|(?:access[_ -]?|auth[_ -]?)?token|password|secret)[\"']?\s*[=:]\s*[\"']?[^\s\"'<>]{8,}"
    ),
    re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?(?:-----END [^-]+-----|$)"
    ),
    re.compile(r"(?i)\b(?:bearer\s+)[A-Za-z0-9._~+/-]{12,}=*"),
    re.compile(r"(?i)(?:https?|ssh)://[^\s/@]+:[^\s/@]+@[^\s]+"),
]
SENSITIVE = re.compile(r"(?i)(?:token|secret|password|api.?key|authorization|credential)")


def contains_secret(text: str) -> bool:
    return any(p.search(text) for p in PATTERNS)


def redact(value):
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            key = str(key)
            # Classification counts are public metadata, not credential-bearing fields.
            if (
                key == "counts"
                and isinstance(child, dict)
                and set(child) <= {"PROMOTE", "EXTRACT", "ARCHIVE", "REJECT", "SECRET"}
                and all(type(n) is int and 0 <= n <= 10000 for n in child.values())
            ):
                result[key] = child.copy()
            elif SENSITIVE.search(key) and not (
                key == "contained_secrets" and isinstance(child, bool)
            ):
                result[key] = "[REDACTED]"
            else:
                result[key] = redact(child)
        return result
    if isinstance(value, (list, tuple)):
        result = []
        hide_next = False
        for item in value:
            result.append("[REDACTED]" if hide_next else redact(item))
            hide_next = (
                isinstance(item, str) and item.startswith("-") and bool(SENSITIVE.search(item))
            )
        return result
    if isinstance(value, str):
        for pattern in PATTERNS:
            value = pattern.sub("[REDACTED]", value)
    return value


def scan_paths(paths: list[Path]) -> list[str]:
    """Return filenames only. No matched contents or line excerpts."""
    return [
        str(p)
        for p in paths
        if p.is_file() and contains_secret(p.read_bytes().decode("utf-8", errors="replace"))
    ]


def mask_identifiers(value, identifiers=()):
    """Remove explicitly collected device identifiers from every string, including argv/output."""
    if isinstance(value, dict):
        return {k: mask_identifiers(v, identifiers) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [mask_identifiers(v, identifiers) for v in value]
    if isinstance(value, str):
        for identifier in sorted(set(identifiers), key=len, reverse=True):
            if identifier:
                value = value.replace(identifier, "[REDACTED_IDENTIFIER]")
    return value


def sanitize_evidence(value):
    """Also mask explicitly named identifiers in legacy receipts before sharing/comparing."""
    identifiers = []

    def collect(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if str(key).lower() in {
                    "serial",
                    "serial_number",
                    "device_serial",
                    "imei",
                    "imsi",
                    "android_id",
                } and isinstance(child, str):
                    identifiers.append(child)
                collect(child)
        elif isinstance(item, (tuple, list)):
            for child in item:
                collect(child)

    collect(value)
    return redact(mask_identifiers(value, identifiers))
