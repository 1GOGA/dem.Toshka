import urllib.request
import time

url = "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle1of5.zip"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://gdc.sonniss.com/',
    'Range': 'bytes=0-10485760'  # 10 MB test
}

t0 = time.time()
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=20) as resp:
    data = resp.read()
elapsed = time.time() - t0
print(f"Downloaded {len(data) / (1024*1024):.2f} MB in {elapsed:.2f}s ({len(data)/(1024*1024)/elapsed:.2f} MB/s)")
