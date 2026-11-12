import subprocess
from pathlib import Path

# Extract frames every 0.25s from 4.0s to 15.0s of hero_pov
out_dir = Path("renders/vfx_validation_tests/hero_pov_frames")
out_dir.mkdir(parents=True, exist_ok=True)

hero_pov = Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_01_hero_pov.mp4")

# Let's check from 4.5s to 14.5s
for i in range(45, 145, 5):
    t = i / 10.0
    out_img = out_dir / f"frame_{t:04.1f}s.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{t:.2f}",
        "-i", str(hero_pov),
        "-frames:v", "1",
        "-q:v", "2",
        str(out_img)
    ], capture_output=True)

print("Frames 4.5s to 14.0s extracted.")
