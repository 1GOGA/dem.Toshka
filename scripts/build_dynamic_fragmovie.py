import math
import os
import pathlib
import subprocess
import time
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal

OUT_DIR = pathlib.Path("renders/ACE_FINAL_V4_MASTER_CUT")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TAKES_DIR = pathlib.Path("renders/cinematic_studio_phase3/takes")
COLOR_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/color")
LUT_PATH = COLOR_DIR / "egyptian_sandstone_cinematic.cube"
lut_fwd = str(LUT_PATH).replace("\\", "/")

TAKE_SHOULDER = TAKES_DIR / "shot_anubis_ace_r19_02_shoulder_approach.mp4"
TAKE_HERO = TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4"
TAKE_ORBIT = TAKES_DIR / "shot_anubis_ace_r19_04_climax_orbit.mp4"

MUSIC_SRC = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/audio/lovelydiller_malyshka_revnuet.wav")
M4A1_SAMPLE = OUT_DIR / "audio_clean/m4a1_burst_clean.wav"
DINK_SAMPLE = OUT_DIR / "audio_clean/headshot_dink_clean.wav"
SFX_DIR = pathlib.Path("renders/ACE_FINAL_V3_AUDIO_KILLFEED/sfx_library")

RATE = 44100
MONTAGE_DUR = 12.5
TOTAL_SAMPLES = int(MONTAGE_DUR * RATE)

def load_resample(wav_path, target_sr=RATE):
    sr, data = wavfile.read(str(wav_path))
    if data.ndim == 1:
        data = np.column_stack([data, data])
    if data.dtype == np.int16:
        data_f = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data_f = data.astype(np.float32) / 2147483648.0
    else:
        data_f = data.astype(np.float32)
    
    if sr != target_sr:
        num_target = int(len(data_f) * target_sr / sr)
        resampled_l = signal.resample(data_f[:, 0], num_target)
        resampled_r = signal.resample(data_f[:, 1], num_target)
        data_f = np.column_stack([resampled_l, resampled_r])
    return data_f

def write_wav(path, data):
    data_clipped = np.clip(data, -1.0, 1.0)
    data_int16 = (data_clipped * 32767.0).astype(np.int16)
    wavfile.write(str(path), RATE, data_int16)

# ==============================================================================
# 1. BUILD PURE, UNMUFFLED, HIGH-IMPACT SOUND DESIGN
# ==============================================================================
print("=== 1. Building High-Fidelity Fragmovie Audio Mix ===")
# Timeline timestamps for kills in the dynamic edit:
# Intro Shoulder: 0.0s - 1.8s
# Whip-Pan: 1.8s - 2.0s
# Hero Peek: 2.0s - 2.18s
# Kill 1 (Tiger07): 2.18s (808 BASS DROP)
# Kill 2 (zuuuuuhhhhn): 3.85s
# Kill 3 (ProfyfGames HEADSHOT): 5.30s
# Kill 4 (freekjkeee): 6.00s
# Orbit Climax: 6.80s - 12.5s

# Music: LOVELYDILLER starting at 25.62s (drop lands exactly at 2.18s!)
music_full = load_resample(MUSIC_SRC)
music_start_idx = int((27.80 - 2.18) * RATE) # 25.62s
music_track = music_full[music_start_idx:music_start_idx + TOTAL_SAMPLES].copy()
if len(music_track) < TOTAL_SAMPLES:
    pad = np.zeros((TOTAL_SAMPLES - len(music_track), 2), dtype=np.float32)
    music_track = np.vstack([music_track, pad])

# Sidechain ducking on each gunshot (-3 dB = 0.70 gain for 90ms)
duck_points = [2.18, 3.85, 5.30, 6.00]
for dt in duck_points:
    d_start = int((dt - 0.01) * RATE)
    d_len = int(0.12 * RATE)
    d_ramp = np.ones(d_len, dtype=np.float32)
    r_in = int(0.02 * RATE)
    r_out = int(0.06 * RATE)
    d_ramp[:r_in] = np.linspace(1.0, 0.70, r_in)
    d_ramp[r_in:r_in+int(0.04*RATE)] = 0.70
    d_ramp[-r_out:] = np.linspace(0.70, 1.0, r_out)
    if d_start + d_len < TOTAL_SAMPLES:
        music_track[d_start:d_start+d_len] *= d_ramp[:, None]

# Fade out music at 11.5s - 12.5s
fade_idx = int(11.5 * RATE)
music_track[fade_idx:] *= np.linspace(1.0, 0.0, TOTAL_SAMPLES - fade_idx)[:, None]

# Gunshots & Foley Track
gunshots_track = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
m4a1_snd = load_resample(M4A1_SAMPLE)
dink_snd = load_resample(DINK_SAMPLE)

def add_sound(dest, src, start_t, gain=1.0):
    start_idx = int(start_t * RATE)
    end_idx = min(start_idx + len(src), len(dest))
    actual_len = end_idx - start_idx
    if actual_len > 0:
        dest[start_idx:end_idx] += src[:actual_len] * gain

# K1: M4A1 burst
add_sound(gunshots_track, m4a1_snd, 2.18, gain=1.20)
# K2: M4A1 burst
add_sound(gunshots_track, m4a1_snd, 3.85, gain=1.15)
# K3: M4A1 burst + iconic headshot dink crunch
add_sound(gunshots_track, m4a1_snd, 5.30, gain=1.10)
add_sound(gunshots_track, dink_snd, 5.30, gain=1.40)
# K4: M4A1 burst
add_sound(gunshots_track, m4a1_snd, 6.00, gain=1.20)

# Whoosh on whip-pan transition (1.75s)
whip_snd = load_resample(SFX_DIR / "3_transitions/transition_wind_whip_turbulent.wav")
add_sound(gunshots_track, whip_snd, 1.75, gain=0.65)

# Sub-bass punch on K1 drop and Headshot
sub_downer = load_resample(SFX_DIR / "1_cinematic_impacts/impact_sub_downer_fast16.wav")
add_sound(gunshots_track, sub_downer, 2.18, gain=0.75)
add_sound(gunshots_track, sub_downer, 5.30, gain=0.85)

# Mixdown
final_audio = music_track * 0.85 + gunshots_track * 0.90
peak = np.max(np.abs(final_audio))
if peak > 0.90:
    final_audio = final_audio * (0.90 / peak)

dynamic_audio_path = OUT_DIR / "audio/audio_dynamic_master.wav"
write_wav(dynamic_audio_path, final_audio)
print("Pristine dynamic audio written:", dynamic_audio_path)

# ==============================================================================
# 2. BUILD HIGH-VELOCITY DYNAMIC VIDEO MONTAGE (NO UGLY PIL OVERLAYS)
# ==============================================================================
print("\n=== 2. Rendering Dynamic High-Velocity Fragmovie (No Clumsy Overlays) ===")

# Video Structure:
# 1. Shoulder Take: 0.0s to 1.95s (in edit: 0.0s to 1.85s)
#    - Camera runs forward, smooth zoom pump
# 2. Whip-Pan cut at 1.85s into Hero POV at source 5.25s:
#    - Hero POV pt 1: 5.25s to 5.90s (dur 0.65s) -> Peek and KILL 1 (Tiger07 at 5.68s = 2.18s timeline!)
#    - Hero POV speed ramp 1: 5.90s to 7.90s at 2.5x speed (source 2.0s -> 0.80s in edit!)
#    - Hero POV pt 2: 7.90s to 8.60s (dur 0.70s) -> KILL 2 (zuuuuuhhhhn at 8.30s = 3.85s timeline!)
#    - Hero POV speed ramp 2: 8.60s to 9.80s at 2.5x speed (source 1.2s -> 0.48s in edit!)
#    - Hero POV pt 3: 9.80s to 10.25s at 50% slow-mo (source 0.45s -> 0.90s in edit!) -> KILL 3 HEADSHOT (ProfyfGames at 10.08s = 5.30s timeline!)
#    - Hero POV pt 4: 10.25s to 11.20s (dur 0.95s) -> Rapid transfer to KILL 4 (freekjkeee at 10.90s = 6.00s timeline!)
# 3. Flash impact cut at 6.65s into Orbit Climax:
#    - Orbit Take: source 0.5s to 6.35s (dur 5.85s in edit) -> Victory Orbit with golden aura, ending at 12.5s!

filter_complex = f"""
[0:v]trim=start=0.0:end=1.95,setpts=PTS-STARTPTS,fps=60,settb=1/60[v_shoulder];

[1:v]trim=start=5.25:end=5.90,setpts=PTS-STARTPTS,fps=60,settb=1/60[v_k1];
[1:v]trim=start=5.90:end=7.90,setpts=0.40*(PTS-STARTPTS),fps=60,settb=1/60[v_ramp1];
[1:v]trim=start=7.90:end=8.60,setpts=PTS-STARTPTS,fps=60,settb=1/60[v_k2];
[1:v]trim=start=8.60:end=9.80,setpts=0.40*(PTS-STARTPTS),fps=60,settb=1/60[v_ramp2];
[1:v]trim=start=9.80:end=10.25,setpts=2.0*(PTS-STARTPTS),fps=60,settb=1/60[v_k3_slow];
[1:v]trim=start=10.25:end=11.20,setpts=PTS-STARTPTS,fps=60,settb=1/60[v_k4];

[v_k1][v_ramp1][v_k2][v_ramp2][v_k3_slow][v_k4]concat=n=6:v=1:a=0,fps=60,settb=1/60[v_hero_action];

[2:v]trim=start=0.5:end=6.35,setpts=PTS-STARTPTS,fps=60,settb=1/60[v_orbit];

[v_shoulder][v_hero_action]xfade=transition=slideleft:duration=0.15:offset=1.80[x1];
[x1][v_orbit]xfade=transition=circlecrop:duration=0.20:offset=6.65[raw_montage];

[raw_montage]
lut3d='{lut_fwd}',
crop=w='iw*(1-0.06*between(t,2.15,2.28)-0.05*between(t,3.82,3.95)-0.08*between(t,5.25,5.45)-0.05*between(t,5.97,6.08))':
h='ih*(1-0.06*between(t,2.15,2.28)-0.05*between(t,3.82,3.95)-0.08*between(t,5.25,5.45)-0.05*between(t,5.97,6.08))':
x='(iw-ow)/2':y='(ih-oh)/2',scale=1920:1080:flags=bicubic,
eq=brightness=0.22:contrast=1.20:enable='between(t,2.18,2.24)+between(t,3.85,3.91)+between(t,5.30,5.37)+between(t,6.00,6.06)+between(t,6.65,6.75)',
curves=master='0/0 0.5/0.52 1/1':red='0/0 0.5/0.55 1/1':blue='0/0 0.5/0.46 1/1':enable='between(t,6.8,12.5)',
fade=t=out:st=11.7:d=0.8[v_final]
"""

out_video = OUT_DIR / "ACE_DYNAMIC_RESOLVE_CUT.mp4"

cmd = [
    "ffmpeg", "-y",
    "-i", str(TAKE_SHOULDER),
    "-i", str(TAKE_HERO),
    "-i", str(TAKE_ORBIT),
    "-i", str(dynamic_audio_path),
    "-filter_complex", filter_complex,
    "-map", "[v_final]",
    "-map", "3:a",
    "-t", "12.5",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "320k",
    "-pix_fmt", "yuv420p",
    str(out_video)
]

print("Rendering ACE_DYNAMIC_RESOLVE_CUT.mp4...")
t0 = time.time()
subprocess.run(cmd, check=True)
print(f"Dynamic Fragmovie successfully rendered in {time.time()-t0:.1f}s ({out_video.stat().st_size} bytes): {out_video}")
