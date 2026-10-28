"""Guidance and AI contracts: synthetic/mocked only, never paid inference."""

import json
from pathlib import Path
from dataclasses import replace
import pytest
from secripts.cli import main, parser
from secripts.ai import context, providers, service, tools
from secripts.safety import SecError
from secripts.recovery.guidance import acquire, INPUTS
from secripts.recovery.diagnostics import classify, diagnose
from secripts.recovery.planner import source_intelligence
from secripts.receipts import load


@pytest.mark.parametrize("have", list(INPUTS))
def test_acquisition_choices(have):
    r = acquire(have)
    assert r["hardware_qualification"] == "UNTESTED"
    assert r["status"] == "PARTIAL" and r["steps"]
    assert all(s["why"] and s["command"][0] == "js" for s in r["steps"])
    assert "No device mutation" in r["boundaries"]


def test_acquisition_no_inputs_no_probe(monkeypatch):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: pytest.fail("implicit process"))
    assert acquire()["observations"] == []
    with pytest.raises(SecError):
        acquire("flash")


@pytest.mark.parametrize("topic", ["image", "recovery", "device", "evidence", "ai"])
def test_topic_help(topic, capsys):
    assert main(["help", topic, "--json"]) == 0
    r = json.loads(capsys.readouterr().out)
    assert r["purpose"] and r["examples"]


def test_noargs_non_tty(capsys):
    assert main([]) == 0
    assert "usage: js" in capsys.readouterr().out


def test_guide_interactive(monkeypatch, capsys):
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    answers = iter(["bad", "3", "4", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main([]) == 0
    t = capsys.readouterr().out
    assert "What do you want to do?" in t and "Image Laboratory" in t
    assert "js ram" in t


def test_guide_eof(monkeypatch):
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    def eof(_):
        raise EOFError()

    monkeypatch.setattr("builtins.input", eof)
    assert main(["guide"]) == 0


@pytest.mark.parametrize("command", ["img", "image", "ram", "ramdisk", "avb", "dtbo"])
def test_namespace_entry(command, capsys):
    assert main([command]) == 0
    assert "usage: js " in capsys.readouterr().out


@pytest.mark.parametrize("short,long", [("ry", "recovery")])
def test_acquisition_alias_receipts(short, long, capsys):
    for command in (short, long):
        assert main([command, "acquire", "--have", "images", "--json"]) == 0
        r = json.loads(capsys.readouterr().out)
        assert r["operation"] == "recovery.acquire"
        assert load(r["receipt_id"])["operation"] == "recovery.acquire"
        assert r["data"]["status"] == "PARTIAL"


def test_source_declarations(tmp_path):
    (tmp_path / "default.xml").write_text(
        '<manifest><default revision="android-12.1"/><project path="prebuilts/jdk/jdk11"/></manifest>'
    )
    r = source_intelligence({"root": str(tmp_path), "manifest": "https://example.test/twrp_aosp"})
    assert r["toolchains"][0]["state"] == "DECLARED"
    assert r["toolchains"][0]["active_selection"] == "UNKNOWN"
    assert r["research_options"][0]["compatibility"] == "UNTESTED"


@pytest.mark.parametrize(
    "xml", ["<broken", "<!DOCTYPE x><manifest/>", '<!ENTITY x "a"><manifest/>']
)
def test_source_bad_xml(tmp_path, xml):
    (tmp_path / "default.xml").write_text(xml)
    assert source_intelligence({"root": str(tmp_path)})["state"] in {"UNKNOWN", "BLOCKED"}


def test_source_absent():
    r = source_intelligence({})
    assert r["state"] == "UNKNOWN" and r["toolchains"] == []


@pytest.mark.parametrize(
    "log,expected",
    [
        ("panic in GenerateBuildActions for module fake", "SOONG_PANIC"),
        ("depends on undefined module fake", "MISSING_MODULE"),
        ("Cannot locate config makefile for product fake", "INVALID_PRODUCT"),
        ("No rule to make target kernel/foo", "MISSING_INPUT"),
        ("kernel/foo error: bad fixture", "KERNEL_BUILD"),
        ("ERROR vintf incompatible", "VINTF"),
        ("neverallow violated", "SELINUX"),
        ("ld.lld: error: missing", "LINKER"),
        ("Unsupported class file major version 999", "JAVA"),
        ("python: command not found", "PYTHON"),
        ("No space left on device", "DISK"),
        ("cannot allocate memory", "MEMORY"),
        ("manifest parse error", "MANIFEST"),
        ("Exec format error", "HOST_TOOL"),
    ],
)
def test_failure_classes(log, expected):
    r = classify(log)
    assert expected in [f["classification"] for f in r["findings"]]
    assert all(f["state"] == "INFERRED" and f["root_cause"] == "UNRESOLVED" for f in r["findings"])
    assert not r["automatic_changes"]


def test_unrecognized_failure_not_success():
    r = classify("Killed\nfixture unrelated output")
    assert r["status"] == "UNKNOWN" and r["findings"] == []


def test_failure_bound_redaction(tmp_path, monkeypatch):
    key = "SYNTHETIC-NONAUTHENTICATING-VALUE"
    monkeypatch.setenv("OPENAI_API_KEY", key)
    p = tmp_path / "build.log"
    p.write_text("x" * 70000 + "\nNo space left on device " + key)
    r = diagnose(p)
    assert len(r["evidence"]["excerpt"]) <= 8192 and key not in str(r)
    assert len(r["log_sha256"]) == 64


def test_context_preview_redacts(tmp_path, monkeypatch):
    key = "SYNTHETIC-NONAUTHENTICATING-VALUE"
    monkeypatch.setenv("DEEPSEEK_API_KEY", key)
    p = tmp_path / "report.json"
    p.write_text(
        json.dumps(
            {
                "serial": "FAKE-DEVICE-ID",
                "log": key + " FAKE-DEVICE-ID /home/example/private/file",
                "password": key,
            }
        )
    )
    r = context.preview(p, "explain")
    assert key not in str(r) and "FAKE-DEVICE-ID" not in str(r) and "/home/example" not in str(r)
    assert r["external_transmission"] is False and r["bytes"] <= 12000
    assert r == context.preview(p, "explain")


@pytest.mark.parametrize("bad", ["{", "[" * 1200 + "0" + "]" * 1200])
def test_context_bad_json(tmp_path, bad):
    p = tmp_path / "bad"
    p.write_text(bad)
    with pytest.raises(SecError):
        context.preview(p)


def test_context_refuses_symlink_and_size(tmp_path):
    p = tmp_path / "report"
    p.write_text("{}")
    s = tmp_path / "link"
    s.symlink_to(p)
    with pytest.raises(SecError):
        context.preview(s)
    p.write_bytes(b" " * 262145)
    with pytest.raises(SecError):
        context.preview(p)


def test_context_truncation_explicit():
    r = context.preview(value={"log": "x" * 40000})
    assert r["truncated"] and r["bytes"] <= 12000


def test_provider_catalog_no_keys(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "SYNTHETIC-NONAUTHENTICATING-VALUE")
    r = providers.catalog()
    assert "SYNTHETIC-" not in str(r)
    assert r["subscription_login"]["status"] == "BLOCKED"


@pytest.mark.parametrize("name", ["openai", "claude", "deepseek"])
def test_missing_credentials(name, monkeypatch):
    p = providers.provider(name)
    monkeypatch.delenv(p.env, raising=False)
    with pytest.raises(SecError, match="Missing/invalid"):
        providers.transport(p, {})


def response(name, text="synthetic advice"):
    return {
        "openai": {
            "status": "completed",
            "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}],
        },
        "claude": {"stop_reason": "end_turn", "content": [{"type": "text", "text": text}]},
        "deepseek": {"choices": [{"finish_reason": "stop", "message": {"content": text}}]},
    }[name]


@pytest.mark.parametrize("name", ["openai", "claude", "deepseek"])
def test_provider_schemas(name, monkeypatch):
    seen = []

    def transport(p, body):
        seen.append((p, body))
        return response(name)

    monkeypatch.setattr(providers, "transport", transport)
    assert providers.request(name, "SYNTHETIC_MODEL", {"report": "fixture"}) == "synthetic advice"
    p, body = seen[0]
    assert p.id == name and body["model"] == "SYNTHETIC_MODEL"
    assert "tools" not in body
    if name == "openai":
        assert body["store"] is False


@pytest.mark.parametrize(
    "name,bad",
    [
        ("openai", {}),
        ("openai", []),
        ("openai", {"status": "incomplete"}),
        ("claude", {"stop_reason": "tool_use"}),
        ("claude", {"stop_reason": "end_turn", "content": []}),
        ("deepseek", {"choices": []}),
        ("deepseek", {"choices": [{"finish_reason": "length"}]}),
        (
            "deepseek",
            {
                "choices": [
                    {"finish_reason": "stop", "message": {"content": "x", "tool_calls": [{}]}}
                ]
            },
        ),
    ],
)
def test_malformed_provider(name, bad, monkeypatch):
    monkeypatch.setattr(providers, "transport", lambda *a: bad)
    with pytest.raises(SecError):
        providers.request(name, "SYNTHETIC_MODEL", {})


def test_fixed_origin_and_redirect(monkeypatch):
    p = providers.provider("openai")
    with pytest.raises(SecError):
        providers.transport(replace(p, endpoint="https://example.test"), {})
    with pytest.raises(SecError):
        providers.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.test")


@pytest.mark.parametrize("name", ["openai", "claude", "deepseek"])
def test_transport_credential_isolation(name, monkeypatch):
    captured = []
    for p in providers.PROVIDERS.values():
        monkeypatch.setenv(p.env, "SYNTHETIC-" + p.id.upper())

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, n):
            return b'{"fixture": true}'

    class Opener:
        def open(self, request, timeout):
            captured.append(request)
            return Response()

    monkeypatch.setattr("urllib.request.build_opener", lambda *a: Opener())
    p = providers.provider(name)
    assert providers.transport(p, {})["fixture"]
    request = captured[0]
    assert request.full_url == p.endpoint
    assert request.get_header("Authorization") == "Bearer SYNTHETIC-" + name.upper()
    assert all(
        "SYNTHETIC-" + other.upper() not in str(request.headers)
        for other in providers.PROVIDERS
        if other != name
    )


def test_preview_requires_hash_for_send(monkeypatch):
    monkeypatch.setattr(providers, "request", lambda *a: pytest.fail("network without consent"))
    preview = service.ask("why?", provider="openai")
    assert preview["external_transmission"] is False
    with pytest.raises(SecError):
        service.ask("why?", provider="openai", send=True, expected="wrong")


def test_advice_metadata_receipt_only(monkeypatch):
    monkeypatch.setattr(providers, "request", lambda *a: "PRIVATE RESPONSE FIXTURE")
    preview = service.ask("PRIVATE QUESTION FIXTURE", provider="openai")
    r = service.ask(
        "PRIVATE QUESTION FIXTURE",
        provider="openai",
        model="SYNTHETIC_MODEL",
        send=True,
        expected=preview["sha256"],
    )
    receipt = load(r["receipt_id"])
    assert "PRIVATE QUESTION" not in str(receipt) and "PRIVATE RESPONSE" not in str(receipt)
    assert r["evidence_upgrade"] is False and r["tool_execution"] == "UNAVAILABLE"


@pytest.mark.parametrize(
    "tool", ["shell", "run", "recovery.build", "image.unpack", "ai.remote", "credential.read"]
)
def test_ai_tool_refusal(tool):
    with pytest.raises(SecError) as exc:
        tools.invoke(tool)
    assert exc.value.code == 4


def test_ai_metadata_tools():
    assert tools.invoke("registry.search", "recovery")
    assert tools.invoke("registry.show", "image.roundtrip")["id"] == "image.roundtrip"


def test_no_implicit_models_network(monkeypatch, capsys):
    monkeypatch.setattr(providers, "transport", lambda *a, **k: pytest.fail("implicit network"))
    assert main(["ai", "models", "--provider", "openai", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "UNTESTED"


def test_model_none_rejected(monkeypatch):
    with pytest.raises(SecError):
        providers.request("openai", None, {})


def test_source_and_acquire_parse_contracts():
    for argv in [
        ["ry", "source"],
        ["recovery", "acquire", "--have", "firmware"],
        ["ry", "failure", "build.log"],
        ["ai", "ask", "why", "--provider", "claude"],
    ]:
        assert parser().parse_args(argv)


@pytest.mark.parametrize("error", [TimeoutError("SYNTHETIC"), OSError("SYNTHETIC")])
def test_transport_offline(error, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "SYNTHETIC-ONLY")

    class Opener:
        def open(self, *args, **kw):
            raise error

    monkeypatch.setattr("urllib.request.build_opener", lambda *a: Opener())
    with pytest.raises(SecError, match="transport unavailable"):
        providers.transport(providers.provider("openai"), {})


def test_transport_oversized(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "SYNTHETIC-ONLY")

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, n):
            return b"x" * n

    class Opener:
        def open(self, *a, **k):
            return Response()

    monkeypatch.setattr("urllib.request.build_opener", lambda *a: Opener())
    with pytest.raises(SecError, match="budget"):
        providers.transport(providers.provider("openai"), {})


def test_failed_advice_receipt(monkeypatch):
    from secripts.receipts import latest

    preview = service.ask("fixture", provider="openai")

    def fail(*a):
        raise SecError("offline fixture")

    monkeypatch.setattr(providers, "request", fail)
    with pytest.raises(SecError):
        service.ask(
            "fixture",
            provider="openai",
            model="SYNTHETIC_MODEL",
            send=True,
            expected=preview["sha256"],
        )
    assert latest()["result"] == "FAIL" and "fixture" not in str(latest())


def test_changed_context_requires_new_consent(tmp_path):
    p = tmp_path / "context.json"
    p.write_text("{}")
    preview = service.ask("q", provider="openai", path=p)
    p.write_text('{"status":"changed"}')
    with pytest.raises(SecError):
        service.ask("q", provider="openai", path=p, send=True, expected=preview["sha256"])


def test_firmware_plan_never_extracts(tmp_path, capsys):
    archive = tmp_path / "input.zip"
    archive.write_bytes(b"not an image")
    assert main(["ry", "acquire", "--have", "firmware", "--json"]) == 0
    r = json.loads(capsys.readouterr().out)
    assert r["data"]["observations"] == [] and not (tmp_path / "extracted").exists()


def test_doc_contracts():
    import importlib.util

    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("doc_contract", root / "tools/doc_contract.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.audit_examples(root)
    assert not result["errors"] and result["checked"] >= 100


def test_research_provenance_is_bounded_metadata():
    root = Path(__file__).resolve().parents[2]
    ledger = json.loads((root / "docs/research/phase5-sources.json").read_text())
    assert len(ledger["device_trees"]) == 6
    assert all(len(row["commit"]) == 40 for row in ledger["device_trees"])
    assert all(row.get("code_adapted") is False for row in ledger["sources"])
    assert (root / "docs/research/phase5-gap-matrix.md").is_file()


def test_source_api_symptom():
    result = classify("error: unknown type name SYNTHETIC")
    assert result["findings"][0]["classification"] == "SOURCE_API"


def test_cockpit_ai_and_compact(monkeypatch, capsys):
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(
        "secripts.ui.console.dashboard", lambda **k: {"SYSTEM": {"host": "synthetic"}}
    )
    answers = iter(["ai", "setup", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main(["1337"]) == 0
    text = capsys.readouterr().out
    assert "AI" in text and "BYOK" in text and "\x1b" not in text


def test_registry_context_does_not_persist_body(tmp_path):
    from secripts.operations import execute
    from secripts.receipts import history

    p = tmp_path / "report.json"
    p.write_text('{"detail":"PRIVATE CONTEXT FIXTURE"}')
    result = execute("ai.context", parameters={"artifact": str(p)})
    assert result["result"] == "PASS" and result["receipt_id"] is None
    assert all("PRIVATE CONTEXT FIXTURE" not in str(r) for r in history())


def test_claude_tool_block_refused(monkeypatch):
    monkeypatch.setattr(
        providers,
        "transport",
        lambda *a: {
            "stop_reason": "end_turn",
            "content": [{"type": "tool_use", "name": "shell"}, {"type": "text", "text": "fixture"}],
        },
    )
    with pytest.raises(SecError):
        providers.request("claude", "SYNTHETIC_MODEL", {})


def test_guide_json_is_one_document(capsys):
    assert main(["guide", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["title"] == "JADIS // SECRIPTS"
