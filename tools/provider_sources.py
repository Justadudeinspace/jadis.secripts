"""Bounded official-source retrieval for explicit development/CI jobs; exact hash always required."""

import base64
import hashlib
import urllib.error
import urllib.request
from urllib.parse import urlparse


def fetch(url, expected):
    if urlparse(url).scheme != "https" or urlparse(url).hostname != "android.googlesource.com":
        raise ValueError("Provider source origin refused")
    attempts = [url]
    parts = url.split("/+/")
    if len(parts) == 2 and "/" in parts[1]:
        _, relative = parts[1].split("/", 1)
        attempts.append(parts[0] + "/+/refs/heads/main/" + relative)
    last = None
    for source in attempts:
        try:
            with urllib.request.urlopen(source + "?format=TEXT", timeout=20) as response:  # noqa: S310 -- exact official HTTPS host validated above; content hash mandatory
                encoded = response.read(2 * 1024**2 + 1)
            if len(encoded) > 2 * 1024**2:
                raise ValueError("Provider byte cap")
            payload = base64.b64decode(encoded, validate=True)
            if hashlib.sha256(payload).hexdigest() != expected:
                raise ValueError("Provider source hash mismatch; never executed")
            return payload, source
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
    raise ValueError("Official provider source unavailable: " + str(last))
