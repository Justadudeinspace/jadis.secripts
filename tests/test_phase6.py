"""Synthetic engineering invariants; none are physical-device/build qualification."""

import json
import pytest
from secripts.recovery import model, architecture, flags, dependencies, projects, fstab
from secripts.recovery.backend import TWRP
from secripts.cli import parser, recovery_dispatch
from secripts.safety import SecError


def device(tmp_path, declarations=""):
    model.create("sample")
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "BoardConfig.mk").write_text("TARGET_ARCH := arm64\n" + declarations)
    (tree / "twrp_sample.mk").write_text("PRODUCT_NAME := twrp_sample\n")
    return model.add_tree("sample", tree)


def lock():
    return {
        "schema": 1,
        "source": {
            "generation": "twrp-12.1",
            "manifest": "https://github.com/example/manifest",
            "revision": "a" * 40,
            "lunch": "twrp_sample-eng",
        },
        "dependencies": [
            {
                "id": "device",
                "role": "device",
                "repository": "https://github.com/example/device",
                "revision": "b" * 40,
                "path": "device/example/sample",
            }
        ],
    }


def select(tmp_path):
    path = tmp_path / "lock.json"
    path.write_text(json.dumps(lock()))
    return dependencies.select("sample", path)


@pytest.mark.parametrize(
    "declarations,targets",
    [
        ("BOARD_RECOVERYIMAGE_PARTITION_SIZE := 67108864\n", ["recoveryimage"]),
        ("BOARD_USES_RECOVERY_AS_BOOT := true\n", ["bootimage"]),
        ("BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true\n", ["vendorbootimage"]),
        (
            "BOARD_RECOVERYIMAGE_PARTITION_SIZE := 67108864\nBOARD_USES_RECOVERY_AS_BOOT := true\n",
            ["recoveryimage", "bootimage"],
        ),
        (
            "BOARD_RECOVERYIMAGE_PARTITION_SIZE := 67108864\nBOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true\n",
            ["recoveryimage", "vendorbootimage"],
        ),
        ("", []),
    ],
)
def test_composite_outputs(tmp_path, declarations, targets):
    d = device(tmp_path, declarations)
    g = architecture.graph(d)
    assert g["targets"] == targets
    assert g["hardware_qualification"] == "UNTESTED"
    assert all(o["flash_target"] == "NOT_INFERRED" for o in g["outputs"])


@pytest.mark.parametrize(
    "roles",
    [[], ["recovery"], ["boot", "vendor_boot"], ["recovery", "boot", "vendor_boot", "init_boot"]],
)
def test_presence_never_implies_build_output(roles):
    d = {
        "artifact_observations": [
            {"role": r, "source": r, "sha256": "a" * 64, "sections": ["kernel"]} for r in roles
        ]
    }
    a = architecture.compose(d)
    assert not a["conflicts"]
    assert architecture.graph(d)["targets"] == []
    for role in roles:
        assert a["features"][role + "_present"]["state"] == "USER_SUPPLIED"


def test_avb_graph_not_trust():
    a = architecture.compose(
        {
            "artifact_observations": [
                {
                    "role": "vbmeta",
                    "source": "test",
                    "sha256": "a" * 64,
                    "avb_descriptors": [
                        {"kind": "CHAIN", "partition": "vbmeta_system", "rollback_location": 2},
                        {"kind": "HASH", "partition": "boot"},
                    ],
                }
            ]
        }
    )
    assert {r["relation"] for r in a["avb_relationships"]} == {"chained_from", "verifies"}
    assert a["rollback_index_locations"] == [2]
    assert all(r["device_trust"] == "UNVERIFIED" for r in a["avb_relationships"])


def test_conflict_not_silently_resolved():
    d = {
        "configuration_evidence": [
            {"name": "BOARD_USES_RECOVERY_AS_BOOT", "resolved_value": v, "state": "DECLARED"}
            for v in ["true", ""]
        ]
    }
    a = architecture.compose(d)
    assert a["features"]["recovery_in_boot"]["state"] == "CONFLICT"
    assert architecture.graph(d)["status"] == "BLOCKED"


def test_kernel_dependency_edge(tmp_path):
    d = device(
        tmp_path,
        "BOARD_RECOVERYIMAGE_PARTITION_SIZE := 100000\nBOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE := true\n",
    )
    assert any(e["relation"] == "supplies_kernel_to" for e in architecture.graph(d)["edges"])
    assert flags.validate("sample")["status"] == "FAIL"


def test_override_not_observation(tmp_path):
    d = device(tmp_path, "BOARD_USES_RECOVERY_AS_BOOT := true\n")
    with pytest.raises(SecError):
        flags.change("sample", "BOARD_USES_RECOVERY_AS_BOOT", "")
    flags.change(
        "sample", "BOARD_USES_RECOVERY_AS_BOOT", "", acknowledge=True, reason="Reviewed alternative"
    )
    row = flags.view("sample")["flags"]["BOARD_USES_RECOVERY_AS_BOOT"]
    assert row["effective"] == {"value": False, "source": "USER_OVERRIDE"}
    assert row["observed"]["value"] is True
    assert model.report("sample")["recovery_architecture"] == d["recovery_architecture"]
    flags.change("sample", "BOARD_USES_RECOVERY_AS_BOOT", action="reset")
    assert (
        flags.view("sample")["flags"]["BOARD_USES_RECOVERY_AS_BOOT"]["effective"]["value"] is True
    )


def test_unset_reset_are_distinct(tmp_path):
    device(tmp_path, "BOARD_KERNEL_PAGESIZE := 4096\n")
    flags.change("sample", "BOARD_KERNEL_PAGESIZE", action="unset", acknowledge=True)
    v = flags.view("sample")
    assert v["flags"]["BOARD_KERNEL_PAGESIZE"]["effective"]["value"] is None
    assert "undefine BOARD_KERNEL_PAGESIZE" in flags.make(v)[0]
    flags.change("sample", "BOARD_KERNEL_PAGESIZE", action="reset")
    assert flags.view("sample")["flags"]["BOARD_KERNEL_PAGESIZE"]["effective"]["value"] == 4096


@pytest.mark.parametrize(
    "value", ["$(shell whoami)", "a;id", "x\ny", "`id`", "../kernel", "/root/kernel"]
)
def test_flag_injection_rejected(tmp_path, value):
    device(tmp_path)
    with pytest.raises(SecError):
        flags.change("sample", "TARGET_PREBUILT_KERNEL", value)


@pytest.mark.parametrize(
    "key",
    [
        "BOARD_AVB_BOOT_ROLLBACK_INDEX",
        "BOARD_AVB_INIT_BOOT_KEY_PATH",
        "BOARD_AVB_RECOVERY_ALGORITHM",
    ],
)
def test_signing_and_rollback_read_only(tmp_path, key):
    device(tmp_path)
    with pytest.raises(SecError):
        flags.change("sample", key, "1")


def test_profile_roundtrip_and_no_overwrite(tmp_path):
    device(tmp_path)
    flags.change("sample", "BOARD_KERNEL_PAGESIZE", "4096", reason="Documented header")
    before = flags.view("sample")["configuration_sha256"]
    flags.profile("save", "sample", "reviewed")
    with pytest.raises(SecError):
        flags.profile("save", "sample", "reviewed")
    flags.change("sample", "BOARD_KERNEL_PAGESIZE", "2048")
    assert flags.profile("diff", "sample", "reviewed")["changes"]
    flags.profile("apply", "sample", "reviewed")
    assert flags.view("sample")["configuration_sha256"] == before
    assert flags.profile("list") == ["reviewed"]


def test_profile_import_atomic(tmp_path):
    device(tmp_path)
    profile = tmp_path / "profile.json"
    profile.write_text(
        json.dumps(
            {
                "schema": 1,
                "kind": "SECRIPTS_FLAG_PROFILE",
                "overrides": {
                    "BOARD_KERNEL_PAGESIZE": {"value": 4096},
                    "BOARD_AVB_BOOT_ROLLBACK_INDEX": {"value": 4},
                },
            }
        )
    )
    with pytest.raises(SecError):
        flags.import_profile("sample", profile)
    assert flags.view("sample")["flags"]["BOARD_KERNEL_PAGESIZE"]["user_override"] is None


def test_source_generation_is_not_android_version(tmp_path):
    device(tmp_path)
    assert flags.view("sample")["source_generation"] == "UNKNOWN"
    select(tmp_path)
    flags.change("sample", "BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE", "1000000")
    assert any(
        r["state"] == "UNSUPPORTED_FOR_SOURCE_GENERATION"
        for r in flags.validate("sample")["findings"]
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"path": "../device"},
        {"path": "/outside/device"},
        {"repository": "https://evil.invalid/thing"},
        {"revision": "main"},
        {"role": "shell"},
    ],
)
def test_unsafe_lock_rejected(changes):
    data = lock()
    data["dependencies"][0].update(changes)
    with pytest.raises(SecError):
        dependencies.validate_lock(data)


def test_dependency_dryrun_no_network(tmp_path, monkeypatch):
    device(tmp_path)
    select(tmp_path)
    monkeypatch.setattr(
        dependencies, "run_command", lambda *a, **k: pytest.fail("No network on dry-run")
    )
    r = dependencies.resolve("sample", root=tmp_path / "sources")
    assert r["network"] == "NOT_USED"
    assert not (tmp_path / "sources").exists()
    assert dependencies.validate("sample")["status"] == "BLOCKED"


@pytest.mark.parametrize(
    "line",
    [
        "/system ext4 /dev/block/by-name/system flags=slotselect",
        "system /system ext4 ro wait,logical,slotselect",
        "/data f2fs /dev/block/by-name/userdata flags=fileencryption=aes-256-xts",
    ],
)
def test_fstab_preserves_declaration(line):
    row = fstab.parse(line.split(), "source", "fstab:1")
    assert row is not None
    result, _ = fstab.generate({"fstab_evidence": [row]})
    assert result.strip() == line


@pytest.mark.parametrize(
    "line", ["../x /data ext4", "/dev/block/x /data ext4 $(shell id)", "/dev/block/x /data unknown"]
)
def test_fstab_unsafe_or_unknown(line):
    assert fstab.parse(line.split(), "s", "1") is None


def test_fstab_conflicts_no_generation():
    rows = [
        fstab.parse(line.split(), "s", "1")
        for line in ["x /data ext4 ro wait", "y /data f2fs rw wait"]
    ]
    assert fstab.generate({"fstab_evidence": rows})[0] == ""


def test_status_persists_and_never_qualifies(tmp_path):
    device(tmp_path)
    result = projects.status("sample")
    assert result["areas"]["HARDWARE"] == "UNTESTED"
    assert projects.load("sample", "status")["input_sha256"] == result["input_sha256"]
    assert result["next"]["command"]


def test_multi_target_vector_safety():
    cmd = TWRP().build_command("twrp_sample-eng", ["recoveryimage", "vendorbootimage"])
    assert cmd[-2:] == ["recoveryimage", "vendorbootimage"]
    with pytest.raises(SecError):
        TWRP().build_command("twrp_sample-eng", ["recoveryimage;id"])


def test_aliases_share_editor(tmp_path):
    device(tmp_path)
    short = parser().parse_args(["ry", "flags", "sh", "sample", "TARGET_ARCH", "--json"])
    long = parser().parse_args(["recovery", "flags", "show", "sample", "TARGET_ARCH", "--json"])
    assert recovery_dispatch(short) == recovery_dispatch(long)


def test_old_schema_adapts_without_rewrite(tmp_path):
    model.create("sample")
    path = model.model_path("sample")
    v = json.loads(path.read_text())
    v["schema"] = 1
    path.write_text(json.dumps(v))
    assert model.load("sample")["schema"] == 2
    assert json.loads(path.read_text())["schema"] == 1


def test_chain_stored_override_not_applied(tmp_path):
    from secripts.recovery.chain import prepare

    device(tmp_path, "BOARD_RECOVERYIMAGE_PARTITION_SIZE := 1000000\n")
    flags.change("sample", "BOARD_KERNEL_PAGESIZE", 4096)
    r = prepare("sample", {"tree": str(tmp_path / "tree"), "targets": ["recoveryimage"]})
    assert any("Override not proven applied" in b for b in r["blockers"])
    assert r["hardware_qualification"] == "UNTESTED"


def test_init_boot_and_dedicated_coexist():
    data = {
        "configuration_evidence": [
            {
                "name": "BOARD_RECOVERYIMAGE_PARTITION_SIZE",
                "resolved_value": "100000",
                "state": "DECLARED",
            }
        ],
        "artifact_observations": [
            {
                "role": r,
                "source": r,
                "sha256": "f" * 64,
                "sections": [],
                "recovery_markers": ["init.recovery.*"] if r == "init_boot" else [],
            }
            for r in ["boot", "init_boot", "vendor_boot", "recovery"]
        ],
    }
    g = architecture.graph(data)
    assert g["targets"] == ["recoveryimage", "initbootimage"]
    assert g["status"] == "BLOCKED"
    assert len([n for n in g["nodes"] if n["kind"] == "artifact"]) == 4


def test_invalid_resource_flags(tmp_path):
    device(tmp_path)
    select(tmp_path)
    for key in ["BOARD_USES_RECOVERY_AS_BOOT", "BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT"]:
        flags.change("sample", key, "true")
    validation = flags.validate("sample")
    assert validation["status"] == "FAIL"
    assert {r["state"] for r in validation["findings"]} >= {
        "INVALID_COMBINATION",
        "MISSING_DEPENDENCY",
    }


@pytest.mark.parametrize("value", ["-1", "0", "18446744073709551616", "4096 * 2"])
def test_invalid_partition_sizes(tmp_path, value):
    device(tmp_path)
    with pytest.raises(SecError):
        flags.change("sample", "BOARD_RECOVERYIMAGE_PARTITION_SIZE", value)


def test_corrupt_project_state(tmp_path):
    device(tmp_path)
    projects.directory("sample").mkdir(parents=True)
    (projects.directory("sample") / "flags.json").write_text('{"schema":999}')
    with pytest.raises(SecError):
        flags.view("sample")


def test_unreviewed_symlink_download_root(tmp_path):
    device(tmp_path)
    select(tmp_path)
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    with pytest.raises(SecError):
        dependencies.resolve("sample", root=alias)


def test_model_free_recipe_no_ai(tmp_path, monkeypatch):
    from secripts.recipes import run

    device(tmp_path)
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    result = run("recovery-configuration-review", parameters={"model": "sample"})
    assert result["exit_code"] == 0
    assert len(result["steps"]) == 4
    assert result["status"] != "PASS"
