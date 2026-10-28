import argparse
import json

import pytest

from secripts.cli import main, parser
from secripts.commands import CommandName, collision_audit, inventory, name, normalize
from secripts.receipts import load
from secripts.completion import candidates
from tests.unit.test_image_phase2 import boot, newc

TOP = [row for row in inventory(parser()) if not row["scope"]]


@pytest.mark.parametrize("row", TOP, ids=lambda row: row["identity"])
def test_root_aliases_same_parser_help_and_identity(row, capsys):
    p = parser()
    action = next(a for a in p._actions if isinstance(a, argparse._SubParsersAction))
    canonical = action.choices[row["canonical"]]
    for alias in row["aliases"]:
        assert action.choices[alias] is canonical
        with pytest.raises(SystemExit) as exc:
            p.parse_args([alias, "--help"])
        assert exc.value.code == 0
        output = capsys.readouterr().out
        assert "js " + row["canonical"] in output
        assert "Aliases:" in output


@pytest.mark.parametrize(
    "first,second",
    [
        (["ls", "--json"], ["list", "--json"]),
        (["fd", "android", "--json"], ["find", "android", "--json"]),
        (["exp", "git.status", "--json"], ["explain", "git.status", "--json"]),
        (["ry", "doc", "--json"], ["recovery", "doctor", "--json"]),
        (["ry", "dce", "ls", "--json"], ["recovery", "device", "list", "--json"]),
        (["ry", "tree", "diag", "fixture"], ["recovery", "tree", "diagnose", "fixture"]),
        (["img", "rt", "fixture", "--dry-run"], ["image", "roundtrip", "fixture", "--dry-run"]),
        (
            ["ram", "ext", "fixture", "--output", "out", "--dry-run"],
            ["ramdisk", "extract", "fixture", "--output", "out", "--dry-run"],
        ),
        (
            ["dtbo", "rb", "workspace", "--output", "out"],
            ["dtbo", "rebuild", "workspace", "--output", "out"],
        ),
        (["rcp", "sh", "python-dev"], ["recipe", "show", "python-dev"]),
        (["rcpt", "latest"], ["receipt", "latest"]),
        (["receipts", "latest"], ["receipt", "latest"]),
    ],
)
def test_alias_argument_parity(first, second):
    p = parser()
    assert vars(normalize(p.parse_args(first))) == vars(normalize(p.parse_args(second)))


def test_scoped_collision_contract_and_map():
    rows = inventory(parser())
    scopes = {}
    for row in rows:
        scopes.setdefault(tuple(row["scope"]), []).append(
            CommandName(row["identity"], row["canonical"], tuple(row["aliases"]))
        )
    for commands in scopes.values():
        assert collision_audit(commands)
    with pytest.raises(ValueError, match="collision"):
        collision_audit([CommandName("one", "x"), CommandName("two", "other", ("x",))])
    assert name("device").canonical == "dce"
    assert "dev" not in name("device").tokens
    assert name("1337").tokens == ("1337",)


def test_alias_json_equivalence_and_receipt_identity(tmp_path, capsys):
    image = boot(tmp_path / "boot.img", newc(), b"kernel")
    values = []
    for argv in (
        ["insp", str(image), "--json"],
        ["inspect", str(image), "--json"],
        ["img", "insp", str(image), "--json"],
        ["image", "inspect", str(image), "--json"],
    ):
        assert main(argv) == 0
        value = json.loads(capsys.readouterr().out)
        receipt = load(value.pop("receipt_id"))
        assert receipt["operation"] == "image.inspect"
        values.append(value)
    assert all(value == values[0] for value in values)


def test_mutating_alias_guards_and_failure_receipts(tmp_path, capsys):
    p = boot(tmp_path / "boot.img", newc(), b"kernel")
    existing = tmp_path / "exists"
    existing.mkdir()
    for argv in (["img", "upk"], ["image", "unpack"]):
        assert main([*argv, str(p), "--output", str(existing), "--json"]) == 4
        value = json.loads(capsys.readouterr().out)
        assert value["operation"] == "image.unpack" and value["result"] == "FAIL"
        assert load(value["receipt_id"])["operation"] == "image.unpack"
    for argv in (["ry", "boot"], ["recovery", "boot"]):
        assert main([*argv, str(p), "--json"]) == 4
        value = json.loads(capsys.readouterr().out)
        assert load(value["receipt_id"])["operation"] == "recovery.boot"


def test_alias_dry_run_no_writes(tmp_path, capsys):
    absent = tmp_path / "not-present"
    output = tmp_path / "output"
    for argv in (["img", "upk"], ["image", "unpack"]):
        assert main([*argv, str(absent), "--output", str(output), "--dry-run", "--json"]) == 0
        assert json.loads(capsys.readouterr().out)["result"] == "DRY_RUN"
        assert not output.exists()


def test_alias_completion_and_error_suggestion(capsys):
    assert candidates(["img"]) == candidates(["image"])
    assert candidates(["ry", "dce"]) == candidates(["recovery", "device"])
    assert candidates(["rcp", "sh"]) == candidates(["recipe", "show"])
    assert candidates([]).index("ls") < candidates([]).index("list")
    assert "upk" in candidates(["img"]) and "unpack" in candidates(["img"])
    with pytest.raises(SystemExit) as exc:
        main(["inspec", "anything"])
    assert exc.value.code == 2
    output = capsys.readouterr().err
    assert "Did you mean:" in output and "insp" in output and "inspect" in output
