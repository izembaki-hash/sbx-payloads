"""Craft bl_sbx payloads for a specific device.

Inputs (already present in this directory):
  downloads.28.sqlitedb     upstream crafted itunesstored download DB
  BLDatabaseManager.sqlite  upstream crafted bookassetd download DB

Outputs:
  crafted-downloads.28.sqlitedb   one row per asset described in the spec
  crafted-BLDatabaseManager.sqlite  bookassetd DB with the traversal target
  manifest.json                   URLs, sha1 sums, and target paths

Usage:
  python craft_sbx.py <spec.json>
"""

from __future__ import annotations

import hashlib
import json
import plistlib
import shutil
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
UPSTREAM_DOWNLOADS = BASE / "downloads.28.sqlitedb"
UPSTREAM_BL = BASE / "BLDatabaseManager.sqlite"

GESTALT_CACHE = (
    "/private/var/containers/Shared/SystemGroup/"
    "systemgroup.com.apple.mobilegestaltcache/Library/Caches"
)


def sha1_of(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def flatten(path: Path) -> None:
    """Move a SQLite database out of WAL mode into a single self-contained file."""
    con = sqlite3.connect(path)
    try:
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        con.execute("PRAGMA journal_mode=DELETE")
        con.commit()
    finally:
        con.close()
    for suffix in ("-wal", "-shm"):
        side = path.with_name(path.name + suffix)
        if side.exists():
            side.unlink()


def hash_array(sha1: str | None) -> bytes | None:
    if not sha1:
        return None
    return plistlib.dumps({"6": sha1}, fmt=plistlib.FMT_BINARY)


def build_downloads(spec: dict, out: Path) -> None:
    shutil.copyfile(UPSTREAM_DOWNLOADS, out)
    flatten(out)
    con = sqlite3.connect(out)
    cur = con.cursor()
    for asset in spec["assets"]:
        cur.execute(
            "UPDATE asset SET url=?, local_path=?, hash_array=?, path_extension=? WHERE pid=?",
            (
                asset["url"],
                asset["local_path"],
                hash_array(asset.get("sha1")),
                asset.get("path_extension", "epub"),
                asset["pid"],
            ),
        )
    con.commit()
    con.close()


def build_bl(spec: dict, out: Path) -> None:
    shutil.copyfile(UPSTREAM_BL, out)
    flatten(out)
    bl = spec.get("bl", {})
    con = sqlite3.connect(out)
    cur = con.cursor()
    updates = []
    values = []
    for column, value in bl.items():
        updates.append(f"{column}=?")
        values.append(value)
    if updates:
        cur.execute(
            f"UPDATE ZBLDOWNLOADINFO SET {', '.join(updates)} WHERE Z_PK=1", values
        )
        con.commit()
    con.close()


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    downloads_out = BASE / "crafted-downloads.28.sqlitedb"
    bl_out = BASE / "crafted-BLDatabaseManager.sqlite"

    build_downloads(spec, downloads_out)
    build_bl(spec, bl_out)

    manifest = {
        "downloads": {
            "file": str(downloads_out),
            "sha1": sha1_of(downloads_out.read_bytes()),
            "size": downloads_out.stat().st_size,
        },
        "bl": {
            "file": str(bl_out),
            "sha1": sha1_of(bl_out.read_bytes()),
            "size": bl_out.stat().st_size,
        },
        "assets": spec["assets"],
        "bl_overrides": spec.get("bl", {}),
    }
    (BASE / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
