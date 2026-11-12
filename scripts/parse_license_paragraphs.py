import urllib.request
import re

url = "https://sonniss.com/gdc-bundle-license/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://gdc.sonniss.com/'
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# print sections with words "Grant", "Commercial", "Royalty", "Permitted", "Prohibited"
for p in re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL):
    clean = re.sub(r'<[^>]+>', ' ', p).strip()
    if any(k in clean.lower() for k in ['license', 'royalty', 'commercial', 'prohibit', 'distribute', 'ai', 'bundle']):
        print("-", clean[:300])
