"""Scan tracked and untracked repository files; no credential excerpts."""

from pathlib import Path
import subprocess
from secripts.secrets import scan_paths

result = subprocess.run(
    ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
    check=True,
    capture_output=True,
)
paths = [Path(p.decode()) for p in result.stdout.split(b"\0") if p]
findings = scan_paths(paths)
for path in findings:
    print(f"Secret-like pattern: {path}")
print(f"Scanned {len(paths)} repository files; {len(findings)} findings")
raise SystemExit(bool(findings))
