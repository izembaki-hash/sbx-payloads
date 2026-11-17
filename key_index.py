"""Locate MobileGestalt keys inside the upstream obfuscated-key table.

The table in poc2.m was produced by walking libMobileGestalt's __cstring in
order, so the position of a key in the table is the value index used by the
cache blob (offset = index * 8).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "poc2.m"

PATTERN = re.compile(r'"([A-Za-z0-9+/=]{8,30})"\s*,\s*"([^"]*)"')


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8", errors="replace")
    start = text.find("obfuscated_keys")
    end = text.find("};", start)
    block = text[start:end]
    pairs = PATTERN.findall(block)
    print(f"table entries: {len(pairs)}")
    wanted = [
        "EffectiveSecurityModeAp",
        "EffectiveProductionStatusAp",
        "CertificateProductionStatus",
        "CertificateSecurityMode",
        "EffectiveSecurityModeSEP",
        "ShouldHactivate",
        "DeviceClass",
        "ProductType",
        "UniqueDeviceID",
        "SerialNumber",
        "ProductVersion",
        "BuildVersion",
    ]
    index = {name: position for position, (_, name) in enumerate(pairs)}
    for name in wanted:
        position = index.get(name)
        if position is None:
            print(f"  {name}: NOT IN TABLE")
            continue
        print(f"  {name}: index={position} blob_offset={position * 8} (0x{position * 8:x})")
    if len(sys.argv) > 1:
        needle = sys.argv[1]
        for position, (obfuscated, name) in enumerate(pairs):
            if needle in name or needle == obfuscated:
                print(f"  match[{position}] {obfuscated} -> {name} offset={position * 8}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
