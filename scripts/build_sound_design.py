import json
import math
import pathlib
import numpy as np
import scipy.io.wavfile as wavfile
import subprocess

AUDIO_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

RATE = 44100
DURATION_S = 18.5
TOTAL_SAMPLES = int(DURATION_S * RATE)

# 1. Stem A2: Music (142 BPM, LOVELYDILLER — МАЛЫШКА РЕВНУЕТ)
source_wav = AUDIO_DIR / "lovelydiller_malyshka_revnuet.wav"
rate_m, data_m = wavfile.read(str(source_wav))
if rate_m != RATE:
    # resample if needed
    pass

# music offset is 19.62s
start_idx = int(19.62 * rate_m)
end_idx = start_idx + TOTAL_SAMPLES
music_slice = data_m[start_idx:end_idx].astype(np.float32) / 32768.0

# Apply fade in (0.3s) and fade out (1.2s)
fade_in_len = int(0.3 * RATE)
fade_out_len = int(1.2 * RATE)
fade_in = np.linspace(0.0, 1.0, fade_in_len)
fade_out = np.linspace(1.0, 0.0, fade_out_len)

for ch in range(music_slice.shape[1]):
    music_slice[:fade_in_len, ch] *= fade_in
    music_slice[-fade_out_len:, ch] *= fade_out

# Music volume balance (-4 dB for fragmovie mix so gunshots cut through)
music_stem = music_slice * 0.65

# 2. Stem A1: Gameplay Audio
# Extract audio from takes:
# 0.0s - 2.5s: shot_anubis_ace_r19_02_shoulder_approach.mp4 (0s to 2.5s)
# 2.5s - 11.7s: shot_anubis_ace_r19_01_hero_pov.mp4 (2.5s to 11.7s)
# 11.7s - 13.1s: shot_anubis_ace_r19_03_victim_reaction.mp4 (0s to 1.4s)
# 13.1s - 15.5s: shot_anubis_ace_r19_01_hero_pov.mp4 (13.1s to 15.5s)
# 15.5s - 18.5s: shot_anubis_ace_r19_04_climax_orbit.mp4 (0s to 3.0s)
gameplay_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

temp_gameplay_wav = AUDIO_DIR / "temp_gameplay.wav"
# Let's extract audio from hero POV as base gameplay
cmd_extract = [
    "ffmpeg", "-y",
    "-ss", "0.0", "-t", "18.5",
    "-i", "renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_01_hero_pov.mp4",
    "-vn", "-ar", "44100", "-ac", "2",
    str(temp_gameplay_wav)
]
subprocess.run(cmd_extract, check=True)
rate_g, data_g = wavfile.read(str(temp_gameplay_wav))
g_len = min(TOTAL_SAMPLES, len(data_g))
gameplay_stem[:g_len] = data_g[:g_len].astype(np.float32) / 32768.0

# Boost gameplay gunshots / crispness (+2 dB)
gameplay_stem = gameplay_stem * 1.25

# 3. Stem A3: Sub-Bass 808 Impacts (synthesized punch on kill moments)
sub_bass_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
kill_times = [8.18, 10.72, 12.41, 13.25, 15.79]

for kt in kill_times:
    idx = int(kt * RATE)
    impact_dur = 0.5  # 500ms 808 sub kick
    impact_samples = int(impact_dur * RATE)
    if idx + impact_samples > TOTAL_SAMPLES:
        impact_samples = TOTAL_SAMPLES - idx
    
    t = np.linspace(0, impact_dur, impact_samples, endpoint=False)
    # Exponential pitch drop from 110Hz to 40Hz
    freq = 40.0 + 70.0 * np.exp(-t * 15.0)
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    sine_wave = np.sin(phase)
    # Exponential amplitude envelope
    env = np.exp(-t * 6.0)
    sub = (sine_wave * env).astype(np.float32)
    # Add subtle soft saturation
    sub = np.tanh(sub * 1.5) * 0.7
    
    sub_bass_stem[idx:idx+impact_samples, 0] += sub
    sub_bass_stem[idx:idx+impact_samples, 1] += sub

# 4. Stem A4: Transition Whooshes (filtered stereo sweeps on cuts)
whoosh_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
transition_times = [2.5, 11.7, 13.1, 15.5]

for tt in transition_times:
    dur = 0.45
    w_samples = int(dur * RATE)
    idx = int((tt - dur/2.0) * RATE)
    if idx < 0:
        idx = 0
    if idx + w_samples > TOTAL_SAMPLES:
        w_samples = TOTAL_SAMPLES - idx
    
    # Generate shaped white noise
    noise = np.random.uniform(-1.0, 1.0, w_samples)
    t = np.linspace(0, 1, w_samples)
    # Bell-shaped envelope
    env = np.sin(t * np.pi) ** 2
    # Stereo panning sweep: Left to Right
    pan_l = np.cos(t * np.pi / 2.0)
    pan_r = np.sin(t * np.pi / 2.0)
    
    whoosh_l = (noise * env * pan_l * 0.4).astype(np.float32)
    whoosh_r = (noise * env * pan_r * 0.4).astype(np.float32)
    
    whoosh_stem[idx:idx+w_samples, 0] += whoosh_l
    whoosh_stem[idx:idx+w_samples, 1] += whoosh_r

# 5. Stem A5: Tension Riser (leading into the 8.18s beat drop)
riser_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
r_start = int(4.5 * RATE)
r_end = int(8.18 * RATE)
r_samples = r_end - r_start
t_r = np.linspace(0, 1, r_samples, endpoint=False)
# Pitch rise from 100Hz to 600Hz
freq_r = 100.0 + 500.0 * (t_r ** 2)
phase_r = 2 * np.pi * np.cumsum(freq_r) / RATE
saw = signal_saw = 2.0 * (phase_r / (2 * np.pi) - np.floor(phase_r / (2 * np.pi) + 0.5))
env_r = (t_r ** 2.5) * 0.35
riser = (saw * env_r).astype(np.float32)
riser_stem[r_start:r_end, 0] = riser
riser_stem[r_start:r_end, 1] = riser

# Save individual stems
def write_stem(name, data):
    p = AUDIO_DIR / name
    # clip to prevent overflow
    np.clip(data, -1.0, 1.0, out=data)
    i16 = (data * 32767.0).astype(np.int16)
    wavfile.write(str(p), RATE, i16)
    print(f"Saved stem: {p.name}")

write_stem("stem_a1_gameplay.wav", gameplay_stem)
write_stem("stem_a2_music.wav", music_stem)
write_stem("stem_a3_sub_bass.wav", sub_bass_stem)
write_stem("stem_a4_whooshes.wav", whoosh_stem)
write_stem("stem_a5_risers.wav", riser_stem)

# Master Mixdown
master = gameplay_stem + music_stem + sub_bass_stem + whoosh_stem + riser_stem

# Peak normalization with 1.0 dB headroom (-1.0 dBFS = 0.891)
max_peak = np.max(np.abs(master))
if max_peak > 0:
    target_peak = 0.891
    master = master * (target_peak / max_peak)

write_stem("audio_master_5track.wav", master)

# Manifest
manifest = {
    "montage_duration_seconds": DURATION_S,
    "sample_rate": RATE,
    "channels": 2,
    "target_lufs": -14.0,
    "tracks": [
        {"track": "A1", "name": "Gameplay", "file": "stem_a1_gameplay.wav", "level_db": 2.0, "description": "CS2 in-game weapon fire, bullet cracks, footsteps"},
        {"track": "A2", "name": "Music Master", "file": "stem_a2_music.wav", "level_db": -4.0, "description": "LOVELYDILLER — МАЛЫШКА РЕВНУЕТ (142 BPM, drop at 8.18s)"},
        {"track": "A3", "name": "Sub-Bass 808", "file": "stem_a3_sub_bass.wav", "level_db": 0.0, "description": "45Hz synthesized 808 transient impacts on kill ticks"},
        {"track": "A4", "name": "Transition Whooshes", "file": "stem_a4_whooshes.wav", "level_db": -6.0, "description": "Stereo swept noise risers for camera angle cuts"},
        {"track": "A5", "name": "Pre-Drop Tension Riser", "file": "stem_a5_risers.wav", "level_db": -8.0, "description": "Exponential pitch riser (4.5s - 8.18s) building to drop"}
    ],
    "master_output": "audio_master_5track.wav",
    "peak_dbfs": -1.0
}
(AUDIO_DIR / "sound_design_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print("Sound design manifest saved successfully.")
