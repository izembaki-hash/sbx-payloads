"""Build the Phase-A spec for craft_sbx.py.

Phase A answers four questions in a single device reboot:
  dl150  can itunesstored write straight into an existing app-group Caches dir?
  dl151  can itunesstored write into /var/mobile/Media (AFC visible)?
  dl152  can itunesstored deliver the crafted bookassetd DB into a group container?
  dl153  does the download engine accept file:// URLs (device-local read)?
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

GESTALT_GROUP = (
    "/private/var/containers/Shared/SystemGroup/"
    "systemgroup.com.apple.mobilegestaltcache/Library/Caches"
)
DEVICE_GESTALT = f"{GESTALT_GROUP}/com.apple.MobileGestalt.plist"
UPSTREAM_BOOKS_GROUP = "3DBBBC39-F5BA-4333-B40C-6996DE48F91C"


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


asset_url = (BASE / "asset_url.txt").read_text(encoding="utf-8").strip()
test_url = (BASE / "test_url.txt").read_text(encoding="utf-8").strip()

spec = {
    "assets": [
        {
            "pid": 1234567890,
            "url": test_url,
            "local_path": f"{GESTALT_GROUP}/SBX-DST-A.txt",
            "sha1": sha1(BASE / "sbx-test.txt"),
        },
        {
            "pid": 1234567891,
            "url": test_url,
            "local_path": "/private/var/mobile/Media/SBX-DST-B.txt",
            "sha1": sha1(BASE / "sbx-test.txt"),
        },
        {
            "pid": 1234567892,
            "url": asset_url,
            "local_path": (
                "/private/var/containers/Shared/SystemGroup/"
                f"{UPSTREAM_BOOKS_GROUP}/Documents/BLDatabaseManager/BLDatabaseManager.sqlite"
            ),
            "sha1": None,
        },
        {
            "pid": 1234567893,
            "url": f"file://{DEVICE_GESTALT}",
            "local_path": "/private/var/mobile/Media/SBX-GESTALT-DUMP.plist",
            "sha1": None,
        },
    ],
    "bl": {
        "ZDOWNLOADID": (
            "../../../../../../private/var/mobile/Media/SBX-STAGE2-PROOF.txt"
        ),
        "ZASSETPATH": "/private/var/mobile/Media/Books/SBX-STAGE2-ASSET.epub",
        "ZPLISTPATH": "/var/mobile/Media/SBX-STAGE2-PLIST.plist",
        "ZURL": asset_url,
    },
}

(BASE / "spec-phaseA.json").write_text(
    json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("wrote spec-phaseA.json")
