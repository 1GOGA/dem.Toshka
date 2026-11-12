import subprocess
from pathlib import Path

out_dir = Path("renders/vfx_validation_tests/kill_sync_verification")
out_dir.mkdir(parents=True, exist_ok=True)
hero_pov = Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_01_hero_pov.mp4")

# Kill exact times in hero_pov:
# K1: 5.68s
# K2: 8.30s
# K3: 10.08s
# K4: 10.90s
# K5: 13.44s

tests = [
    (1, "Tiger07", 5.68),
    (2, "zuuuuuhhhhn", 8.30),
    (3, "ProfyfGames", 10.08),
    (4, "freekjkeee", 10.90),
    (5, "axuenchik002", 13.44),
]

for k_id, victim, t in tests:
    for dt, label in [(-0.10, "peek_aim"), (0.00, "muzzle_hit"), (+0.15, "victim_death")]:
        f_time = t + dt
        out_img = out_dir / f"k{k_id}_{victim}_{label}_{f_time:.2f}s.jpg"
        subprocess.run([
            "ffmpeg", "-y", "-ss", f"{f_time:.3f}",
            "-i", str(hero_pov),
            "-frames:v", "1",
            "-q:v", "2",
            str(out_img)
        ], capture_output=True)

print("Extracted kill sync frames successfully.")
