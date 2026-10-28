import pytest


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRIPTS_DATA_HOME", str(tmp_path / "state"))
