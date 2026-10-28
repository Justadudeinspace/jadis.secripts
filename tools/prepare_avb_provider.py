"""Explicit development/CI provision of pinned upstream avbtool source, never a runtime download."""

import argparse
from pathlib import Path
from secripts.images.artifacts import digest, exclusive, canonical
from provider_sources import fetch

REVISION = "761178607206f4cb2af79ed9eec52d8cbd814adb"
SHA256 = "e5a664a38db623da00f080219bc0ee60a640a9dc4a872803616fae4938ac749b"
URL = f"https://android.googlesource.com/platform/external/avb/+/{REVISION}/avbtool.py"
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True, help="New private provider directory")
args = parser.parse_args()
if args.output.exists() or args.output.is_symlink():
    parser.error("Output directory must not exist")
payload, origin = fetch(URL, SHA256)
if digest(payload) != SHA256:
    raise ValueError("Provider hash mismatch; source not installed or executed")
args.output.mkdir(mode=0o700)
target = args.output / "avbtool"
exclusive(target, payload)
target.chmod(0o700)
canonical(
    args.output / "provider.json",
    {
        "schema": 1,
        "source": origin,
        "revision": REVISION,
        "sha256": SHA256,
        "license": "MIT-style source notice retained verbatim in downloaded file",
        "relationship": "Explicit optional test/verification provider; not bundled",
    },
)
print(f"Pinned avbtool source prepared: {target}")
