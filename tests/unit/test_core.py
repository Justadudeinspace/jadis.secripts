from dataclasses import replace
import sys
from pathlib import Path
import pytest
from secripts.registry import Operation, Registry, registry
from secripts.runner import run_command
from secripts.receipts import save, load, history
from secripts.safety import Risk, SecError
from secripts.operations import execute
from secripts.doctor import doctor, sdk
from secripts.provenance import packaged, validate


def test_registry_contract():
    ops = registry().search()
    assert len(ops) == 20
    assert all(
        op.summary and op.effect and op.platforms and isinstance(op.risk, Risk) for op in ops
    )
    with pytest.raises(ValueError, match="Duplicate"):
        Registry([ops[0], ops[0]])
    for kwargs in ({"id": "invalid"}, {"summary": ""}, {"risk": "BOGUS"}):
        with pytest.raises(ValueError):
            replace(ops[0], **kwargs)
    with pytest.raises(ValueError):
        Operation("test.invalid", "Bad", "Bad", "test")


def test_registry_search_and_invalid():
    assert registry().search("sdk license")[0].id == "android.sdk.validate"
    with pytest.raises(SecError) as exc:
        registry().get("absent")
    assert exc.value.code == 2


def test_runner_success_failure_missing_timeout():
    ok = run_command([sys.executable, "-c", "print('evidence')"])
    assert ok["exit_code"] == 0 and ok["stdout"].strip() == "evidence"
    fail = run_command([sys.executable, "-c", "import sys; sys.exit(7)"])
    assert fail["exit_code"] == 7 and fail["result"] == "FAIL"
    assert run_command(["secripts-certainly-missing-tool"])["result"] == "MISSING"
    assert (
        run_command([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.01)["result"]
        == "TIMEOUT"
    )


def test_runner_literal_arguments(tmp_path):
    marker = tmp_path / "owned"
    text = f"$(touch {marker}); echo unsafe"
    value = run_command([sys.executable, "-c", "import sys; print(sys.argv[1])", text])
    assert text in value["stdout"] and not marker.exists()
    assert run_command(["missing"], dry_run=True)["result"] == "DRY_RUN"
    with pytest.raises(SecError):
        run_command(["echo", "bad\0arg"])


def test_receipts_corruption_failure_artifacts(tmp_path):
    r = save(
        "test.failure",
        Risk.READ_ONLY,
        [{"result": "FAIL", "exit_code": 9}],
        artifacts=[{"path": "artifact.img", "sha256": "abc"}],
    )
    assert load(r["receipt_id"])["result"] == "FAIL"
    assert history()[0]["artifacts"][0]["path"] == "artifact.img"
    path = tmp_path / "state/receipts" / f"{r['receipt_id']}.json"
    path.write_text("broken")
    with pytest.raises(SecError, match="corrupted"):
        load(r["receipt_id"])
    assert history()[0]["result"] == "CORRUPTED"
    with pytest.raises(SecError):
        load("../../private")


def test_failed_operation_receipt(monkeypatch):
    monkeypatch.setattr("secripts.operations.shutil.which", lambda _: None)
    value = execute("adb.devices")
    assert value["exit_code"] == 3
    assert load(value["receipt_id"])["result"] == "FAIL"
    assert execute("fastboot.devices")["exit_code"] == 3
    assert execute("git.status", dry_run=True)["result"] == "DRY_RUN"


def test_doctor_no_fake_green(monkeypatch):
    monkeypatch.setattr("secripts.doctor.shutil.which", lambda _: None)
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    value = doctor()
    assert all(c["status"] in {"WARN", "UNTESTED"} for c in value["checks"])
    assert value["hardware_qualification"] == "UNTESTED"
    assert sdk()["status"] == "WARN"
    monkeypatch.setattr("secripts.doctor.shutil.which", lambda _: "/test/tool")
    assert doctor()["checks"][0]["status"] == "PASS"


def test_provenance_packaged():
    value = packaged()
    assert value["file_count"] == 153
    for row in value["artifacts"]:
        if row["contained_secrets"]:
            assert row["classification"] == "SECRET"
            assert row["source"].startswith("excluded-")
    with pytest.raises(SecError):
        validate({"schema": 1, "artifacts": [{"id": "bad"}]})


def test_catalog_consistency():
    expected = "# Operation catalog\n\nGenerated from `sec list --json`; update with `python tools/catalog.py`.\n\n"
    expected += "| Operation | Summary | Risk |\n|---|---|---|\n"
    for op in registry().search():
        expected += f"| `{op.id}` | {op.summary} | {op.risk} |\n"
    assert Path("docs/catalog.md").read_text() == expected


def test_host_android_runtime_and_unknown_environment(monkeypatch):
    from secripts.context import host

    monkeypatch.delenv("PREFIX", raising=False)
    monkeypatch.setattr("sys.base_prefix", "/data/data/com.termux/files/usr")
    monkeypatch.setattr("platform.system", lambda: "Android")
    assert host()["platform"] == "termux"
    monkeypatch.setattr("sys.base_prefix", "/usr")
    monkeypatch.setattr("sys.executable", "/usr/bin/python3")
    monkeypatch.setattr("platform.system", lambda: "UnqualifiedOS")
    assert host()["platform"] == "unsupported"
