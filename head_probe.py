"""Probe candidate file hosts for HEAD responses with a usable Content-Length."""

from __future__ import annotations

import sys
import urllib.request

url = sys.argv[1]
request = urllib.request.Request(url, method="HEAD")
request.add_header("User-Agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X)")
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        length = response.headers.get("Content-Length")
        print(f"status={response.status} length={length} type={response.headers.get('Content-Type')}")
except Exception as exc:  # noqa: BLE001
    print(f"HEAD failed: {exc}")

request = urllib.request.Request(url)
request.add_header("User-Agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X)")
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        print(f"GET status={response.status} bytes={len(body)} length={response.headers.get('Content-Length')}")
except Exception as exc:  # noqa: BLE001
    print(f"GET failed: {exc}")
