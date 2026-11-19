import subprocess
from pathlib import Path

out_dir = Path("renders/ACE_FINAL_V4_MASTER_CUT/audio_clean")
out_dir.mkdir(parents=True, exist_ok=True)

hero_pov = Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_01_hero_pov.mp4")

# Extract M4A1 burst (from 5.60s to 6.10s, 0.5s duration)
subprocess.run([
    "ffmpeg", "-y", "-ss", "5.60", "-t", "0.55",
    "-i", str(hero_pov),
    "-vn", "-ar", "44100", "-ac", "2",
    str(out_dir / "m4a1_burst_clean.wav")
], check=True)

# Extract Headshot dink (from 10.00s to 10.50s, 0.5s duration)
subprocess.run([
    "ffmpeg", "-y", "-ss", "10.00", "-t", "0.55",
    "-i", str(hero_pov),
    "-vn", "-ar", "44100", "-ac", "2",
    str(out_dir / "headshot_dink_clean.wav")
], check=True)

print("Clean CS2 weapon sounds extracted directly from hero POV gameplay!")
