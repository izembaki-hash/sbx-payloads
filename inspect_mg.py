import zipfile, plistlib, re, os, sys, binascii

EPUB = 'gestalt.epub'
with zipfile.ZipFile(EPUB) as z:
    names = z.namelist()
    print('epub entries:', names)
    data = None
    for n in names:
        if n.endswith('com.apple.MobileGestalt.plist'):
            data = z.read(n)
    if data is None:
        for n in names:
            if n.endswith('.plist'):
                data = z.read(n)
    print('plist size:', len(data))

p = plistlib.loads(data)
print('top keys:', sorted(p.keys()))
for k, v in p.items():
    if k == 'CacheData':
        print(f'CacheData: {type(v).__name__} len={len(v)}')
    elif isinstance(v, dict):
        print(f'{k}: dict[{len(v)}]')
        for kk, vv in list(v.items())[:12]:
            print('    ', repr(kk), '=', repr(vv)[:120])
        if len(v) > 12:
            print('     ...')
    else:
        print(f'{k}: {type(v).__name__} = {repr(v)[:200]}')

cd = p.get('CacheData')
if isinstance(cd, bytes):
    print('\n--- CacheData first 256 bytes ---')
    print(binascii.hexlify(cd[:256]).decode())
    # look for ascii strings
    strs = re.findall(rb'[ -~]{4,}', cd)
    print('\n--- ascii strings in CacheData (%d) ---' % len(strs))
    for s in strs[:60]:
        print('   ', s.decode('ascii', 'replace'))
    # locate the sentinel
    pat = b'\xff\xff\xff\xff\x00\x00\x00\x00'
    idx = []
    start = 0
    while True:
        i = cd.find(pat, start)
        if i < 0:
            break
        idx.append(i)
        start = i + 1
    print('\nsentinel FFFFFFFF00000000 occurrences:', idx)
    if idx:
        sep = idx[1] if len(idx) > 1 else idx[0]
        print('  int slots before sep:', (sep - 0) // 8, ' (assuming base 0)')
        print('  bytes after sep:', len(cd) - sep - 8)
