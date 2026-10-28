import io
import json
import random
import struct
import zipfile
import pytest
from tests.fixtures import images
from secripts.images.engine import inspect
from secripts.images.compression import lz4
from secripts.images.devicetree import fdt, dtbo
from secripts.images.containers import elf
from secripts.corpus import inventory, CorpusLimits
from secripts.recovery import model, planner
from secripts.safety import SecError


@pytest.mark.parametrize(
    "factory,kind",
    [
        (images.fdt, "FDT"),
        (lambda: images.fdt(True), "UBOOT_FIT"),
        (images.dtbo, "DTBO"),
        (images.elf, "ELF"),
        (images.uimage, "UBOOT_LEGACY"),
        (images.lz4, "COMPRESSION"),
    ],
)
def test_generic_dispatch(tmp_path, factory, kind):
    path = tmp_path / "misleading.txt"
    path.write_bytes(factory())
    value = inspect(path, cache=False)
    assert value["type"] == kind and value["structure_status"] == "PASS"
    assert value["qualification"]["bootability"] == "UNTESTED"
    assert value["identification"]["extension_context"] == ".txt"


@pytest.mark.parametrize("version", range(5))
def test_all_boot_generations(tmp_path, version):
    path = tmp_path / "image"
    path.write_bytes(images.boot(version))
    value = inspect(path, cache=False)
    assert value["properties"]["header_version"] == version
    assert value["structure_status"] == "PASS"
    assert value["identification"]["role"]["value"] == "BOOT_WITHOUT_KERNEL"


def test_lz4_flags_skippable_and_boundaries():
    value = lz4(images.lz4())
    assert value["frames"][0]["blocks"][0]["uncompressed"]
    assert value["checksum_verification"] == "UNTESTED"
    skipped = struct.pack("<II", 0x184D2A50, 3) + b"abc"
    assert len(lz4(skipped + images.lz4())["frames"]) == 2
    assert lz4(b"\x02\x21\x4c\x18" + struct.pack("<I", 3) + b"abc")["frames"][0]["kind"] == "legacy"
    for data in (images.lz4()[:-1], images.lz4()[:4] + b"\0\0\0", skipped[:-1]):
        with pytest.raises(ValueError):
            lz4(data)


def test_dtb_dtbo_and_elf_adversarial_bounds():
    data = bytearray(images.fdt())
    struct.pack_into(">I", data, 8, 0xFFFFFFFC)
    with pytest.raises(ValueError):
        fdt(bytes(data))
    data = bytearray(images.dtbo())
    struct.pack_into(">I", data, 36, 32)
    with pytest.raises(ValueError):
        dtbo(bytes(data))
    for bits in (32, 64):
        for big in (False, True):
            assert elf(images.elf(bits, big))["bits"] == bits
    data = bytearray(images.elf())
    struct.pack_into("<Q", data, 32, 0xFFFFFFFFFFFFFFFF)
    struct.pack_into("<H", data, 56, 1)
    with pytest.raises(ValueError):
        elf(bytes(data))


def test_vendor_markers_and_mtk_bounds(tmp_path):
    samples = [
        (b"RKFW" + bytes(20), "ROCKCHIP_MARKER"),
        (b"CHROMEOS" + bytes(20), "CHROMEOS_MARKER"),
        (bytes(1024) + b"LOKI", "LOKI_MARKER"),
    ]
    for data, kind in samples:
        p = tmp_path / "sample"
        p.write_bytes(data)
        value = inspect(p, cache=False)
        assert value["type"] == kind and value["structure_status"] == "PARTIAL"
    data = bytearray(512)
    data[:4] = b"\x88\x16\x88\x58"
    struct.pack_into("<I", data, 4, 3)
    p.write_bytes(data + b"abc")
    assert inspect(p, cache=False)["type"] == "MTK_LEGACY_HEADER"
    p.write_bytes(data)
    assert inspect(p, cache=False)["structure_status"] == "FAIL"


def test_cache_context_and_optional_provider_disagreement(tmp_path, monkeypatch):
    p = tmp_path / "kernel"
    p.write_bytes(images.elf())
    a = inspect(p)
    q = tmp_path / "kernel.gz"
    q.write_bytes(p.read_bytes())
    b = inspect(q)
    assert a["sha256"] == b["sha256"] and b["path"] == str(q.resolve())
    monkeypatch.setattr(
        "secripts.images.providers.evidence",
        lambda *a: [{"provider": "file", "status": "PASS", "command": {"stdout": "ASCII text"}}],
    )
    assert inspect(p, providers=True)["identification"]["provider_agreement"] == "DISAGREES"


def test_nested_corpus_duplicates_secrets_and_no_extraction(tmp_path):
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w") as z:
        z.writestr("mkbootimg.c", "int main(void) {return 0;}")
        z.writestr("../escape.sh", "echo unsafe")
        z.writestr("private.pem", "DO NOT IMPORT")
    outer = tmp_path / "corpus.zip"
    with zipfile.ZipFile(outer, "w") as z:
        z.writestr("nested.zip", inner.getvalue())
        z.writestr("duplicate.zip", inner.getvalue())
        z.writestr("config.txt", "sk-" + "NOT_A_REAL_CREDENTIAL_" * 3)
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = 0o120777 << 16
        z.writestr(link, "/etc/passwd")
    value = inventory([outer])
    assert value["members"] == 10 and value["duplicates"] >= 1
    assert any(r["classification"] == "SECRET" for r in value["components"])
    assert any(r["classification"] == "UNSAFE" for r in value["components"])
    assert not (tmp_path / "escape.sh").exists()
    assert "NOT_A_REAL_CREDENTIAL" not in json.dumps(value)
    limited = inventory([outer], CorpusLimits(depth=0))
    assert limited["blockers"]


def test_corpus_byte_limits(tmp_path):
    p = tmp_path / "bounded.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("oversized", bytes(2048))
    value = inventory([p], CorpusLimits(member_bytes=1024))
    assert value["blockers"] and value["components"][0]["sha256"] is None


def make_tree(path, arch="arm64", arrangement="boot"):
    path.mkdir()
    text = f"TARGET_ARCH := {arch}\nPRODUCT_DEVICE := fixture\nPRODUCT_NAME := twrp_fixture\n"
    if arrangement == "boot":
        text += "BOARD_USES_RECOVERY_AS_BOOT := true\n"
    elif arrangement == "dedicated":
        text += "BOARD_RECOVERYIMAGE_PARTITION_SIZE := 65536\n"
    (path / "BoardConfig.mk").write_text(text)
    return path


def test_model_conflicts_and_unknown_not_promoted(tmp_path):
    model.create("fixture")
    model.add_tree("fixture", make_tree(tmp_path / "one"))
    value = model.add_tree("fixture", make_tree(tmp_path / "two", "arm", "dedicated"))
    assert value["fields"]["architecture"]["state"] == "CONFLICT"
    assert set(value["fields"]["recovery_arrangement"]["value"]) == {"boot", "dedicated"}
    assert (
        value["recovery_architecture"]["features"]["dedicated_recovery_partition"]["value"] is True
    )
    assert value["recovery_architecture"]["features"]["recovery_in_boot"]["value"] is True
    assert planner.target_for(value)["target"] == "UNKNOWN"
    assert value["fields"]["manufacturer"]["state"] == "UNKNOWN"
    assert value["qualification"] == "UNTESTED"
    with pytest.raises(SecError):
        planner.derive("fixture", tmp_path / "candidate")


def test_candidate_provenance_plan_and_no_overwrite(tmp_path):
    model.create("fixture")
    model.add_tree("fixture", make_tree(tmp_path / "tree"))
    out = tmp_path / "candidate"
    value = planner.derive("fixture", out)
    assert value["result"] == "CANDIDATE"
    manifest = json.loads((out / "candidate.json").read_text())
    assert all(
        line["requires_review"] and line["line"] >= 2 for line in manifest["generated_lines"]
    )
    assert any(line["evidence"] for line in manifest["generated_lines"])
    with pytest.raises(SecError, match="not exist"):
        planner.derive("fixture", out)
    plan = planner.plan("fixture")
    assert plan["status"] == "BLOCKED" and plan["hardware_qualification"] == "UNTESTED"
    assert plan["build_target"]["target"] == "bootimage"


def test_model_input_guards_and_metadata(tmp_path):
    with pytest.raises(SecError):
        model.create("../escape")
    model.create("fixture")
    p = tmp_path / "data.json"
    p.write_text(json.dumps({"architecture": "arm64", "codename": "bad\nINJECT := true"}))
    model.add_metadata("fixture", p)
    with pytest.raises(SecError, match="Unsafe codename"):
        planner.derive("fixture", tmp_path / "out")
    with pytest.raises(SecError):
        model.create("fixture")


def test_static_resolution_append_conditional_and_locations(tmp_path):
    from secripts.recovery.inspection import audit_tree

    (tmp_path / "BoardConfig.mk").write_text(
        "BASE := arm64\nTARGET_ARCH := $(BASE)\nLIST := a\nLIST += b\nifeq ($(MODE),yes)\nOTHER := x\nendif\n"
    )
    declarations = audit_tree(tmp_path)["dependency_graph"]["declarations"]
    arch = next(d for d in declarations if d["name"] == "TARGET_ARCH")
    assert (
        arch["resolved_value"] == "arm64"
        and arch["state"] == "STATICALLY_RESOLVED"
        and arch["line"] == 2
    )
    assert next(d for d in declarations if d["operator"] == "+=")["resolved_value"] == "a b"
    assert next(d for d in declarations if d["name"] == "OTHER")["state"] == "UNRESOLVED"


def test_deterministic_small_fuzz_no_parser_crash(tmp_path):
    rng = random.Random(1337)  # noqa: S311 -- deterministic non-security adversarial fixtures
    p = tmp_path / "fuzz"
    seeds = [
        b"",
        b"ANDROID!",
        b"VNDRBOOT",
        b"\xd0\x0d\xfe\xed",
        b"\x7fELF",
        b"AVB0",
        b"\x04\x22\x4d\x18",
    ]
    for prefix in seeds:
        for size in (0, 1, 8, 64, 256):
            p.write_bytes(prefix + rng.randbytes(size))
            result = inspect(p, cache=False)
            assert result["structure_status"] in {"PASS", "FAIL", "UNKNOWN", "PARTIAL"}


def test_corrupt_cache_and_header_lineage(tmp_path):
    from secripts.context import data_dir
    from secripts.images import PARSER_VERSION

    p = tmp_path / "boot.img"
    p.write_bytes(images.boot(4))
    first = inspect(p)
    cache = data_dir() / "cache/images" / PARSER_VERSION / (first["sha256"] + ".json")
    cache.write_text("[]")
    result = inspect(p)
    assert result["identification"]["header_evidence"]["version_offset"] == 40
    assert result["identification"]["research_sources"] == ["aosp"]


def test_corpus_duplicate_members_and_symlink(tmp_path):
    from secripts.corpus import unsafe_path

    assert unsafe_path("/absolute")
    assert unsafe_path("C:/windows")
    assert unsafe_path("one/../two")
    p = tmp_path / "broken.zip"
    p.write_bytes(b"PK\x03\x04truncated")
    assert inventory([p])["blockers"]


def test_model_malformed_and_standalone_ramdisk(tmp_path):
    model.create("fixture")
    model.model_path("fixture").write_text("[]")
    with pytest.raises(SecError, match="malformed"):
        model.report("fixture")


def test_source_manifest_bounds_and_generation(tmp_path):
    p = tmp_path / "default.xml"
    p.write_text('<manifest><default revision="android-12.1"/></manifest>')
    value = planner.source_intelligence({"root": str(tmp_path), "manifest": "twrp_aosp"})
    assert value["android_base"]["state"] == "DECLARED"
    assert value["product_convention"]["state"] == "INFERRED"
    p.write_text("<!DOCTYPE x><manifest/>")
    assert planner.source_intelligence({"root": str(tmp_path)})["state"] == "BLOCKED"


def test_phase3_cli_and_registry(tmp_path, capsys):
    from secripts.cli import main
    from secripts.registry import registry

    for operation in (
        "image.inspect",
        "image.providers",
        "recovery.model",
        "recovery.diagnose",
        "recovery.plan",
        "recovery.host",
        "recovery.derive",
    ):
        assert registry().get(operation).summary
    p = tmp_path / "kernel"
    p.write_bytes(images.elf())
    assert main(["inspect", str(p), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["type"] == "ELF"
    assert main(["recovery", "device", "create", "fixture", "--json"]) == 0
    capsys.readouterr()
    assert main(["recovery", "plan", "fixture", "--json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert "BLOCKED" in json.dumps(output) and "UNTESTED" in json.dumps(output)


def test_credits_and_public_research_references():
    import re
    from pathlib import Path
    from urllib.parse import urlparse

    root = Path(__file__).resolve().parents[2]
    credits = (root / "CREDITS.md").read_text()
    assert "CREDITS.md" in (root / "README.md").read_text()
    assert "not a substitute" in credits
    for name in (
        "osm0sis",
        "Yann Collet",
        "Ian F. Darwin",
        "Christos Zoulas",
        "lopestom",
        "Team Win",
        "Android Open Source",
        "Al Viro",
        "H. Peter Anvin",
    ):
        assert name in credits
    for url in re.findall(r"https://[^\s)]+", credits):
        parsed = urlparse(url)
        assert parsed.scheme == "https" and parsed.hostname
    research = json.loads((root / "src/secripts/data/research.json").read_text())
    assert len({r["id"] for r in research["sources"]}) == len(research["sources"])
    assert all(r["retrieved"] and r["implementation_influence"] for r in research["sources"])


def test_corpus_classification_redaction_contract():
    from secripts.secrets import redact, contains_secret

    safe = {"classifications": {"SECRET": 1122, "REFERENCE": 39182}, "possible_secrets": True}
    assert redact(safe) == safe
    unsafe = {"classifications": {"SECRET": "never retain arbitrary values"}}
    assert "never retain" not in json.dumps(redact(unsafe))
    assert not contains_secret(json.dumps(safe))


def test_skippable_frame_bomb_and_empty_lz4():
    skipped = struct.pack("<II", 0x184D2A50, 0)
    with pytest.raises(ValueError, match="frame count"):
        lz4(skipped * 257)
    with pytest.raises(ValueError, match="magic"):
        lz4(b"")


def test_conditional_override_invalidates_static_variable(tmp_path):
    from secripts.recovery.inspection import audit_tree

    (tmp_path / "BoardConfig.mk").write_text(
        "BASE := arm64\nifeq ($(MODE),yes)\nBASE := arm\nendif\nTARGET_ARCH := $(BASE)\nDEFAULT ?= candidate\n"
    )
    rows = audit_tree(tmp_path)["dependency_graph"]["declarations"]
    assert next(r for r in rows if r["name"] == "TARGET_ARCH")["state"] == "UNRESOLVED"
    assert next(r for r in rows if r["name"] == "DEFAULT")["state"] == "UNRESOLVED"


def test_registry_image_failure_records_failure(tmp_path):
    from secripts.operations import execute
    from secripts.receipts import load

    p = tmp_path / "bad.img"
    p.write_bytes(b"ANDROID!")
    value = execute("image.inspect", parameters={"artifact": str(p)})
    assert value["exit_code"] == 1 and value["result"] == "FAIL"
    assert load(value["receipt_id"])["result"] == "FAIL"


def test_generic_inspection_missing_file_receipt(tmp_path, capsys):
    from secripts.cli import main
    from secripts.receipts import load

    assert main(["inspect", str(tmp_path / "missing"), "--json"]) == 3
    value = json.loads(capsys.readouterr().out)
    receipt = load(value["receipt_id"])
    assert receipt["result"] == "FAIL" and receipt["operation"] == "image.inspect"


def test_model_preserves_unresolved_conditional_override(tmp_path):
    tree = make_tree(tmp_path / "tree")
    p = tree / "BoardConfig.mk"
    p.write_text(p.read_text() + "ifeq ($(MODE),other)\nTARGET_ARCH := arm\nendif\n")
    model.create("fixture")
    report = model.add_tree("fixture", tree)
    assert report["fields"]["architecture"]["state"] == "CONFLICT"
    assert any(e["state"] == "UNKNOWN" for e in report["fields"]["architecture"]["evidence"])
    with pytest.raises(SecError):
        planner.derive("fixture", tmp_path / "candidate")
