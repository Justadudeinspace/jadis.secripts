import sys
import pytest
from secripts.safety import authorize, Risk, SecError
from secripts.secrets import contains_secret, redact
from secripts.runner import run_command
from secripts.receipts import save, load

# Deliberately invalid synthetic credentials, assembled to exercise classes without storing tokens.
FAKE = "sk-" + "NOT_A_REAL_CREDENTIAL_" * 3


def test_secret_redaction_and_refusal():
    assert contains_secret(FAKE)
    assert FAKE not in str(redact({"stdout": FAKE, "token": "".join(["syn", "thetic"])}))
    with pytest.raises(SecError) as exc:
        run_command(["echo", FAKE])
    assert exc.value.code == 4
    value = run_command([sys.executable, "-c", "print('sk-' + 'NOT_A_REAL_CREDENTIAL_' * 3)"])
    assert FAKE not in value["stdout"]
    receipt = save(
        "test.redaction", Risk.READ_ONLY, [value], arguments=["--password", "synthetic-value"]
    )
    assert "synthetic-value" not in str(load(receipt["receipt_id"]))


def test_destructive_noninteractive_and_deliberate_confirmation(monkeypatch):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    with pytest.raises(SecError) as exc:
        authorize(Risk.DESTRUCTIVE, "erase", identity="device hash")
    assert exc.value.code == 4
    authorize(Risk.DESTRUCTIVE, "erase", dry_run=True)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "y")
    with pytest.raises(SecError):
        authorize(Risk.DESTRUCTIVE, "erase", identity="device hash")
    monkeypatch.setattr("builtins.input", lambda _: "CONFIRM device hash")
    authorize(Risk.DESTRUCTIVE, "erase", identity="device hash")


def test_privilege_does_not_elevate(monkeypatch):
    monkeypatch.setattr("os.geteuid", lambda: 1000)
    with pytest.raises(SecError) as exc:
        authorize(Risk.PRIVILEGED, "needs root")
    assert exc.value.code == 3


def test_metadata_secret_flag_is_preserved():
    assert redact({"contained_secrets": False})["contained_secrets"] is False
    assert redact({"counts": {"SECRET": 35}})["counts"]["SECRET"] == 35
    marker = "[REDACTED]"
    assert redact({"SECRET": int("12345678")})["SECRET"] == marker


def test_sensitive_containers_and_numeric_values():
    value = redact(
        {
            "password": int("12345678"),
            "credentials": {"opaque": "synthetic-value"},
            "contained_secrets": True,
        }
    )
    marker = "[REDACTED]"
    assert value["password"] == marker
    assert value["credentials"] == marker
    assert value["contained_secrets"] is True


def test_output_truncation_does_not_leak_partial_credential():
    from secripts.runner import MAX_CAPTURE

    script = f"print('safe'); print('x' * {MAX_CAPTURE} + 'sk-' + 'NOT_A_REAL_CREDENTIAL_' * 3)"
    value = run_command([sys.executable, "-c", script])
    assert value["stdout"].strip() == "safe\n[TRUNCATED]"


def test_json_generic_credential_detection():
    import json

    value = json.dumps({"api_key": "".join(["INVALID_", "SYNTHETIC_VALUE"])})
    assert contains_secret(value)
    assert "SYNTHETIC_VALUE" not in redact(value)
