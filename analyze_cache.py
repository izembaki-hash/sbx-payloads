"""Analyse the structure of a MobileGestalt cache plist (CacheData / CacheExtra).

Usage: python analyze_cache.py <plist> [<plist> ...]
"""

from __future__ import annotations

import plistlib
import sys
import zipfile
from pathlib import Path

PATTERN = bytes.fromhex("ffffffff00000000")


def load_plist(path: Path) -> dict:
    if path.suffix == ".epub":
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.endswith("com.apple.MobileGestalt.plist"):
                    return plistlib.loads(archive.read(name))
    return plistlib.loads(path.read_bytes())


def main() -> int:
    for argument in sys.argv[1:]:
        path = Path(argument)
        plist = load_plist(path)
        print(f"########## {path}")
        print("keys:", sorted(plist.keys()))
        data = plist["CacheData"]
        print(f"CacheData: {len(data)} bytes = {len(data) / 8:.2f} slots")
        version = plist.get("CacheVersion")
        print("CacheVersion:", version)
        print("CacheUUID:", plist.get("CacheUUID"))
        extra = plist.get("CacheExtra", {})
        print(f"CacheExtra: {len(extra)} entries")
        for key, value in extra.items():
            print(f"   {key} = {value!r}")

        offsets = []
        start = 0
        while True:
            found = data.find(PATTERN, start)
            if found < 0:
                break
            offsets.append(found)
            start = found + 1
        print("pattern FFFFFFFF00000000 at:", offsets)

        slots = [int.from_bytes(data[i : i + 8], "little") for i in range(0, len(data) - 7, 8)]
        nonzero = [i for i, value in enumerate(slots) if value]
        print(f"slots: {len(slots)}, nonzero: {len(nonzero)}")
        print("first nonzero slots:", [(i, slots[i]) for i in nonzero[:25]])
        print("last nonzero slots:", [(i, slots[i]) for i in nonzero[-25:]])
        # value histogram of the leading bytes
        histogram: dict[int, int] = {}
        for value in slots:
            byte = value & 0xFF
            histogram[byte] = histogram.get(byte, 0) + 1
        print("low-byte histogram:", dict(sorted(histogram.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
