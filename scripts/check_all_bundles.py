import urllib.request

urls = [
    "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle1of5.zip",
    "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle2of5.zip",
    "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle3of5.zip",
    "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle4of5.zip",
    "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle5of5.zip",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://gdc.sonniss.com/',
    'Range': 'bytes=0-10'
}

total_size = 0
for u in urls:
    req = urllib.request.Request(u, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            cr = resp.headers.get("Content-Range")
            # e.g. bytes 0-10/1301592146
            total_b = int(cr.split('/')[-1])
            total_size += total_b
            print(f"{u.split('/')[-1]}: {total_b / (1024*1024):.2f} MB ({total_b} bytes)")
    except Exception as e:
        print(f"Error {u}: {e}")

print(f"\nTotal 5 bundles size: {total_size / (1024*1024*1024):.2f} GB")
