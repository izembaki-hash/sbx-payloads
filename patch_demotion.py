"""Patch the AP-demotion bit in a MobileGestalt cache plist.

Port of hanakim3945/gestalt_hax_v2 poc.m. The cache blob holds an 8-byte value
table, a FFFFFFFF00000000 separator and a byte-per-key boolean table. The
demotion key ("vENa/R1xAXLobl8r3PBL6w", EffectiveSecurityModeAp) lives in the
boolean table; its index comes from libMobileGestalt's __const entry.

Usage:
  python patch_demotion.py <plist> <index> [--bitmap-base 7|8] [--out FILE]
"""

from __future__ import annotations

import plistlib
import sys
from pathlib import Path

PATTERN = bytes.fromhex("ffffffff00000000")
DEMOTION_KEY = "vENa/R1xAXLobl8r3PBL6w"


def find_pattern(data: bytes) -> list[int]:
    offsets = []
    start = 0
    while True:
        found = data.find(PATTERN, start)
        if found < 0:
            return offsets
        offsets.append(found)
        start = found + 1


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    path = Path(sys.argv[1])
    index = int(sys.argv[2])
    base = 7
    out_path = path
    args = sys.argv[3:]
    while args:
        flag = args.pop(0)
        if flag == "--bitmap-base":
            base = int(args.pop(0))
        elif flag == "--out":
            out_path = Path(args.pop(0))

    plist = plistlib.loads(path.read_bytes())
    data = bytearray(plist["CacheData"])
    offsets = find_pattern(bytes(data))
    print(f"cache: {path}")
    print(f"  CacheVersion: {plist.get('CacheVersion')}")
    print(f"  CacheUUID:    {plist.get('CacheUUID')}")
    print(f"  CacheData:    {len(data)} bytes")
    print(f"  CacheExtra:   {len(plist.get('CacheExtra', {}))} entries")
    print(f"  pattern at:   {offsets}")
    if not offsets:
        print("  no separator found")
        return 2

    separator = offsets[-1]
    bitmap_start = separator + base
    target = bitmap_start + index
    print(f"  bitmap start: {bitmap_start} (separator + {base})")
    print(f"  target byte:  {target} (index {index}) current=0x{data[target]:02x}")
    if target >= len(data):
        print("  target out of range")
        return 2
    if data[target] not in (0x00, 0x01):
        print(f"  warning: target byte is 0x{data[target]:02x}, expected 0x00/0x01")

    data[target] = 0x01
    plist["CacheData"] = bytes(data)
    out_path.write_bytes(plistlib.dumps(plist, fmt=plistlib.FMT_BINARY))
    print(f"  patched -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
