import json
import pathlib
from test_remote_zip import inspect_remote_zip

bundle_urls = [
    ("bundle1", "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle1of5.zip", 1301592146),
    ("bundle2", "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle2of5.zip", 1418237636),
    ("bundle3", "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle3of5.zip", 1490753131),
    ("bundle4", "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle4of5.zip", 1853924113),
    ("bundle5", "https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle5of5.zip", 856448992),
]

catalog = {}
for b_name, url, size in bundle_urls:
    print(f"Scanning {b_name} ({url.split('/')[-1]})...")
    zf, namelist = inspect_remote_zip(url, size)
    wavs = [n for n in namelist if n.lower().endswith('.wav')]
    catalog[b_name] = {
        "url": url,
        "size": size,
        "wav_count": len(wavs),
        "files": wavs
    }

out_p = pathlib.Path("scripts/gdc_bundle_catalog.json")
out_p.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
print(f"Catalog saved to {out_p}. Total bundles: {len(catalog)}")
