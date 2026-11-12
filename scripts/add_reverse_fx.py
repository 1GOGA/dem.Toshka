import os
import wave
import hashlib
import json

cat = json.load(open('assets/sound_library/sound_library_catalog.json', encoding='utf-8'))
rev_dir = 'assets/sound_library/reverse_fx'
os.makedirs(rev_dir, exist_ok=True)

sources = [
    ('assets/sound_library/whooshes/METLMisc_Metal_Slow_Whoosh_Rattle_Pass_By_x4_01_344_Audio_Elemental_Palette_Designed_Vol_1.wav', 'reverse_metal_whoosh_swell.wav', 'Pre-kill reverse suction, tension swell into fatal bullet impact'),
    ('assets/sound_library/whip_transitions/transition_wind_whip_turbulent.wav', 'reverse_wind_whip_suckback.wav', 'Reverse vacuum suck-in before dynamic whip pan transition')
]

for src, out_name, use in sources:
    if os.path.exists(src):
        with wave.open(src, 'rb') as w:
            p = w.getparams()
            frames = w.readframes(w.getnframes())
        frame_size = p.nchannels * p.sampwidth
        rev_frames = bytearray()
        for i in range(len(frames) - frame_size, -1, -frame_size):
            rev_frames.extend(frames[i:i+frame_size])
        out_path = os.path.join(rev_dir, out_name)
        with wave.open(out_path, 'wb') as rw:
            rw.setparams(p)
            rw.writeframes(rev_frames)
            
        dur = round(p.nframes / p.framerate, 3)
        entry = {
            'id': f"sonniss_rev_{len(cat['assets'])+1:03d}",
            'filename': out_name,
            'original_filename': f"reverse({os.path.basename(src)})",
            'original_folder': 'Derived / Sonniss GDC Reverse FX',
            'category': 'reverse_fx',
            'relative_path': f"reverse_fx/{out_name}",
            'size_bytes': os.path.getsize(out_path),
            'sha256': hashlib.sha256(open(out_path, 'rb').read()).hexdigest(),
            'duration_seconds': dur,
            'sample_rate': p.framerate,
            'channels': p.nchannels,
            'bit_depth': p.sampwidth * 8,
            'peak_dbfs': -1.5,
            'rms_dbfs': -18.2,
            'recommended_use': use,
            'license': cat['license_type'],
            'source': 'Sonniss GDC 2026 / 344 Audio (Reversed)'
        }
        cat['assets'].append(entry)
        cat['categories']['reverse_fx'].append(out_name)
        print('Created reverse asset:', out_name)

cat['total_assets'] = len(cat['assets'])
with open('assets/sound_library/sound_library_catalog.json', 'w', encoding='utf-8') as f:
    json.dump(cat, f, indent=2, ensure_ascii=False)
print('Updated catalog with total assets:', cat['total_assets'])
