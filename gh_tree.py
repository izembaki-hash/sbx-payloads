"""Print a GitHub repository tree (paths, types, sizes)."""

from __future__ import annotations

import json
import sys
import urllib.request

url = sys.argv[1]
if len(sys.argv) > 2:
    url += f"?recursive={sys.argv[2]}"
request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
with urllib.request.urlopen(request, timeout=60) as response:
    payload = json.load(response)
for entry in payload.get("tree", []):
    print(f"{entry['type']:4s} {entry.get('size', 0):9d} {entry['path']}")
