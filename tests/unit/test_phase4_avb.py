import shutil
import struct
import pytest
from secripts.images import avbmodel
from secripts.images.artifacts import digest
from secripts.runner import run_command
from secripts.safety import SecError


def unsigned():
    value = bytearray(256)
    value[:4] = b"AVB0"
    struct.pack_into(">II", value, 4, 1, 0)
    return value


def test_avb_native_layout_and_provider_absent(tmp_path, monkeypatch):
    p = tmp_path / "vbmeta.img"
    p.write_bytes(unsigned())
    value = avbmodel.metadata(p)
    assert value["algorithm"] == "NONE" and value["embedded_key"]["state"] == "ABSENT"
    assert value["root_of_trust"] == "ROOT_OF_TRUST_UNVERIFIED"
    monkeypatch.setattr(avbmodel, "trusted_tool", lambda name: None)
    result = avbmodel.verify(p)
    assert result["signature"] == "CRYPTO_PROVIDER_UNAVAILABLE" and result["exit_code"] == 3
    raw = bytearray(p.read_bytes())
    struct.pack_into(">I", raw, 28, 999)
    p.write_bytes(raw)
    monkeypatch.setattr(avbmodel, "trusted_tool", lambda name: "/usr/bin/avbtool")
    assert avbmodel.verify(p)["signature"] == "UNSUPPORTED_ALGORITHM"


def test_avb_hash_descriptor_native_verification_and_bounds(tmp_path, monkeypatch):
    content = b"legitimate synthetic data"
    salt = b"fixture"
    expected = bytes.fromhex(digest(salt + content))
    name = b"boot"
    descriptor = bytearray(132)
    struct.pack_into(">QQQ", descriptor, 0, 2, 0, len(content))
    descriptor[24:30] = b"sha256"
    struct.pack_into(">III", descriptor, 56, len(name), len(salt), len(expected))
    descriptor.extend(name + salt + expected)
    descriptor.extend(bytes((-len(descriptor)) % 8))
    struct.pack_into(">Q", descriptor, 8, len(descriptor) - 16)
    header = unsigned()
    aux = bytes(descriptor) + bytes((-len(descriptor)) % 64)
    struct.pack_into(">Q", header, 20, len(aux))
    struct.pack_into(">QQ", header, 96, 0, len(descriptor))
    p = tmp_path / "vbmeta.img"
    p.write_bytes(header + aux)
    boot = tmp_path / "boot.img"
    boot.write_bytes(content)
    monkeypatch.setattr(avbmodel, "trusted_tool", lambda name: None)
    assert (
        avbmodel.verify(p, partitions={"boot": boot})["hash_descriptors"][0]["state"]
        == "HASH_DESCRIPTOR_VALID"
    )
    boot.write_bytes(b"bad")
    assert avbmodel.verify(p, partitions={"boot": boot})["status"] == "FAIL"
    with pytest.raises(SecError, match="partition"):
        avbmodel.verify(p, partitions={"../escape": boot})
    raw = bytearray(p.read_bytes())
    struct.pack_into(">I", raw, 256 + 56, 0xFFFFFFFF)
    p.write_bytes(raw)
    with pytest.raises(ValueError):
        avbmodel.metadata(p)


def test_avb_private_expected_key_refused(tmp_path):
    p = tmp_path / "vbmeta.img"
    p.write_bytes(unsigned())
    key = tmp_path / "key.pem"
    key.write_text("PRIVATE KEY — synthetic marker, no key body")
    with pytest.raises(SecError, match="public key"):
        avbmodel.verify(p, expected_key=key)


@pytest.fixture
def real_avb_keys(tmp_path, request):
    if not shutil.which("avbtool") or not shutil.which("openssl"):
        pytest.skip("Optional installed avbtool/openssl unavailable")

    def cleanup():
        for key in tmp_path.glob("*.pem"):
            key.unlink(missing_ok=True)

    request.addfinalizer(cleanup)
    private = tmp_path / "ephemeral.pem"
    public = tmp_path / "public.pem"
    for argv in (
        [
            shutil.which("openssl"),
            "genpkey",
            "-algorithm",
            "RSA",
            "-pkeyopt",
            "rsa_keygen_bits:2048",
            "-out",
            str(private),
        ],
        [shutil.which("openssl"), "pkey", "-in", str(private), "-pubout", "-out", str(public)],
    ):
        assert run_command(argv, timeout=20)["exit_code"] == 0
    return private, public


def test_real_avb_signature_expected_key_and_tampering(tmp_path, real_avb_keys):
    private, public = real_avb_keys
    p = tmp_path / "vbmeta.img"
    command = run_command(
        [
            shutil.which("avbtool"),
            "make_vbmeta_image",
            "--algorithm",
            "SHA256_RSA2048",
            "--key",
            str(private),
            "--rollback_index",
            "42",
            "--output",
            str(p),
        ],
        timeout=20,
    )
    assert command["exit_code"] == 0
    value = avbmodel.verify(p, expected_key=public)
    assert value["signature"] == "SIGNATURE_MATHEMATICALLY_VALID"
    assert value["expected_key_match"] == "EXPECTED_KEY_MATCH"
    assert value["vbmeta_digest"]["state"] == "VBMETA_DIGEST_CALCULATED"
    assert value["device_rollback_policy"] == "DEVICE_ROLLBACK_POLICY_UNVERIFIED"
    assert value["root_of_trust"] == "ROOT_OF_TRUST_UNVERIFIED"
    assert value["status"] == "PASS"
    raw = bytearray(p.read_bytes())
    raw[256 + 32] ^= 1
    p.write_bytes(raw)
    bad = avbmodel.verify(p)
    assert bad["signature"] == "SIGNATURE_INVALID" and bad["exit_code"] == 1


def test_real_avb_wrong_key(tmp_path, real_avb_keys):
    private, public = real_avb_keys
    p = tmp_path / "vbmeta.img"
    assert (
        run_command(
            [
                shutil.which("avbtool"),
                "make_vbmeta_image",
                "--algorithm",
                "SHA256_RSA2048",
                "--key",
                str(private),
                "--output",
                str(p),
            ],
            timeout=20,
        )["exit_code"]
        == 0
    )
    wrong_private = tmp_path / "other.pem"
    wrong_public = tmp_path / "other-public.pem"
    assert (
        run_command(
            [
                shutil.which("openssl"),
                "genpkey",
                "-algorithm",
                "RSA",
                "-pkeyopt",
                "rsa_keygen_bits:2048",
                "-out",
                str(wrong_private),
            ],
            timeout=20,
        )["exit_code"]
        == 0
    )
    assert (
        run_command(
            [
                shutil.which("openssl"),
                "pkey",
                "-in",
                str(wrong_private),
                "-pubout",
                "-out",
                str(wrong_public),
            ],
            timeout=20,
        )["exit_code"]
        == 0
    )
    result = avbmodel.verify(p, expected_key=wrong_public)
    assert result["expected_key_match"] == "EXPECTED_KEY_MISMATCH" and result["exit_code"] == 1


def test_real_hashtree_valid_and_corrupt(tmp_path, real_avb_keys):
    private, public = real_avb_keys
    image = tmp_path / "system.img"
    image.write_bytes(b"synthetic filesystem" * 512)
    command = run_command(
        [
            shutil.which("avbtool"),
            "add_hashtree_footer",
            "--image",
            str(image),
            "--partition_name",
            "system",
            "--partition_size",
            "131072",
            "--algorithm",
            "SHA256_RSA2048",
            "--key",
            str(private),
            "--do_not_generate_fec",
        ],
        timeout=20,
    )
    assert command["exit_code"] == 0
    value = avbmodel.verify(image, expected_key=public, partitions={"system": image})
    assert value["signature"] == "SIGNATURE_MATHEMATICALLY_VALID"
    assert value["hashtrees"] == "HASHTREE_VALID"
    assert value["root_of_trust"] == "ROOT_OF_TRUST_UNVERIFIED"
    raw = bytearray(image.read_bytes())
    raw[0] ^= 1
    image.write_bytes(raw)
    invalid = avbmodel.verify(image, partitions={"system": image})
    assert invalid["hashtrees"] == "HASHTREE_INVALID" and invalid["exit_code"] == 1
