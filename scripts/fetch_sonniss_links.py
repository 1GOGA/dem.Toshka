import urllib.request
import re

url = "https://sonniss.com/gameaudiogdc"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"Fetched {len(html)} bytes from {url}")
        
        # Look for links to zip, rar, torrent, drive, mega, etc.
        links = set(re.findall(r'href=["\'](https?://[^"\']+)["\']', html))
        for l in sorted(links):
            if any(k in l.lower() for k in ['2026', 'gdc', 'download', 'torrent', 'archive', 'drive.google', 'mega.nz', 'we.tl']):
                print("Candidate Link:", l)
except Exception as e:
    print("Fetch error:", e)
