"""Bounded AVB structures and native hash evidence; RSA delegated to explicit upstream tools."""

import hashlib
from pathlib import Path
import re
import struct
import tempfile
from secripts.images.avb import inspect_avb
from secripts.images.common import Reader
from secripts.images.artifacts import read, digest, exclusive, evidence, CAP
from secripts.images.providers import trusted_tool
from secripts.runner import run_command
from secripts.safety import SecError

SAFE_PARTITION = re.compile(r"[A-Za-z0-9_]{1,64}")


def metadata(path):
    path = Path(path)
    raw = read(path)
    basic = inspect_avb(path)
    if not basic["detected"] or basic["status"] == "FAIL":
        raise ValueError("Missing or malformed AVB metadata")
    offset = basic.get("footer", {}).get("vbmeta_offset", 0)
    r = Reader(raw)
    header = r.region(offset, 256)
    auth, aux = struct.unpack_from(">QQ", header, 12)
    if auth + aux > 4 * 1024**2:
        raise ValueError("AVB metadata budget")
    block = r.region(offset, 256 + auth + aux)
    signature_offset, signature_size = struct.unpack_from(">QQ", header, 48)
    hash_offset, hash_size = struct.unpack_from(">QQ", header, 32)
    public_offset, public_size = struct.unpack_from(">QQ", header, 64)
    pubmeta_offset, pubmeta_size = struct.unpack_from(">QQ", header, 80)
    desc_offset, desc_size = struct.unpack_from(">QQ", header, 96)
    if (
        signature_size
        and hash_size
        and max(signature_offset, hash_offset)
        < min(signature_offset + signature_size, hash_offset + hash_size)
    ):
        raise ValueError("AVB authentication regions overlap")
    aux_regions = [
        (public_offset, public_offset + public_size),
        (pubmeta_offset, pubmeta_offset + pubmeta_size),
        (desc_offset, desc_offset + desc_size),
    ]
    for index, (start, end) in enumerate(aux_regions):
        if start != end and any(
            a != b and max(start, a) < min(end, b) for a, b in aux_regions[:index]
        ):
            raise ValueError("AVB auxiliary regions overlap")
    data = r.region(offset + 256 + auth + desc_offset, desc_size)
    descriptors = []
    cursor = 0
    while cursor < len(data):
        reader = Reader(data[cursor:])
        tag, length = reader.unpack(">QQ")
        entry = reader.region(0, 16 + length)
        part = {"tag": tag, "bytes": len(entry), "state": "UNTRUSTED_DECLARATION"}
        fixed = None
        if tag == 2:
            values = reader.unpack(">Q32s4I", 16)
            size, algorithm, name_length, salt_length, digest_length, flags = values
            fixed = 132
            if any(reader.region(72, 60)):
                raise ValueError("Nonzero reserved hash descriptor fields")
            part.update(
                kind="HASH",
                image_size=size,
                hash_algorithm=algorithm.split(b"\0")[0].decode("ascii"),
                flags=flags,
            )
        elif tag == 1:
            values = reader.unpack(">IQQQIIIQQ32s4I", 16)
            (
                version,
                size,
                tree_offset,
                tree_size,
                data_block,
                hash_block,
                fec_roots,
                fec_offset,
                fec_size,
                algorithm,
                name_length,
                salt_length,
                digest_length,
                flags,
            ) = values
            fixed = 180
            if any(reader.region(120, 60)):
                raise ValueError("Nonzero reserved hashtree fields")
            part.update(
                kind="HASHTREE",
                dm_verity_version=version,
                image_size=size,
                tree_offset=tree_offset,
                tree_size=tree_size,
                data_block_size=data_block,
                hash_block_size=hash_block,
                fec_roots=fec_roots,
                fec_offset=fec_offset,
                fec_size=fec_size,
                hash_algorithm=algorithm.split(b"\0")[0].decode("ascii"),
                flags=flags,
            )
            if (
                data_block < 512
                or hash_block < 512
                or data_block & (data_block - 1)
                or hash_block & (hash_block - 1)
            ):
                raise ValueError("Invalid AVB hashtree block sizes")
        elif tag == 4:
            rollback, name_length, key_length, flags = reader.unpack(">4I", 16)
            if any(reader.region(32, 60)):
                raise ValueError("Nonzero reserved chain fields")
            name = reader.region(92, name_length).decode("utf-8")
            key = reader.region(92 + name_length, key_length)
            if 92 + name_length + key_length > len(entry):
                raise ValueError("AVB chain descriptor bounds")
            part.update(
                kind="CHAIN",
                partition=name,
                rollback_location=rollback,
                flags=flags,
                public_key_sha256=digest(key),
                public_key_bytes=key_length,
            )
        elif tag == 0:
            part.update(kind="PROPERTY", contents="NOT_DUMPED")
        elif tag == 3:
            part.update(kind="KERNEL_CMDLINE", contents="NOT_DUMPED")
        else:
            part.update(kind="UNKNOWN")
        if fixed is not None:
            if fixed + name_length + salt_length + digest_length > len(entry):
                raise ValueError("AVB descriptor variable lengths")
            name = reader.region(fixed, name_length).decode("utf-8")
            salt = reader.region(fixed + name_length, salt_length)
            expected = reader.region(fixed + name_length + salt_length, digest_length)
            part.update(partition=name, salt_hex=salt.hex(), digest_hex=expected.hex())
        if part.get("partition") and not SAFE_PARTITION.fullmatch(part["partition"]):
            raise ValueError("Unsafe AVB partition reference")
        descriptors.append(part)
        cursor += len(entry)
    public = r.region(offset + 256 + auth + public_offset, public_size)
    algorithm_id = struct.unpack_from(">I", header, 28)[0]
    hash_state = "NOT_APPLICABLE"
    if algorithm_id in range(1, 7):
        bits = {1: 2048, 2: 4096, 3: 8192, 4: 2048, 5: 4096, 6: 8192}[algorithm_id]
        algorithm = "sha256" if algorithm_id < 4 else "sha512"
        if (
            hash_size != hashlib.new(algorithm).digest_size
            or signature_size != bits // 8
            or public_size != 8 + bits // 4
        ):
            raise ValueError("AVB algorithm authentication/key sizes inconsistent")
        if struct.unpack_from(">I", public)[0] != bits:
            raise ValueError("AVB public key bit width inconsistent")
        declared = r.region(offset + 256 + hash_offset, hash_size)
        actual = hashlib.new(algorithm, header + r.region(offset + 256 + auth, aux)).digest()
        hash_state = (
            "AUTHENTICATION_HASH_MATCHED" if declared == actual else "AUTHENTICATION_HASH_MISMATCH"
        )

    return {
        **basic,
        "schema": 1,
        "model": "avb",
        "source_sha256": digest(raw),
        "algorithm_id": struct.unpack_from(">I", header, 28)[0],
        "descriptors": descriptors,
        "vbmeta_offset": offset,
        "vbmeta_size": len(block),
        "embedded_key": {
            "state": "EMBEDDED_KEY_IDENTIFIED" if public else "ABSENT",
            "sha256": digest(public) if public else None,
            "bytes": len(public),
        },
        "authentication_hash": hash_state,
        "authentication": {
            "bytes": auth,
            "hash_offset": hash_offset,
            "hash_size": hash_size,
            "signature_offset": signature_offset,
            "signature_size": signature_size,
        },
        "auxiliary": {
            "bytes": aux,
            "public_key_offset": public_offset,
            "public_key_size": public_size,
            "public_key_metadata_offset": pubmeta_offset,
            "public_key_metadata_size": pubmeta_size,
            "descriptors_offset": desc_offset,
            "descriptors_size": desc_size,
        },
        "rollback_state": "ROLLBACK_METADATA_PRESENT",
        "device_rollback_policy": "DEVICE_ROLLBACK_POLICY_UNVERIFIED",
        "root_of_trust": "ROOT_OF_TRUST_UNVERIFIED",
    }


def verify(path, *, expected_key=None, partitions=None):
    path = Path(path)
    value = metadata(path)
    raw = read(path)
    partitions = {name: Path(p) for name, p in (partitions or {}).items()}
    if any(not SAFE_PARTITION.fullmatch(name) for name in partitions):
        raise SecError("Invalid companion partition name", 4)
    if expected_key:
        public = read(expected_key, 65536)
        if b"PRIVATE KEY" in public or not (
            b"BEGIN PUBLIC KEY" in public or b"BEGIN RSA PUBLIC KEY" in public
        ):
            raise SecError("Expected key must be a PEM public key; private keys refused", 4)
    hashes = []
    for desc in value["descriptors"]:
        if desc["kind"] != "HASH":
            continue
        target = partitions.get(desc["partition"])
        payload = (
            read(target)
            if target
            else raw
            if value.get("footer")
            and len([d for d in value["descriptors"] if d["kind"] == "HASH"]) == 1
            else None
        )
        if payload is None:
            state = "BLOCKED_MISSING_PARTITION"
        elif desc["hash_algorithm"] not in {"sha256", "sha512", "sha1"}:
            state = "UNSUPPORTED_ALGORITHM"
        elif not desc["digest_hex"]:
            state = "UNVERIFIED_PERSISTENT_DIGEST"
        elif desc["image_size"] > len(payload):
            state = "HASH_DESCRIPTOR_INVALID"
        else:
            actual = hashlib.new(
                desc["hash_algorithm"],
                bytes.fromhex(desc["salt_hex"]) + payload[: desc["image_size"]],
            ).hexdigest()
            state = (
                "HASH_DESCRIPTOR_VALID"
                if actual == desc["digest_hex"]
                else "HASH_DESCRIPTOR_INVALID"
            )
        hashes.append({"partition": desc["partition"], "state": state})
    result = {
        "schema": 1,
        "metadata": value,
        "signature": "UNVERIFIED",
        "expected_key_match": "UNVERIFIED" if expected_key else "NOT_SUPPLIED",
        "hash_descriptors": hashes,
        "hashtrees": "UNVERIFIED",
        "chains": "UNVERIFIED",
        "vbmeta_digest": None,
        "device_rollback_policy": "DEVICE_ROLLBACK_POLICY_UNVERIFIED",
        "root_of_trust": "ROOT_OF_TRUST_UNVERIFIED",
        "providers": [],
        "status": "PARTIAL",
        "exit_code": 3,
    }
    unsafe_descriptor = any(
        d.get("image_size", 0) > CAP
        or d.get("data_block_size", 512) > 1024**2
        or d.get("hash_block_size", 512) > 1024**2
        or d.get("tree_size", 0) > CAP
        or d.get("tree_offset", 0) > CAP
        or d.get("fec_size", 0) > CAP
        for d in value["descriptors"]
    )
    tool = trusted_tool("avbtool")
    if unsafe_descriptor:
        result.update(
            status="FAIL",
            exit_code=1,
            signature="BLOCKED_UNBOUNDED_DESCRIPTOR",
            hashtrees="UNVERIFIED",
        )
        tool = None

    if not tool and not unsafe_descriptor:
        result["signature"] = "CRYPTO_PROVIDER_UNAVAILABLE"
    elif unsafe_descriptor:
        pass
    elif value["algorithm_id"] not in range(7):
        result.update(signature="UNSUPPORTED_ALGORITHM", exit_code=5)
    else:
        total = len(raw)
        with tempfile.TemporaryDirectory(prefix="js-avb-verify-") as directory:
            root = Path(directory)
            image = root / ".input.img"
            exclusive(image, raw)
            # For a footer-bearing single-image hash, provide an explicit isolated alias.
            local = dict(partitions)
            self_names = [
                h["partition"]
                for h in hashes
                if h["state"] in {"HASH_DESCRIPTOR_VALID", "HASH_DESCRIPTOR_INVALID"}
            ]
            if (
                value.get("footer")
                and len(self_names) == 1
                and self_names[0]
                and self_names[0] not in local
            ):
                local[self_names[0]] = path
            for name, source in local.items():
                data = read(source)
                total += len(data)
                if total > 2 * CAP:
                    raise SecError("AVB companion aggregate limit", 4)
                # Nested descriptor references must also be safe before any provider sees them.
                observed = inspect_avb(source)
                if observed["detected"]:
                    metadata(source)
                destination = root / (name + ".img")
                if destination != image:
                    exclusive(destination, data)
            argv = [tool, "verify_image", "--image", str(image)]
            if expected_key:
                key = root / "expected-public.pem"
                exclusive(key, public)
                argv += ["--key", str(key)]
            command = run_command(argv, timeout=20)
            result["providers"].append(
                {"provider": "avbtool", "capability": "verify_image", "command": command}
            )
            text = command["stdout"] + "\n" + command["stderr"]
            if value["algorithm_id"] == 0:
                result["signature"] = "UNSIGNED"
            elif "Successfully verified" in text and "vbmeta struct" in text:
                result["signature"] = "SIGNATURE_MATHEMATICALLY_VALID"
            elif command["result"] == "TIMEOUT":
                result["signature"] = "PROVIDER_TIMEOUT"
            elif "Signature check failed" in text:
                result["signature"] = "SIGNATURE_INVALID"
            else:
                result["signature"] = "UNVERIFIED_PROVIDER_FAILURE"
            if expected_key:
                result["expected_key_match"] = (
                    "EXPECTED_KEY_MISMATCH"
                    if "does not match given key" in text
                    else (
                        "EXPECTED_KEY_MATCH"
                        if result["signature"] == "SIGNATURE_MATHEMATICALLY_VALID"
                        and command["exit_code"] == 0
                        else "UNVERIFIED"
                    )
                )
            if re.search(
                r"hashtree of .* (?:does not match descriptor|contains invalid data)", text
            ):
                result.update(hashtrees="HASHTREE_INVALID", status="FAIL", exit_code=1)
            if command["exit_code"] == 0:
                result["hashtrees"] = (
                    "HASHTREE_VALID"
                    if any(d["kind"] == "HASHTREE" for d in value["descriptors"])
                    else "NOT_APPLICABLE"
                )
                result["chains"] = (
                    "NOT_APPLICABLE"
                    if not any(d["kind"] == "CHAIN" for d in value["descriptors"])
                    else "UNVERIFIED"
                )
                result.update(
                    status="PASS"
                    if result["signature"] == "SIGNATURE_MATHEMATICALLY_VALID"
                    else "PARTIAL",
                    exit_code=0,
                )
            elif (
                result["signature"] == "SIGNATURE_INVALID"
                or result["expected_key_match"] == "EXPECTED_KEY_MISMATCH"
                or any(h["state"] == "HASH_DESCRIPTOR_INVALID" for h in hashes)
            ):
                result.update(status="FAIL", exit_code=1)
            info = run_command([tool, "info_image", "--image", str(image)], timeout=10)
            result["providers"].append(
                {
                    "provider": "avbtool",
                    "capability": "info_image",
                    "command": info,
                    "algorithm_agreement": "AGREEMENT"
                    if f"Algorithm:                {value['algorithm']}" in info["stdout"]
                    else "UNVERIFIED",
                }
            )
            # calculate_vbmeta_digest follows chained references: only invoke when all are explicitly supplied.
            if not any(d["kind"] == "CHAIN" for d in value["descriptors"]):
                calculated = run_command(
                    [
                        tool,
                        "calculate_vbmeta_digest",
                        "--image",
                        str(image),
                        "--hash_algorithm",
                        "sha256",
                    ],
                    timeout=20,
                )
                result["providers"].append(
                    {
                        "provider": "avbtool",
                        "capability": "calculate_vbmeta_digest",
                        "command": calculated,
                    }
                )
                if calculated["exit_code"] == 0 and re.fullmatch(
                    r"[a-fA-F0-9]{64}", calculated["stdout"].strip()
                ):
                    result["vbmeta_digest"] = {
                        "state": "VBMETA_DIGEST_CALCULATED",
                        "sha256": calculated["stdout"].strip(),
                    }
    if any(h["state"] == "HASH_DESCRIPTOR_INVALID" for h in hashes):
        result.update(status="FAIL", exit_code=1)
    receipt = evidence("avb.verify", source=path, verification=result)
    result["receipt_id"] = receipt["receipt_id"]
    return result
