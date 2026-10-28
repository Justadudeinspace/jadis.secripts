import zipfile
import pytest
from secripts.provenance import inventory, ingest, validate
from secripts.safety import SecError


def test_ingestion_duplicates_secret_safe_and_rejected(tmp_path):
    path = tmp_path / "history.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("android-sdk.txt", "sdkmanager --list")
        z.writestr("copy.txt", "sdkmanager --list")
        z.writestr("private.txt", "sk-" + "NOT_A_REAL_CREDENTIAL_" * 3)
        z.writestr("blux/plan.md", "unrelated project")
        z.writestr("../escape.sh", "echo no")
    value = ingest(path, tmp_path / "inventory.json")
    assert [r["classification"] for r in value["artifacts"]] == [
        "EXTRACT",
        "REJECT",
        "SECRET",
        "REJECT",
        "REJECT",
    ]
    assert value["duplicates"] == 1
    assert not (tmp_path / "escape.sh").exists()
    assert "NOT_A_REAL" not in (tmp_path / "inventory.json").read_text()
    value["artifacts"][2]["classification"] = "PROMOTE"
    with pytest.raises(SecError):
        validate(value)


def test_zip_bomb_limit(tmp_path):
    path = tmp_path / "large.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("large.txt", b"0" * (8 * 1024 * 1024 + 1))
    with pytest.raises(SecError):
        inventory(path)
