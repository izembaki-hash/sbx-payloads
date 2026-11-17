import sqlite3, hashlib, plistlib, urllib.request, os

UP = 'https://raw.githubusercontent.com/khanhduytran0/bl_sbx/main/'
files = ['BLDatabaseManager.sqlite', 'BLDatabaseManager.sqlite-shm', 'BLDatabaseManager.sqlite-wal',
         'downloads.28.sqlitedb', 'iTunesMetadata.plist', 'empty.txt']

print('--- repo file sha1 ---')
for f in files:
    p = os.path.join('.', 'up_' + f)
    if os.path.exists(p):
        d = open(p, 'rb').read()
        print(f'{f:35s} size={len(d):8d} sha1={hashlib.sha1(d).hexdigest()}')

print('\n--- HEAD checks on raw.githubusercontent (device-visible) ---')
for f in files:
    u = UP + f
    try:
        req = urllib.request.Request(u, method='HEAD', headers={'User-Agent': 'curl/8.0'})
        with urllib.request.urlopen(req, timeout=40) as r:
            print(f'{f:35s} status={r.status} len={r.headers.get("Content-Length")} type={r.headers.get("Content-Type")}')
    except Exception as e:
        print(f'{f:35s} ERR {e}')

print('\n--- upstream downloads.28 asset rows ---')
con = sqlite3.connect('up_downloads.28.sqlitedb')
con.row_factory = sqlite3.Row
cols = [r[1] for r in con.execute('PRAGMA table_info(asset)')]
print('asset cols:', cols)
for r in con.execute('SELECT * FROM asset'):
    d = dict(r)
    keep = {k: d[k] for k in ('pid','download_id','asset_order','asset_type','url','local_path','download_token',
                              'hash_array','url_session_task_id','bytes_total','is_external','http_method','path_extension')}
    print(keep)

print('\n--- upstream downloads.28 download rows (for our download_ids) ---')
dcols = [r[1] for r in con.execute('PRAGMA table_info(download)')]
print('download cols:', dcols)
for r in con.execute('SELECT * FROM download LIMIT 6'):
    print(dict(r))
con.close()

print('\n--- upstream iTunesMetadata.plist ---')
print(plistlib.loads(open('up_iTunesMetadata.plist','rb').read()))
