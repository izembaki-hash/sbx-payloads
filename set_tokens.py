"""Set the AMS download token on every asset row of the crafted database."""

from __future__ import annotations

import sqlite3
import sys

path = sys.argv[1]
token = int(sys.argv[2]) if len(sys.argv) > 2 else 466440000
con = sqlite3.connect(path)
cur = con.execute("update asset set download_token = ?", (token,))
con.commit()
print(f"updated {cur.rowcount} asset rows with download_token={token}")
for row in con.execute("select pid, download_id, download_token, url from asset order by pid"):
    print(f"  pid={row[0]} download_id={row[1]} token={row[2]} url={row[3]}")
con.close()
