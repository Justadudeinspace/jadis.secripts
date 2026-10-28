import json
import pytest
from secripts.cli import main


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--help"],
        ["--version"],
        ["list", "--json"],
        ["find", "android"],
        ["show", "git.status"],
        ["explain", "android.sdk.validate"],
        ["doctor", "--json"],
        ["run", "git.status", "--dry-run"],
        ["1337"],
        ["recovery"],
        ["recovery", "doctor", "--json"],
        ["recipes"],
        ["recipe", "show", "android-dev"],
        ["recipe", "run", "git-review", "--dry-run"],
        ["archaeology"],
        ["history"],
    ],
)
def test_cli_safe_surfaces(argv, capsys):
    try:
        result = main(argv)
    except SystemExit as exc:
        result = exc.code
    assert result == 0
    output = capsys.readouterr().out
    assert output
    if "--json" in argv:
        json.loads(output)


@pytest.mark.parametrize(
    "argv,code",
    [
        (["run", "invalid"], 2),
        (["receipt", "bad"], 2),
        (["recovery", "inspect", "/nonexistent.img"], 3),
        (["recovery", "tree", "audit", "/nonexistent-tree"], 3),
        (["recovery", "build"], 3),
        (["recovery", "inspect"], 2),
    ],
)
def test_cli_failure_surfaces(argv, code, capsys):
    assert main(argv) == code
    assert "error" in capsys.readouterr().out.lower()


def test_console_degraded_descriptions(capsys):
    assert main(["1337"]) == 0
    text = capsys.readouterr().out
    assert "Noninteractive preview" in text
    assert "Inspect SDK" in text and "Sanitized lineage" in text


def test_console_interactive_paths(monkeypatch, capsys):
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(
        "secripts.ui.console.dashboard",
        lambda **kwargs: {"host": "fixture; device probing disabled"},
    )
    answers = iter(["4", "git.status", "D", "A", "git", "3", "doctor", "B", "Q"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main(["1337"]) == 0
    output = capsys.readouterr().out
    assert "DRY_RUN" in output and "RECOVERY LAB // TWRP" in output
    assert "RECEIPT" in output and "MODERN REPLACEMENT" in output


def test_temporary_boot_refused_with_receipt(tmp_path, capsys):
    image = tmp_path / "image.img"
    image.write_bytes(b"fixture")
    assert main(["recovery", "boot", str(image), "--json"]) == 4
    value = json.loads(capsys.readouterr().out)
    assert value["receipt_id"] and "UNRESOLVED" in value["error"]
