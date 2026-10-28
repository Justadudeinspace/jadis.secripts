"""Plain, readable human output; no ANSI sequences from external evidence."""

import re


def safe_text(value) -> str:
    # Strip terminal control bytes including ESC; JSON output already escapes them.
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "?", str(value))


def render(value, indent=0) -> str:
    pad = " " * indent
    if isinstance(value, dict):
        lines = []
        for key, child in value.items():
            label = safe_text(key).replace("_", " ").upper()
            if isinstance(child, (dict, list, tuple)):
                lines.append(f"{pad}{label}")
                lines.append(render(child, indent + 2))
            else:
                lines.append(f"{pad}{label}: {safe_text(child)}")
        return "\n".join(lines)
    if isinstance(value, (list, tuple)):
        if not value:
            return f"{pad}(none)"
        if all(
            isinstance(item, dict) and all(k in item for k in ("id", "title", "summary", "risk"))
            for item in value
        ):
            return "\n".join(
                f"{pad}{safe_text(item['id']):28} {safe_text(item['title'])} [{safe_text(item['risk'])}]\n"
                f"{pad}    {safe_text(item['summary'])}"
                for item in value
            )
        return "\n".join(render(item, indent) for item in value)
    return f"{pad}{safe_text(value)}"
