import subprocess
from pathlib import Path

out_dir = Path("renders/vfx_validation_tests/v4_cut_verification")
out_dir.mkdir(parents=True, exist_ok=True)

shoulder = Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_02_shoulder_approach.mp4")
hero_pov = Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_01_hero_pov.mp4")
orbit = Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_04_climax_orbit.mp4")

# Verification points:
# 1. Shoulder at 1.0s (running in canal)
# 2. Shoulder at 2.2s (approaching corner)
# 3. Hero POV at 5.20s (entry into POV)
# 4. Hero POV at 5.45s (peeking mid)
# 5. Hero POV at 5.68s (Kill 1 Tiger07 hit)
# 6. Hero POV at 8.30s (Kill 2 zuuuuuhhhhn hit)
# 7. Hero POV at 10.08s (Kill 3 ProfyfGames headshot hit)
# 8. Hero POV at 10.90s (Kill 4 freekjkeee rapid hit)
# 9. Orbit at 1.5s (celebration orbit)

checks = [
    ("01_shoulder_canal", shoulder, 1.0),
    ("02_shoulder_corner", shoulder, 2.2),
    ("03_hero_entry_pov", hero_pov, 5.20),
    ("04_hero_peek_mid", hero_pov, 5.45),
    ("05_hero_k1_tiger07", hero_pov, 5.68),
    ("06_hero_k2_zuuuuuhhhhn", hero_pov, 8.30),
    ("07_hero_k3_profyfgames", hero_pov, 10.08),
    ("08_hero_k4_freekjkeee", hero_pov, 10.90),
    ("09_orbit_celebration", orbit, 1.5),
]

for name, take_p, sec in checks:
    out_img = out_dir / f"{name}_{sec:.2f}s.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{sec:.3f}",
        "-i", str(take_p),
        "-frames:v", "1",
        "-q:v", "2",
        str(out_img)
    ], capture_output=True)

print("V4 cut verification frames extracted to", out_dir)
