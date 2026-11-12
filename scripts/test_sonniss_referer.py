import urllib.request

url = "https://downloads.sonniss.com/GameAudioGDCPart9.torrent"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://gdc.sonniss.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        content = resp.read()
        print(f"Success! Fetched {len(content)} bytes for torrent file.")
except Exception as e:
    print(f"Error: {e}")
