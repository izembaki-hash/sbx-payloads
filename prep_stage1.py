"""Prepare stage-1 payload: upstream pristine downloads.28 with the real bookassetd group UUID."""
import sqlite3, hashlib, plistlib, shutil, os, sys

BOOKS_UUID = '5CD47415-FF2F-4892-90F4-048326510761'
SRC = 'up_downloads.28.sqlitedb'
OUT = 'stage1.downloads.28.sqlitedb'

shutil.copyfile(SRC, OUT)
for ext in ('-wal', '-shm'):
    p = OUT + ext
    if os.path.exists(p):
        os.remove(p)

con = sqlite3.connect(OUT)
cur = con.cursor()

# 1. real bookassetd group container UUID in every local_path
n = cur.execute(
    "UPDATE asset SET local_path = REPLACE(local_path, "
    "'00000000-0000-0000-0000-000000000000', ?) "
    "WHERE local_path LIKE '/private/var/containers/Shared/SystemGroup/%/Documents/BLDatabaseManager/BLDatabaseManager.sqlite%'",
    (BOOKS_UUID,)).rowcount
print('local_path rows updated:', n)

# 2. sha1 of the payload actually served (GitHub raw main branch)
served = {}
for name, fname in (('BLDatabaseManager.sqlite', 'BLDatabaseManager.sqlite'),
                    ('BLDatabaseManager.sqlite-shm', 'BLDatabaseManager.sqlite-shm'),
                    ('BLDatabaseManager.sqlite-wal', 'BLDatabaseManager.sqlite-wal')):
    url = 'https://raw.githubusercontent.com/khanhduytran0/bl_sbx/main/' + fname
    served[name] = url

# download the exact bytes GitHub serves so the hash matches byte-for-byte
import urllib.request
cache = {}
for name, url in served.items():
    req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.0'})
    data = urllib.request.urlopen(req, timeout=60).read()
    cache[name] = data
    print(f'{name}: served size={len(data)} sha1={hashlib.sha1(data).hexdigest()}')

for name, data in cache.items():
    open('served_' + name, 'wb').write(data)

# 3. hash_array must match the bytes we serve, else the install step rejects the asset
for pid, name in ((1234567890, 'BLDatabaseManager.sqlite'),
                  (1234567891, 'BLDatabaseManager.sqlite-shm'),
                  (1234567892, 'BLDatabaseManager.sqlite-wal')):
    sha1 = hashlib.sha1(cache[name]).hexdigest()
    ha = plistlib.dumps({'6': sha1}, fmt=plistlib.FMT_BINARY)
    cur.execute('UPDATE asset SET hash_array = ? WHERE pid = ?', (ha, pid))
    print(f'pid {pid} hash_array <- sha1 {sha1}')

# 4. keep upstream token/task semantics untouched, just report
for r in cur.execute('SELECT pid,download_id,url,local_path,download_token,url_session_task_id FROM asset'):
    print(r)

con.commit()
# fold the WAL back into the main file so the pushed -wal is empty/trivial
print('checkpoint:', cur.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchall())
con.close()

for p in (OUT, OUT + '-wal', OUT + '-shm'):
    if os.path.exists(p):
        print(p, os.path.getsize(p), hashlib.sha1(open(p, 'rb').read()).hexdigest())
