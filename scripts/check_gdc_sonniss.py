import urllib.request
import re

req = urllib.request.Request(
    'https://gdc.sonniss.com/',
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"Fetched {len(html)} bytes")
        links = re.findall(r'href=["\']([^"\']+)["\']', html)
        for l in set(links):
            if any(k in l.lower() for k in ['bundle', 'download', 'part', 'torrent', 'zip', 'gdc', 'license']):
                print("Found:", l)
except Exception as e:
    print("Err:", e)
