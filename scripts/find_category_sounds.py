import json
import pathlib

catalog = json.loads(pathlib.Path("scripts/gdc_bundle_catalog.json").read_text(encoding="utf-8"))

keywords = {
    "cinematic_impacts": ["bass drop", "downer", "impact", "hit", "slam", "strike", "explosion", "firework", "punch"],
    "whooshes": ["whoosh", "blast off", "air", "sweep", "passby", "jet", "swish"],
    "transitions": ["transition", "swell", "whip", "sweeping", "crack"],
    "risers": ["tension", "magic creation", "rise", "swell", "alarm"],
    "glitch_digital": ["glitch", "mechanism", "switch", "dial", "alarm", "counting machine"],
    "atmospheric": ["ambience", "drone", "scare", "evil spell", "camp fire", "industrial"],
    "gameplay_accents": ["lock", "latch", "flick", "click", "handling", "climbing gear", "metal"]
}

matches = {k: [] for k in keywords}

for b_name, b_data in catalog.items():
    for f in b_data["files"]:
        f_lower = f.lower()
        for cat, kws in keywords.items():
            if any(kw in f_lower for kw in kws):
                matches[cat].append((b_name, b_data["url"], b_data["size"], f))

for cat, items in matches.items():
    print(f"\n=== Category: {cat} ({len(items)} found) ===")
    for b_name, url, sz, f in items[:6]:
        print(f"  [{b_name}] {f}")

out_matches = pathlib.Path("scripts/categorized_gdc_matches.json")
out_matches.write_text(json.dumps(matches, indent=2), encoding="utf-8")
print(f"\nSaved matches to {out_matches}")
