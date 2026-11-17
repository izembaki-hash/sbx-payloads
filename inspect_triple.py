import sqlite3, hashlib, os, shutil, tempfile

for tag, base in (('UPSTREAM', 'up_'), ('LOCAL', '')):
    d = base + 'BLDatabaseManager.sqlite'
    if not os.path.exists(d):
        print(tag, 'missing', d); continue
    raw = open(d, 'rb').read()
    print(f'=== {tag} {d} size={len(raw)} sha1={hashlib.sha1(raw).hexdigest()}')
    print('  header magic:', raw[:16])
    print('  page_size:', int.from_bytes(raw[16:18], "big"), 'write_ver:', raw[18], 'read_ver:', raw[19],
          'reserved:', raw[20], 'change_counter:', int.from_bytes(raw[24:28], "big"),
          'db_size_pages:', int.from_bytes(raw[28:32], "big"), 'schema_cookie:', int.from_bytes(raw[40:44], "big"))
    print('  file_change_counter:', int.from_bytes(raw[24:28], "big"), 'version_valid_for:', int.from_bytes(raw[92:96], "big"))
    for ext in ('-wal', '-shm'):
        p = base + 'BLDatabaseManager.sqlite' + ext
        if os.path.exists(p):
            r = open(p, 'rb').read()
            print(f'  {ext}: size={len(r)} sha1={hashlib.sha1(r).hexdigest()} nonzero={sum(1 for b in r if b)}')
            if ext == '-wal' and len(r) >= 32:
                print('    wal magic:', r[:4].hex(), 'fmtver:', int.from_bytes(r[4:8], 'big'),
                      'pgsz:', int.from_bytes(r[8:12], 'big'), 'ckpt_seq:', int.from_bytes(r[12:16], 'big'),
                      'salt1:', r[16:20].hex(), 'salt2:', r[20:24].hex())
        else:
            print(f'  {ext}: ABSENT')

# does the row live in the WAL?  copy main only to temp and query
print('\n=== row visibility with main-only vs main+wal ===')
for tag, base in (('UPSTREAM', 'up_'), ('LOCAL', '')):
    d = base + 'BLDatabaseManager.sqlite'
    if not os.path.exists(d):
        continue
    tmp = tempfile.mkdtemp()
    main = os.path.join(tmp, 'BLDatabaseManager.sqlite')
    shutil.copyfile(d, main)
    con = sqlite3.connect('file:' + main + '?mode=ro', uri=True)
    try:
        n = con.execute('select count(*) from ZBLDOWNLOADINFO').fetchone()[0]
        row = con.execute('select ZPLISTPATH,ZDOWNLOADID,ZURL from ZBLDOWNLOADINFO').fetchall()
        print(f'  {tag} main-only: rows={n} {row}')
    except Exception as e:
        print(f'  {tag} main-only ERROR: {e}')
    con.close()
    shutil.rmtree(tmp, ignore_errors=True)

# compare local downloads.28 vs upstream
print('\n=== downloads.28 compare ===')
for p in ('up_downloads.28.sqlitedb', 'downloads.28.sqlitedb'):
    if os.path.exists(p):
        raw = open(p, 'rb').read()
        print(p, len(raw), hashlib.sha1(raw).hexdigest())

def dump(p, label):
    if not os.path.exists(p):
        return
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    print(f'-- {label} ({p})')
    for r in con.execute('SELECT pid,download_id,url,local_path,download_token,hash_array,url_session_task_id FROM asset'):
        print('   ', {k: (r[k] if k != 'hash_array' else (r[k].hex() if r[k] else None)) for k in r.keys()})
    con.close()

dump('up_downloads.28.sqlitedb', 'UPSTREAM downloads.28')
dump('downloads.28.sqlitedb', 'LOCAL downloads.28')
dump('crafted-downloads.28.sqlitedb', 'CRAFTED downloads.28')
