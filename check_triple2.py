import sqlite3, shutil, os, tempfile, hashlib, binascii

os.chdir(r'E:\bypass\work\sbx')

def probe(files, label):
    tmp = tempfile.mkdtemp()
    main = os.path.join(tmp, 'BLDatabaseManager.sqlite')
    shutil.copyfile(files['main'], main)
    for ext, src in files.items():
        if ext == 'main':
            continue
        shutil.copyfile(src, main + ext)
    con = sqlite3.connect('file:' + main + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in con.execute('SELECT Z_PK,ZPLISTPATH,ZDOWNLOADID,ZASSETPATH,ZTITLE,ZURL,ZSTATE FROM ZBLDOWNLOADINFO')]
        print(f'--- {label}: {len(rows)} rows')
        for r in rows:
            print('   ', {k: (v if k != 'ZFILEATTRIBUTES' else '...') for k, v in r.items()})
    except Exception as e:
        print(f'--- {label}: ERROR {e}')
    con.close()
    shutil.rmtree(tmp, ignore_errors=True)

# main only
probe({'main': 'up_BLDatabaseManager.sqlite'}, 'main only')
# main + upstream wal/shm
probe({'main': 'up_BLDatabaseManager.sqlite',
       '-wal': 'served_BLDatabaseManager.sqlite-wal',
       '-shm': 'served_BLDatabaseManager.sqlite-shm'}, 'main + upstream wal/shm')

print('\n=== wal header of upstream served -wal ===')
w = open('served_BLDatabaseManager.sqlite-wal', 'rb').read()
print('len', len(w))
print('magic', w[:4].hex(), 'fmt', int.from_bytes(w[4:8], 'big'), 'pgsz', int.from_bytes(w[8:12], 'big'),
      'ckpt', int.from_bytes(w[12:16], 'big'), 'salt1', w[16:20].hex(), 'salt2', w[20:24].hex())
print('frames:', (len(w) - 32) // (4096 + 24))

print('\n=== downloads.28 header ===')
d = open('up_downloads.28.sqlitedb', 'rb').read()
print('size', len(d), 'write_ver', d[18], 'read_ver', d[19], 'page_size', int.from_bytes(d[16:18], 'big'))

print('\n=== upstream downloads.28: download rows for our ids ===')
con = sqlite3.connect('file:up_downloads.28.sqlitedb?mode=ro', uri=True)
con.row_factory = sqlite3.Row
cols = [r[1] for r in con.execute('PRAGMA table_info(download)')]
for r in con.execute('SELECT * FROM download WHERE pid IN (6936249076851270150,6936249076851270151,6936249076851270152)'):
    d = dict(r)
    keep = {k: d[k] for k in ('pid','kind','state','title','store_transaction_id','transaction_id','download_permalink',
                              'client_id','effective_client_id','collection_name','document_target_id','unique_asset_id',
                              'episode_id','asset_flavor','file_size','total_bytes','purchased_date','pre_order_date')}
    print({k: (str(v)[:90] if v is not None else None) for k, v in keep.items() if k in d})
con.close()

print('\n=== tables in downloads.28 ===')
con = sqlite3.connect('file:up_downloads.28.sqlitedb?mode=ro', uri=True)
print([r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")])
con.close()
