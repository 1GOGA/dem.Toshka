import subprocess
import pathlib
from PIL import Image

OUT_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX")
MASTER = OUT_DIR / "ACE_FINAL_V2_MASTER.mp4"
HERO_TAKE = pathlib.Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_01_hero_pov.mp4")
VICTIM_TAKE = pathlib.Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_03_victim_reaction.mp4")

DEBUG_DIR = pathlib.Path("renders/ACE_FINAL_V3_AUDIO_KILLFEED/timing_debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

# 1. Let's analyze Hero Take frame-by-frame around the 5 kill ticks
# start_tick = 120200
kills = [
    (1, 120927, "Tiger07"),
    (2, 121263, "zuuuuuhhhhn"),
    (3, 121491, "ProfyfGames"),
    (4, 121595, "freekjkeee"),
    (5, 121920, "axuenchik002")
]

print("=== Hero Take Kill Timings from Demo Ticks ===")
for k_num, tick, victim in kills:
    t_sec = (tick - 120200) / 128.0
    f_num = round(t_sec * 60.0)
    print(f"Kill #{k_num} ({victim}): tick {tick} -> {t_sec:.4f}s (Frame {f_num} in hero take)")
    
    # Extract 3 frames: t - 0.25s, t, t + 0.25s
    for dt, suffix in [(-0.3, "before"), (0.0, "hit"), (+0.3, "after")]:
        f_time = max(0.0, t_sec + dt)
        out_f = DEBUG_DIR / f"hero_take_k{k_num}_{suffix}_{f_time:.3f}s.png"
        cmd = ["ffmpeg", "-y", "-ss", f"{f_time:.3f}", "-i", str(HERO_TAKE), "-frames:v", "1", "-q:v", "2", str(out_f)]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print("\nHero take frames extracted to", DEBUG_DIR)
