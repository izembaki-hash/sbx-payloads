"""Dump the raw slot layout of a MobileGestalt CacheData blob."""

from __future__ import annotations

import plistlib
import struct
import sys
import zipfile
from pathlib import Path


def load_cache_data(path: Path) -> bytes:
    if path.suffix == ".epub":
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.endswith("com.apple.MobileGestalt.plist"):
                    return plistlib.loads(archive.read(name))["CacheData"]
    return plistlib.loads(path.read_bytes())["CacheData"]


def main() -> int:
    data = load_cache_data(Path(sys.argv[1]))
    print(f"size={len(data)} ({len(data) / 8:.3f} slots)")
    ranges = [(0, 24), (128, 152), (676, 700), (744, len(data) // 8)]
    for start, end in ranges:
        print(f"--- slots {start}..{end}")
        for index in range(start, min(end, len(data) // 8)):
            chunk = data[index * 8 : index * 8 + 8]
            value = struct.unpack("<Q", chunk)[0]
            as_double = struct.unpack("<d", chunk)[0]
            print(
                f"  slot {index:4d} off {index * 8:6d}  {chunk.hex(' ')}"
                f"  u64={value:<22d} d={as_double:<14g}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
