import os
import subprocess
from pathlib import Path

out_dir = Path("renders/vfx_validation_tests/frame_audit")
out_dir.mkdir(parents=True, exist_ok=True)

hero_pov = Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_01_hero_pov.mp4")

# Extract every 0.5s from 4.0s to 15.0s
for t in range(8, 30):
    sec = t * 0.5
    out_file = out_dir / f"hero_pov_{sec:04.1f}s.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{sec:.2f}",
        "-i", str(hero_pov),
        "-frames:v", "1",
        "-q:v", "2",
        str(out_file)
    ], capture_output=True)

print("Frames extracted to", out_dir)
