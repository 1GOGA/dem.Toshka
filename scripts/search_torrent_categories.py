import pathlib
from inspect_torrent import bdecode_val

torrent_path = pathlib.Path("GameAudioGDCPart9.torrent")
data = torrent_path.read_bytes()
torrent, _ = bdecode_val(data, 0)
info = torrent.get('info', {})
files = info.get('files', [])

categories = {
    "1_CINEMATIC_IMPACTS": ["impact", "hit", "slam", "strike", "smash", "punch", "drop", "bass", "thud"],
    "2_WHOOSHES": ["whoosh", "swish", "air", "flyby", "pass"],
    "3_TRANSITIONS": ["transition", "sweep", "whip", "reverse"],
    "4_RISERS": ["riser", "rise", "swell", "build", "tension"],
    "5_GLITCH_DIGITAL": ["glitch", "digital", "ui", "beep", "tech", "static", "cyber"],
    "6_ATMOSPHERIC": ["ambience", "ambient", "drone", "atmosphere", "texture", "room"],
    "7_GAMEPLAY_ACCENTS": ["accent", "metal", "click", "foley", "weapon", "bullet", "crack"]
}

categorized = {k: [] for k in categories}
uncategorized = []

total_bytes = 0
for f in files:
    length = f.get('length', 0)
    total_bytes += length
    path_list = f.get('path', [])
    full_path = "/".join(path_list)
    fn_lower = full_path.lower()
    
    matched = False
    for cat, kws in categories.items():
        if any(kw in fn_lower for kw in kws):
            categorized[cat].append((full_path, length))
            matched = True
            break
    if not matched:
        uncategorized.append((full_path, length))

print(f"Total files: {len(files)}, Total uncompressed size: {total_bytes / (1024*1024*1024):.2f} GB")
for cat, flist in categorized.items():
    print(f"\n--- {cat} ({len(flist)} files) ---")
    for p, sz in flist[:5]:
        print(f"  {p} ({sz / (1024*1024):.2f} MB)")
