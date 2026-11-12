import urllib.request

urls = [
    "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle1of5.zip",
    "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle2of5.zip",
    "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle3of5.zip",
    "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle4of5.zip",
    "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle5of5.zip",
]

headers = {'User-Agent': 'Mozilla/5.0'}

for u in urls:
    req = urllib.request.Request(u, headers=headers, method='HEAD')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            length = int(resp.headers.get('Content-Length', 0))
            print(f"{u.split('/')[-1]}: {length / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"Error checking {u}: {e}")
