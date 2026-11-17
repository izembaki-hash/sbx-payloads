import re, zipfile, plistlib, os, binascii

os.chdir(r'E:\bypass\work\sbx')

src = open('poc2.m', 'r', encoding='utf-8', errors='replace').read()

DEMO = ['EffectiveSecurityModeAp', 'EffectiveProductionStatusAp', 'CertificateProductionStatus',
        'CertificateSecurityMode', 'EffectiveSecurityModeSEP']

# mgparser maps obfuscated -> real name. Find entries mentioning our demo keys.
print('=== mgparser (poc2.m) entries for demotion keys ===')
found = {}
for name in DEMO:
    for m in re.finditer(re.escape(name), src):
        s = max(0, m.start() - 160)
        ctx = src[s:m.end() + 80]
        # find the obfuscated literal near this match
        lits = re.findall(r'"([A-Za-z0-9+/=]{22})"', ctx)
        print(f'\n-- {name}')
        print('   literals nearby:', lits[:6])
        print('   ctx:', ' '.join(ctx.split())[-220:])
        found[name] = lits
        break

# Also list the general structure of the key table in poc2.m
print('\n=== structure sniff ===')
for pat in [r'const char\s+\*\s*keys\[\]', r'static const char', r'\{[^{}]*"[A-Za-z0-9+/=]{22}"[^{}]*\}']:
    ms = list(re.finditer(pat, src))
    print(f'pattern {pat!r}: {len(ms)} matches')
    if ms:
        print('   sample:', ' '.join(src[ms[0].start():ms[0].start()+300].split()))

# Check the 26.0.1 sample cache CacheExtra for the demotion obfuscated names
print('\n=== sample (26.0.1 / iPhone13,2) CacheExtra inspection ===')
with zipfile.ZipFile('gestalt.epub') as z:
    for n in z.namelist():
        if n.endswith('com.apple.MobileGestalt.plist'):
            p = plistlib.loads(z.read(n))
extra = p['CacheExtra']
# collect obfuscated literals from poc2.m near each demo key
cands = set()
for name in DEMO:
    for m in re.finditer(re.escape(name), src):
        s = max(0, m.start() - 200)
        for lit in re.findall(r'"([A-Za-z0-9+/=]{22})"', src[s:m.end() + 120]):
            cands.add((name, lit))
print('candidate obfuscated names:', cands)
for name, lit in sorted(cands):
    print(f'  {name} -> {lit}: in CacheExtra? {lit in extra}', extra.get(lit))

print('\n=== all CacheExtra entries whose value is a small int / bytes ===')
for k, v in sorted(extra.items()):
    if isinstance(v, int) or (isinstance(v, bytes) and len(v) <= 32):
        print(f'   {k} = {v!r}')
