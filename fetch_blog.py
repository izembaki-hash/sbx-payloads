import urllib.request, re, html

u = 'https://hanakim3945.github.io/posts/download28_sbx_escape/'
req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
h = urllib.request.urlopen(req, timeout=60).read().decode('utf8', 'replace')
h = re.sub(r'<script[\s\S]*?</script>', '', h)
h = re.sub(r'<style[\s\S]*?</style>', '', h)
h = re.sub(r'<(br|/p|/div|/li|/h\d)[^>]*>', '\n', h)
h = re.sub(r'<[^>]+>', '', h)
h = html.unescape(h)
lines = [l.strip() for l in h.split('\n')]
out = '\n'.join(l for l in lines if l)
open('blog_post.txt', 'w', encoding='utf8').write(out)
print('LEN', len(out))
print(out[:12000])
