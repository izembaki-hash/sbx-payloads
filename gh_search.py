"""Search GitHub code/repositories for published iOS dyld caches or MobileGestalt dylibs."""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

query = sys.argv[1]
kind = sys.argv[2] if len(sys.argv) > 2 else "repositories"
url = f"https://api.github.com/search/{kind}?q={urllib.parse.quote(query)}&per_page=20"
request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
try:
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
except Exception as exc:  # noqa: BLE001
    print(f"search failed: {exc}")
    raise SystemExit(0)
print(f"total: {payload.get('total_count')}")
for item in payload.get("items", []):
    if kind == "repositories":
        print(f"  {item['full_name']}  {item.get('description')}")
    else:
        print(f"  {item['repository']['full_name']}  {item['path']}")
