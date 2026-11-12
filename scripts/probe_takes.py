import json
import subprocess
from pathlib import Path

takes = [
    'shot_anubis_ace_r19_01_hero_pov.mp4',
    'shot_anubis_ace_r19_02_shoulder_approach.mp4',
    'shot_anubis_ace_r19_03_victim_reaction.mp4',
    'shot_anubis_ace_r19_04_climax_orbit.mp4'
]

for name in takes:
    p = Path('renders/cinematic_studio_phase3/takes') / name
    res = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', str(p)
    ], capture_output=True, text=True)
    d = json.loads(res.stdout)
    dur = float(d['format']['duration'])
    v = [s for s in d['streams'] if s['codec_type'] == 'video'][0]
    print(f"{name}: dur={dur:.2f}s, {v['width']}x{v['height']}, fps={v['r_frame_rate']}")
