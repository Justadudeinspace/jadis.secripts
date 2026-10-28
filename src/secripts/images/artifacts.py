"""Private canonical model I/O and exclusive outputs; payload paths are fixed identifiers."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from secripts.images.common import artifact_hash
from secripts.receipts import save
from secripts.safety import SecError

CAP = 128 * 1024**2


def read(path, cap=CAP):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > cap:
        raise SecError("Artifact must be a bounded regular non-symlink file", 3)
    with path.open("rb") as stream:
        data = stream.read(cap + 1)
    if len(data) > cap:
        raise SecError("Artifact grew beyond input limit", 4)
    return data


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(path, value):
    """Exact artifact metadata, not a receipt. Never serialize firmware payload bodies."""
    payload = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()
    if len(payload) > 8 * 1024**2:
        raise SecError("Canonical metadata exceeds model budget", 4)
    exclusive(path, payload)


def exclusive(path, data):
    path = Path(path)
    if path.exists() or path.is_symlink() or not path.parent.is_dir():
        raise SecError("Output must be new, with an existing parent; overwrite refused", 4)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def json_model(path, kind):
    try:
        value = json.loads(read(path, 8 * 1024**2))
        if not isinstance(value, dict) or value.get("schema") != 1 or value.get("model") != kind:
            raise ValueError("Unsupported model/schema")
        return value
    except (ValueError, TypeError, KeyError) as exc:
        raise SecError("Malformed or unsupported artifact model", 3) from exc


def child(root, relative):
    """Only normalized local paths; reject every symlink component."""
    root = Path(root).resolve()
    p = Path(relative)
    if p.is_absolute() or not p.parts or any(s in {".", ".."} for s in p.parts):
        raise SecError("Unsafe model payload path", 4)
    target = root
    for part in p.parts:
        target = target / part
        if target.is_symlink():
            raise SecError("Symlink in artifact workspace refused", 4)
    if not target.is_relative_to(root):
        raise SecError("Workspace escape refused", 4)
    return target


class NewWorkspace:
    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        if self.path.exists() or self.path.is_symlink() or not self.path.parent.is_dir():
            raise SecError("Workspace must be a new directory with existing parent", 4)
        self.temp = tempfile.TemporaryDirectory(prefix=".js-artifact-", dir=self.path.parent)
        self.root = Path(self.temp.name) / "workspace"
        self.root.mkdir(mode=0o700)
        for folder in ("source", "extracted", "model", "rebuilt", "reports", "evidence"):
            (self.root / folder).mkdir(mode=0o700)
        return self.root

    def __exit__(self, kind, value, trace):
        try:
            if kind is None:
                self.path.mkdir(mode=0o700)
                try:
                    os.replace(self.root, self.path)
                except OSError:
                    self.path.rmdir()
                    raise
        finally:
            self.temp.cleanup()


def evidence(operation, *, source=None, output=None, **details):
    value = {"model_version": 1, "timestamp": datetime.now(timezone.utc).isoformat(), **details}
    if source:
        source = Path(source)
        value.update(
            source_artifact=str(source),
            source_sha256=artifact_hash(source),
            source_size=source.stat().st_size,
        )
    if output:
        output = Path(output)
        value.update(
            output_artifact=str(output),
            output_sha256=artifact_hash(output),
            output_size=output.stat().st_size,
        )
    return save(
        operation,
        "MUTATING" if output else "READ_ONLY",
        [],
        result="FAIL"
        if isinstance(details.get("verification"), dict)
        and details["verification"].get("exit_code", 0)
        else "PASS",
        artifacts=[{"path": str(output), "sha256": value["output_sha256"]}] if output else [],
        transformation=value,
        warnings=["Offline artifact evidence only; device compatibility and bootability UNTESTED"],
    )
