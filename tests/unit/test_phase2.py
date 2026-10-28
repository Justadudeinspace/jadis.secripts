"""Phase-two contract, evidence and privacy regressions; no device/network access."""

from dataclasses import replace
import json
import sys
import pytest
from secripts.registry import registry, Parameter
from secripts.operations import execute
from secripts.evidence import Collector, overall
from secripts.receipts import save, load, history, latest, compare
from secripts.safety import SecError
from secripts.devices import adb_inspect, fastboot_inspect, transport_summary
from secripts import inspectors


def response(stdout="", stderr="", result="PASS", exit_code=0):
    return {
        "stdout": stdout,
        "stderr": stderr,
        "result": result,
        "exit_code": exit_code,
        "duration": 0,
        "arguments": [],
    }


def test_parameter_contract_and_all_dry_runs(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Dry run launched a process")

    monkeypatch.setattr("secripts.runner.subprocess.Popen", forbidden)
    for op in registry().search():
        parameters = {p.name: "/nonexistent-safe-fixture" for p in op.parameters if p.required}
        value = execute(op.id, True, parameters)
        assert value["result"] == "DRY_RUN", op.id
        assert value["exit_code"] == 0, op.id
    with pytest.raises(ValueError):
        Parameter("arbitrary", "No arbitrary argument routing")
    with pytest.raises(ValueError):
        replace(
            registry().get("git.status"),
            parameters=(Parameter("tree", "x"), Parameter("tree", "x")),
        )
    with pytest.raises(SecError):
        execute("recovery.tree", True)
    with pytest.raises(SecError):
        execute("git.status", True, {"device": "unrelated"})


def test_ranked_search_and_filters():
    reg = registry()
    assert reg.search("git.status")[0].id == "git.status"
    assert reg.search("git.")[0].id.startswith("git.")
    assert all(op.category == "recovery" for op in reg.search(category="recovery"))
    assert all(op.risk == "READ_ONLY" for op in reg.search("tree", risk="READ_ONLY"))
    assert reg.search("device tree")[0].id == "recovery.tree"
    assert not reg.search(risk="DESTRUCTIVE")
    assert [o.id for o in reg.search("git")] == [o.id for o in reg.search("git")]


def test_receipt_filters_latest_diff_and_artifact():
    a = save("git.status", "READ_ONLY", [], result="PASS", timestamp="2026-01-01T01:00:00+00:00")
    b = save(
        "recovery.image",
        "READ_ONLY",
        [],
        result="FAIL",
        timestamp="2026-02-01T01:00:00+00:00",
        artifacts=[{"path": "fixture.img", "sha256": "abc"}],
    )
    assert latest()["receipt_id"] == b["receipt_id"]
    assert latest(failed=True)["receipt_id"] == b["receipt_id"]
    assert history(operation="git.status")[0]["receipt_id"] == a["receipt_id"]
    assert len(history(since="2026-02-01", artifact="abc", failed=True, limit=20)) == 1
    assert not history(result="DRY_RUN")
    assert history(limit=0) == []
    assert compare(a["receipt_id"], b["receipt_id"])["changes"]
    for kwargs in ({"since": "bad-date"}, {"limit": -1}):
        with pytest.raises(SecError):
            history(**kwargs)


def test_legacy_receipt_identifier_sanitization():
    serial = "SYNTHETIC_DEVICE_ID"
    value = save("test.identifier", "READ_ONLY", [response(serial)], evidence={"serial": serial})
    assert serial not in json.dumps(load(value["receipt_id"]))


@pytest.mark.parametrize(
    "text,message",
    [
        ("List of devices attached\n", "NO DEVICE"),
        ("List of devices attached\nfirst device\nsecond device\n", "Exactly one"),
        ("List of devices attached\nfirst unauthorized\n", "unauthorized"),
        ("List of devices attached\nfirst offline\n", "offline"),
        ("malformed output", "malformed"),
    ],
)
def test_adb_selection_refusals(monkeypatch, text, message):
    monkeypatch.setattr("secripts.evidence.run_command", lambda *a, **k: response(text))
    with pytest.raises(SecError, match=message):
        adb_inspect(Collector())


def test_device_dossier_private_identifier_and_package_names(monkeypatch):
    serial = "SYNTHETIC_DEVICE_ID"

    def command(argv, **kwargs):
        if argv[1] == "devices":
            return response(f"List of devices attached\n{serial} device product:example\n")
        if argv[-3:] == ["pm", "list", "packages"]:
            return response("package:private.application\npackage:another.application\n")
        if argv[-1] == "/proc/cpuinfo":
            return response(f"processor: 0\nSerial: {serial}\nHardware: fixture\n")
        return response("fixture observation")

    monkeypatch.setattr("secripts.evidence.run_command", command)
    c = Collector()
    value = adb_inspect(c, device=serial)
    text = json.dumps({"dossier": value, "commands": c.commands})
    assert serial not in text and "private.application" not in text
    assert value["sections"]["packages"]["evidence"]["count"] == 2
    assert value["hardware_qualification"] == "UNTESTED"
    assert all(
        not any(x in cmd.get("arguments", []) for x in ("root", "reboot", "flash", "su"))
        for cmd in c.commands
    )


def test_fastboot_no_device_and_variable_evidence(monkeypatch):
    monkeypatch.setattr("secripts.evidence.run_command", lambda *a, **k: response(""))
    assert transport_summary(Collector(), "fastboot")["count"] == 0
    with pytest.raises(SecError, match="NO DEVICE"):
        fastboot_inspect(Collector())

    def command(argv, **kwargs):
        if argv[1] == "devices":
            return response("FAKE_SERIAL fastboot\n")
        name = argv[-1]
        return response(stderr=f"(bootloader) {name}: fixture\nFinished. Total time: 0.001s\n")

    monkeypatch.setattr("secripts.evidence.run_command", command)
    value = fastboot_inspect(Collector())
    assert value["variables"]["product"]["evidence"] == "fixture"
    assert value["temporary_boot_support"] == "UNRESOLVED"


def test_collector_deadline_and_unknown_status(monkeypatch):
    monkeypatch.setattr(
        "secripts.evidence.run_command",
        lambda *a, **k: pytest.fail("Expired collector ran command"),
    )
    value = Collector(deadline=0).command(["adb", "devices"])
    assert value["result"] == "BLOCKED"
    assert overall([{"status": "PASS"}, {"status": "UNKNOWN"}]) == "UNKNOWN"
    assert overall([]) == "UNKNOWN"
    collector = Collector(
        deadline=0, runner=lambda *a, **k: pytest.fail("Injected recovery runner bypassed deadline")
    )
    assert collector.command(["adb", "devices"])["result"] == "BLOCKED"


def test_sdk_components_conflict_and_license_state(tmp_path, monkeypatch):
    first = tmp_path / "sdk"
    second = tmp_path / "other"
    first.mkdir()
    second.mkdir()
    for name in (
        "build-tools/35.0.0",
        "platforms/android-35",
        "ndk/fixture",
        "cmake/fixture",
        "cmdline-tools/latest/bin",
        "licenses",
        "platform-tools",
    ):
        (first / name).mkdir(parents=True, exist_ok=True)
    (first / "cmdline-tools/latest/bin/sdkmanager").write_text("not executed")
    monkeypatch.setenv("ANDROID_HOME", str(first))
    monkeypatch.setenv("ANDROID_SDK_ROOT", str(second))
    value = inspectors.sdk()
    assert value["conflict"] and value["status"] == "WARN"
    assert value["components"]["build-tools"]["entries"] == ["35.0.0"]
    assert value["license_state"].startswith("UNKNOWN")
    assert value["compatibility"].startswith("UNTESTED")


def test_python_metadata_invalid_and_allowlist(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert inspectors.python_project()["status"] == "UNKNOWN"
    p = tmp_path / "pyproject.toml"
    p.write_text("not valid = [")
    assert inspectors.python_project()["status"] == "FAIL"
    p.write_text(
        '[project]\nname="fixture"\nversion="0"\n[build-system]\nbuild-backend="fixture.backend"\n[tool.private]\nopaque="not-for-output"\n'
    )
    value = inspectors.python_project()
    assert value["status"] == "PASS" and "not-for-output" not in str(value)
    assert inspectors.python_environment()["executable"] == sys.executable


def test_dossier_no_implicit_network_or_devices(monkeypatch):
    import secripts.dossier as d

    monkeypatch.setattr(
        "secripts.devices.transport_summary", lambda *a, **k: pytest.fail("Implicit device probe")
    )
    monkeypatch.setattr(
        "secripts.inspectors.git_health", lambda c: {"status": "UNKNOWN", "reason": "fixture"}
    )
    value = d.dossier()
    assert value["network_probes"] == "NOT_RUN"
    assert value["sections"]["devices"]["adb"]["status"] == "UNTESTED"
    assert value["sections"]["recovery"]["hardware"] == "UNTESTED"
    assert value["sections"]["secripts"]["operations"] == 63


def test_recipes_contract_network_refusal_and_parent_receipt():
    from secripts.recipes import RECIPES, get, run

    assert len(RECIPES) == 19
    for recipe in RECIPES:
        value = get(recipe)
        assert len(value["operations"]) >= 2
        assert value["summary"]
    with pytest.raises(SecError, match="network"):
        run("github-readiness")
    with pytest.raises(SecError, match="tree"):
        run("twrp-tree-review", True)
    value = run("git-review", True)
    assert load(value["receipt_id"])["step_receipts"]


def test_bash_completion_and_candidates(tmp_path):
    from secripts.completion import bash, candidates
    from secripts.runner import run_command

    assert "git.health" in candidates(["run"])
    assert "python-dev" in candidates(["recipe", "run"])
    assert "recovery" in candidates([])
    assert "READ_ONLY" in candidates(["--risk"])
    p = tmp_path / "js.bash"
    p.write_text(bash())
    assert run_command(["bash", "-n", str(p)])["result"] == "PASS"


def test_receipt_missing_latest():
    with pytest.raises(SecError, match="No matching"):
        latest(failed=True)
