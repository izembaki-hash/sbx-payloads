"""Dump the ZBLDOWNLOADINFO rows of candidate BLDatabaseManager.sqlite files."""

from __future__ import annotations

import sqlite3
import sys


def as_text(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            return repr(value[:60])
    return str(value)


for path in sys.argv[1:]:
    print(f"########## {path}")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.text_factory = bytes
    tables = [as_text(r[0]) for r in con.execute("select name from sqlite_master where type='table'")]
    print("tables:", tables)
    for table in tables:
        try:
            cur = con.execute(f'select * from "{table}"')
            cols = [as_text(d[0]) for d in cur.description]
            rows = cur.fetchall()
        except Exception as exc:  # noqa: BLE001
            print(f"  {table}: ERR {exc}")
            continue
        print(f"  -- {table}: {len(rows)} rows")
        for row in rows:
            for col, val in zip(cols, row):
                shown = as_text(val)[:160]
                if shown in ("", "None", "0", "-1"):
                    continue
                print(f"       {col} = {shown}")
            print("       ---")
    con.close()
