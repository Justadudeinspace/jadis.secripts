"""Consent-bound advisory orchestration; metadata receipts deliberately omit prompts and responses."""

from secripts.ai import context, providers
from secripts.receipts import save
from secripts.safety import SecError


def ask(question, *, provider, model=None, path=None, send=False, expected=None):
    providers.provider(provider)
    preview = context.preview(path, question)
    if not send:
        return {
            **preview,
            "provider": provider,
            "model": model,
            "next": "Review the payload; repeat with --send --approve SHA256 to authorize exactly this context",
        }
    if expected != preview["sha256"]:
        raise SecError(
            "AI transmission refused: --approve must match the current preview SHA256", 4
        )
    try:
        advice = providers.request(provider, model, preview["payload"])
    except SecError:
        save(
            "ai.advice",
            "READ_ONLY",
            [],
            result="FAIL",
            provider=provider,
            context_sha256=preview["sha256"],
            external_transmission="UNKNOWN_OR_BLOCKED",
            body_retained=False,
        )
        raise
    receipt = save(
        "ai.advice",
        "READ_ONLY",
        [],
        result="PASS",
        provider=provider,
        context_sha256=preview["sha256"],
        external_transmission=True,
        body_retained=False,
        evidence_state="AI_ADVICE_NOT_EVIDENCE",
    )
    return {
        "schema": 1,
        "status": "AI_ADVICE_NOT_EVIDENCE",
        "provider": provider,
        "advice": advice,
        "receipt_id": receipt["receipt_id"],
        "evidence_upgrade": False,
        "tool_execution": "UNAVAILABLE",
    }
