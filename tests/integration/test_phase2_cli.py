import json
import pytest
from secripts.cli import main


@pytest.mark.parametrize(
    "args",
    [
        ["dossier", "--json"],
        ["1337", "--json"],
        ["find", "--category", "recovery", "--json"],
        ["find", "--risk", "DESTRUCTIVE", "--json"],
        ["show", "recovery.tree", "--json"],
        ["explain", "python.environment", "--json"],
        ["run", "python.project", "--dry-run", "--json"],
        ["recipe", "show", "twrp-tree-review", "--json"],
        ["recipe", "run", "twrp-tree-review", "--tree", "/fixture", "--dry-run", "--json"],
        ["history", "--operation", "git.status", "--failed", "--limit", "2", "--json"],
    ],
)
def test_phase2_cli_json(args, capsys):
    assert main(args) == 0
    value = json.loads(capsys.readouterr().out)
    if "--risk" in args:
        assert value == {"operations": [], "recipes": {}}


def test_latest_receipt_and_diff_cli(capsys):
    assert main(["run", "diagnostics.host", "--json"]) == 0
    first = json.loads(capsys.readouterr().out)["receipt_id"]
    assert main(["run", "environment.path", "--json"]) == 0
    second = json.loads(capsys.readouterr().out)["receipt_id"]
    assert main(["receipt", "latest", "--summary", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["receipt_id"] == second
    assert main(["receipt", "diff", first, second, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["changes"]


def test_no_color_and_dashboard_noninteractive(monkeypatch, capsys):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.setattr(
        "secripts.devices.transport_summary", lambda *a, **k: pytest.fail("Implicit device query")
    )
    assert main(["1337"]) == 0
    output = capsys.readouterr().out
    assert "\x1b" not in output
    assert all(
        label in output
        for label in (
            "SYSTEM",
            "DEVELOPMENT",
            "REPOSITORY",
            "DEVICES",
            "SECRIPTS",
            "RECOVERY LAB",
            "Noninteractive preview",
        )
    )


def test_cli_device_absence_and_failure_receipt(monkeypatch, capsys):
    monkeypatch.setattr("secripts.operations.shutil.which", lambda _: "/fixture/tool")
    monkeypatch.setattr(
        "secripts.evidence.run_command",
        lambda *a, **k: {
            "result": "PASS",
            "stdout": "List of devices attached\n",
            "stderr": "",
            "duration": 0,
            "exit_code": 0,
        },
    )
    assert main(["device", "inspect", "--json"]) == 3
    value = json.loads(capsys.readouterr().out)
    assert "NO DEVICE" in value["data"]["error"] and value["receipt_id"]


def test_failure_receipt_storage_error_is_clear(monkeypatch, capsys):
    def unavailable(*a, **k):
        raise OSError("fixture state path unavailable")

    monkeypatch.setattr("secripts.receipts.save", unavailable)
    assert main(["recovery", "inspect", "/does-not-exist", "--json"]) == 3
    assert json.loads(capsys.readouterr().out)["receipt_warning"]


def test_network_recipe_requires_explicit_permission(capsys):
    assert main(["recipe", "run", "github-readiness", "--json"]) == 4
    assert "--network" in json.loads(capsys.readouterr().out)["error"]


def test_search_legacy_source_filename():
    from secripts.registry import registry

    assert any(op.legacy for op in registry().search("Getting_Started_Git"))


def test_canonical_js_entry_point_and_no_old_alias(capsys):
    import importlib.metadata
    import tomllib
    from pathlib import Path

    metadata = tomllib.loads(Path("pyproject.toml").read_text())
    assert metadata["project"]["scripts"] == {"js": "secripts.cli:main"}
    points = {
        entry.name: entry.value
        for entry in importlib.metadata.distribution("jadis-secripts").entry_points
        if entry.group == "console_scripts"
    }
    assert points == {"js": "secripts.cli:main"}
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    text = capsys.readouterr().out
    assert text.startswith("usage: js ") and "usage: sec " not in text
    assert main(["run", "invalid.operation"]) == 2
    assert "Use js find" in capsys.readouterr().out
