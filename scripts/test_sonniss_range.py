import urllib.request

url = "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle1of5.zip"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://gdc.sonniss.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Range': 'bytes=0-1024'  # test range request to see size without full download
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("Status:", resp.status)
        print("Content-Range:", resp.headers.get("Content-Range"))
        print("Content-Length:", resp.headers.get("Content-Length"))
except Exception as e:
    print(f"Error: {e}")
