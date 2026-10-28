from pathlib import Path
import struct
import pytest
from secripts.recovery.inspection import inspect_image, audit_tree, artifact_hash
from secripts.recovery.workspace import initialize, load_workspace, sync, build, recovery_doctor
from secripts.recovery.qualification import record, report, markdown
from secripts.recovery.device import inspect_device
from secripts.safety import SecError


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "workspace"
    tree = root / "device/test/example"
    tree.mkdir(parents=True)
    (tree / "BoardConfig.mk").write_text(
        "TARGET_ARCH := arm64\nBOARD_BOOT_HEADER_VERSION := 4\nTARGET_PREBUILT_KERNEL := missing-kernel\n"
    )
    (tree / "AndroidProducts.mk").write_text("PRODUCT_MAKEFILES := $(LOCAL_DIR)/twrp_example.mk\n")
    (tree / "twrp_example.mk").write_text("PRODUCT_NAME := twrp_example\n")
    return initialize(
        root,
        "example",
        tree,
        "https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git",
        "twrp-12.1",
        "twrp_example-eng",
        "vendorbootimage",
    )


def test_workspace_validation(workspace):
    assert load_workspace() == workspace
    assert sync(dry_run=True)["exit_code"] == 0
    assert build(dry_run=True)["result"] == "DRY_RUN"
    from secripts.recovery.workspace import validate_workspace

    for updates in (
        {"backend": "imaginary"},
        {"device": "../bad"},
        {"manifest": "file:///tmp/foo"},
        {"target": "guessed"},
        {"tree": "/outside"},
    ):
        with pytest.raises(SecError):
            validate_workspace({**workspace, **updates})


def test_tree_audit_and_missing_fields(workspace, tmp_path):
    value = audit_tree(Path(workspace["tree"]))
    assert value["variables"]["TARGET_ARCH"] == "arm64"
    assert any(f["check"] == "missing local reference" for f in value["findings"])
    assert value["hardware"] == "UNTESTED"
    assert audit_tree(tmp_path)["result"] == "REVIEW_REQUIRED"  # contains fixture tree
    empty = tmp_path / "empty"
    empty.mkdir()
    assert audit_tree(empty)["result"] == "FAIL"


def test_image_metadata(tmp_path):
    path = tmp_path / "boot.img"
    path.write_bytes(b"unknown")
    assert inspect_image(path)["confidence"] == "UNRESOLVED"
    header = bytearray(4096)
    header[:8] = b"ANDROID!"
    struct.pack_into("<I", header, 40, 4)
    path.write_bytes(header)
    value = inspect_image(path)
    assert value["type"] == "ANDROID_BOOT"
    assert value["properties"]["header_version"] == 4
    assert len(artifact_hash(path)) == 64
    struct.pack_into("<I", header, 8, 999999)
    path.write_bytes(header)
    with pytest.raises(SecError, match="payload"):
        inspect_image(path)
    path.write_bytes(b"ANDROID!")
    with pytest.raises(SecError, match="Truncated"):
        inspect_image(path)
    with pytest.raises(SecError):
        inspect_image(tmp_path / "absent")


def test_qualification_no_auto_pass(tmp_path):
    path = tmp_path / "artifact.img"
    path.write_bytes(b"fixture")
    value = record(path, "test-device")
    assert all(a["state"] == "UNTESTED" for a in value["areas"].values())
    with pytest.raises(SecError):
        record(path, "test-device", "touch", "PASS")
    record(path, "test-device", "touch", "BLOCKED", "No test hardware")
    value = report(path, "test-device")
    assert "boot" in value["untested"] and value["build"] is None
    assert "BLOCKED" in markdown(value)
    with pytest.raises(SecError):
        record(path, "different-device")


def test_device_disconnected_or_missing(monkeypatch):
    monkeypatch.setattr(
        "secripts.recovery.device.run_command",
        lambda _: {"result": "PASS", "stdout": "List of devices attached\n"},
    )
    with pytest.raises(SecError, match="Exactly one"):
        inspect_device()
    monkeypatch.setattr("secripts.recovery.device.run_command", lambda _: {"result": "MISSING"})
    with pytest.raises(SecError, match="unavailable"):
        inspect_device()


def test_sync_network_failure_and_low_disk(workspace, monkeypatch):
    monkeypatch.setattr("secripts.recovery.workspace.disk_check", lambda _: None)
    monkeypatch.setattr("secripts.recovery.workspace.shutil.which", lambda _: "/test/repo")
    monkeypatch.setattr(
        "secripts.recovery.workspace.run_command",
        lambda *a, **k: {"result": "FAIL", "exit_code": 1, "stderr": "network unavailable"},
    )
    value = sync()
    assert value["exit_code"] == 1 and value["receipt"]["result"] == "FAIL"
    monkeypatch.undo()
    from secripts.recovery.workspace import disk_check
    from collections import namedtuple

    disk = namedtuple("Disk", "total used free")
    monkeypatch.setattr("secripts.recovery.workspace.shutil.disk_usage", lambda _: disk(10, 9, 1))
    with pytest.raises(SecError, match="Insufficient"):
        disk_check(Path(workspace["root"]))


def test_build_failure_recorded(workspace, monkeypatch):
    root = Path(workspace["root"])
    (root / "build").mkdir()
    (root / "build/envsetup.sh").write_text("# fixture; never executed")
    monkeypatch.setattr("secripts.recovery.workspace.disk_check", lambda _: None)
    monkeypatch.setattr("secripts.recovery.workspace.host", lambda: {"architecture": "x86_64"})
    commands = iter(
        [
            {"result": "PASS", "stdout": "<manifest/>", "exit_code": 0},
            {"result": "PASS", "stdout": "abc123", "exit_code": 0},
            {"result": "FAIL", "stdout": "", "stderr": "fixture compile error", "exit_code": 2},
        ]
    )
    monkeypatch.setattr("secripts.recovery.workspace.run_command", lambda *a, **k: next(commands))
    value = build()
    assert value["exit_code"] == 1 and value["build"]["artifacts"] == []
    assert Path(value["output"], "build.log").is_file()
    assert not list(Path(value["output"]).glob("*.img"))


def test_recovery_doctor_hardware_unknown(monkeypatch):
    value = recovery_doctor()
    assert value["device_qualification"] == "UNTESTED"
    assert next(c for c in value["checks"] if c["name"] == "hardware")["status"] == "UNKNOWN"


def test_workspace_concurrency_refused(workspace):
    import fcntl

    root = Path(workspace["root"])
    with (root / ".secripts-workspace.lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(SecError, match="busy"):
            sync()
        # A plan does not require acquiring a mutation lock.
        assert sync(dry_run=True)["exit_code"] == 0


def test_build_collects_real_artifact_fixture(workspace, monkeypatch):
    root = Path(workspace["root"])
    (root / "build").mkdir()
    (root / "build/envsetup.sh").write_text("# fixture")
    monkeypatch.setattr("secripts.recovery.workspace.disk_check", lambda _: None)
    monkeypatch.setattr("secripts.recovery.workspace.host", lambda: {"architecture": "x86_64"})
    expected = root / "out/target/product/example/vendor_boot.img"

    def command(argv, **kwargs):
        if argv[0] == "bash":
            expected.parent.mkdir(parents=True)
            expected.write_bytes(b"synthetic artifact; not a recovery image")
        return {
            "result": "PASS",
            "stdout": "fixture revision metadata",
            "stderr": "",
            "exit_code": 0,
        }

    monkeypatch.setattr("secripts.recovery.workspace.run_command", command)
    value = build()
    assert value["build"]["result"] == "BUILD_SUCCESS"
    assert value["build"]["device_qualification"] == "UNTESTED"
    artifact = value["build"]["artifacts"][0]
    assert artifact_hash(Path(artifact["path"])) == artifact["sha256"]


def test_vendor_boot_bounds(tmp_path):
    path = tmp_path / "vendor_boot.img"
    header = bytearray(4096)
    header[:8] = b"VNDRBOOT"
    struct.pack_into("<II", header, 8, 4, 4096)
    struct.pack_into("<I", header, 2096, 2128)
    path.write_bytes(header)
    assert inspect_image(path)["properties"]["ramdisk_entries"] == 0
    struct.pack_into("<I", header, 24, 100000)
    path.write_bytes(header)
    with pytest.raises(SecError, match="beyond"):
        inspect_image(path)


def test_tree_fstab_and_dependencies(workspace):
    tree = Path(workspace["tree"])
    (tree / "recovery.fstab").write_text(
        "/data f2fs /dev/block/by-name/userdata flags=fileencryption=ice\nmalformed\n"
    )
    (tree / "twrp.dependencies").write_text(
        '[{"repository": "android_device_common", "target_path": "device/vendor/common"}]'
    )
    (tree / "conditional.mk").write_text("ifeq ($(MODE),yes)\nTARGET_ARCH := arm\nendif\n")
    value = audit_tree(tree)
    checks = {f["check"] for f in value["findings"]}
    assert {
        "fstab declaration",
        "malformed fstab entry",
        "external dependency",
        "conditional make declarations",
    } <= checks
    assert value["configuration_hashes"]["BoardConfig.mk"]
