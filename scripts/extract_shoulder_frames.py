import subprocess
from pathlib import Path

out_dir = Path("renders/vfx_validation_tests/shoulder_frames")
out_dir.mkdir(parents=True, exist_ok=True)
shoulder = Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_02_shoulder_approach.mp4")

for t in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]:
    out_img = out_dir / f"shoulder_{t:04.1f}s.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{t:.2f}",
        "-i", str(shoulder),
        "-frames:v", "1",
        "-q:v", "2",
        str(out_img)
    ], capture_output=True)

print("Shoulder frames extracted.")
