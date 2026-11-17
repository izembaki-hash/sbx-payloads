"""Read an iOS IPSW over HTTP range requests.

Only the ZIP central directory is fetched first, so the member list and sizes
are known without downloading the multi-gigabyte firmware image.
"""

from __future__ import annotations

import io
import json
import sys
import urllib.request
import zipfile


class HttpRangeFile(io.RawIOBase):
    """Minimal seekable read-only file object backed by HTTP Range requests."""

    def __init__(self, url: str, block: int = 1 << 20) -> None:
        self.url = url
        self.block = block
        self.pos = 0
        self.size = self._content_length()
        self._buf = b""
        self._buf_pos = 0

    def _request(self, start: int, end: int) -> bytes:
        request = urllib.request.Request(self.url)
        request.add_header("Range", f"bytes={start}-{end}")
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.read()

    def _content_length(self) -> int:
        request = urllib.request.Request(self.url, method="HEAD")
        with urllib.request.urlopen(request, timeout=60) as response:
            return int(response.headers["Content-Length"])

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        elif whence == io.SEEK_END:
            self.pos = self.size + offset
        return self.pos

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = self.size - self.pos
        if size == 0 or self.pos >= self.size:
            return b""
        end = min(self.pos + size, self.size)
        chunk = self._request(self.pos, end - 1)
        self.pos = end
        return chunk


def ipsw_url(product: str, build: str) -> str:
    query = f"https://api.ipsw.me/v4/device/{product}?type=ipsw"
    with urllib.request.urlopen(query, timeout=60) as response:
        payload = json.load(response)
    entries = []
    if isinstance(payload, dict):
        entries = payload.get("firmwares", payload.get("releases", []))
    else:
        entries = payload
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        candidates = entry.get("ipsw", [entry])
        for ipsw in candidates:
            if ipsw.get("buildid") == build:
                return ipsw["url"]
    available = sorted(
        {entry.get("buildid") for entry in entries if isinstance(entry, dict)}
    )
    raise SystemExit(f"no IPSW for {product} build {build}; available: {available}")


def main() -> int:
    product = sys.argv[1] if len(sys.argv) > 1 else "iPhone12,1"
    build = sys.argv[2] if len(sys.argv) > 2 else "22G84"
    url = ipsw_url(product, build)
    print(f"ipsw: {url}")
    handle = HttpRangeFile(url)
    print(f"size: {handle.size}")
    with zipfile.ZipFile(handle) as archive:
        for info in archive.infolist():
            print(f"{info.file_size:12d} {info.compress_size:12d} {info.filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
