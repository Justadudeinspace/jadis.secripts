"""Plain, readable human output; no ANSI sequences from external evidence."""

import re


def safe_text(value) -> str:
    # Strip terminal control bytes including ESC; JSON output already escapes them.
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "?", str(value))


def render(value, indent=0) -> str:
    pad = " " * indent
    if isinstance(value, dict):
        if indent == 0 and all(key in value for key in ("checks", "sdk", "summary", "host")):
            return render_doctor(value)
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
            isinstance(item, dict) and all(k in item for k in ("receipt_id", "operation", "result"))
            for item in value
        ):
            return "\n".join(
                f"{pad}{safe_text(item.get('timestamp', 'UNKNOWN')):33} {safe_text(item['operation']):26} {safe_text(item['result']):10} {item['receipt_id']}"
                for item in value
            )
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


def render_doctor(value):
    lines = [
        f"JADIS // DOCTOR :: {value['status']}",
        f"Host: {value['host']['os']} / {value['host']['architecture']}",
    ]
    for check in value["checks"]:
        lines.append(f"{safe_text(check['name']):20} {check['status']}")
        if check["status"] not in ("PASS", "UNTESTED"):
            advice = (
                check.get("remediation")
                or check.get("reason")
                or "Inspect the detailed JSON evidence."
            )
            lines.append(f"    {safe_text(advice)}")
    lines.extend(
        [
            f"Summary: {value['summary']}",
            "Hardware qualification: UNTESTED",
            "Invocation success does not imply environment readiness. Use --json for details.",
        ]
    )
    return "\n".join(lines)
