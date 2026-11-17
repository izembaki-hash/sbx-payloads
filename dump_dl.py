import sqlite3, json, os
os.chdir(r'E:\bypass\work\sbx')

con = sqlite3.connect('file:up_downloads.28.sqlitedb?mode=ro', uri=True)
con.row_factory = sqlite3.Row
cols = [r[1] for r in con.execute('PRAGMA table_info(download)')]
print('download columns:', cols)

for pid in (6936249076851270150, 6936249076851270151, 6936249076851270152):
    rows = con.execute('SELECT * FROM download WHERE pid = ?', (pid,)).fetchall()
    print(f'\n=== download pid={pid}: {len(rows)} rows ===')
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if v is None:
                continue
            s = str(v)
            if len(s) > 100:
                s = s[:100] + f'...({len(s)})'
            print(f'   {k} = {s}')
        break
con.close()
