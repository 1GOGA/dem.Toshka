import math
import os
import pathlib
import subprocess
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal

V4_DIR = pathlib.Path("renders/ACE_FINAL_V4_MASTER_CUT")
AUDIO_DIR = V4_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SFX_DIR = pathlib.Path("renders/ACE_FINAL_V3_AUDIO_KILLFEED/sfx_library")
TAKES_DIR = pathlib.Path("renders/cinematic_studio_phase3/takes")
MUSIC_SRC = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/audio/lovelydiller_malyshka_revnuet.wav")

RATE = 44100
DURATION_S = 15.0
TOTAL_SAMPLES = int(DURATION_S * RATE)

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

def extract_take_audio(take_file, start_s, dur_s):
    temp_wav = AUDIO_DIR / "temp_extract.wav"
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_s),
        "-t", str(dur_s),
        "-i", str(take_file),
        "-vn", "-ar", str(RATE), "-ac", "2",
        str(temp_wav)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data = load_resample(temp_wav)
    temp_wav.unlink(missing_ok=True)
    return data

print("=== Building Synchronized V4 Fairlight Audio Mix ===")

# ==============================================================================
# TRACK A1: Gameplay Audio Matched to Video Retime
# ==============================================================================
# Clip 1: Shoulder (0.0 to 2.40s, in edit 0.0 to 2.20s)
s1 = extract_take_audio(TAKES_DIR / "shot_anubis_ace_r19_02_shoulder_approach.mp4", 0.0, 2.20)

# Clip 2A: Hero POV normal (source 5.20s to 9.95s, dur 4.75s)
s2a = extract_take_audio(TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4", 5.20, 4.75)

# Clip 2B: Headshot slow-mo (source 9.95s to 10.20s, raw 0.25s -> stretched to 0.50s)
s2b_raw = extract_take_audio(TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4", 9.95, 0.25)
n_slow = int(0.50 * RATE)
s2b = np.column_stack([
    signal.resample(s2b_raw[:, 0], n_slow),
    signal.resample(s2b_raw[:, 1], n_slow)
])

# Clip 2C: Hero POV normal (source 10.20s to 11.80s, dur 1.60s)
s2c = extract_take_audio(TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4", 10.20, 1.60)

# Clip 3: Orbit Climax (source 0.0s to 6.20s)
s3 = extract_take_audio(TAKES_DIR / "shot_anubis_ace_r19_04_climax_orbit.mp4", 0.0, 6.20)

# Assemble gameplay timeline:
a1_gameplay = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

def place_direct(dest, src, start_t):
    start_idx = int(start_t * RATE)
    end_idx = min(start_idx + len(src), len(dest))
    actual_len = end_idx - start_idx
    if actual_len > 0:
        dest[start_idx:end_idx] += src[:actual_len]

place_direct(a1_gameplay, s1, 0.0)
place_direct(a1_gameplay, s2a, 2.20)
place_direct(a1_gameplay, s2b, 2.20 + 4.75)
place_direct(a1_gameplay, s2c, 2.20 + 4.75 + 0.50)
place_direct(a1_gameplay, s3, 8.85)

write_wav(AUDIO_DIR / "stem_a1_gameplay.wav", a1_gameplay * 0.90)

# ==============================================================================
# TRACK A2: Music Track (LOVELYDILLER with Intro Filter & Gunshot Ducking)
# ==============================================================================
music_full = load_resample(MUSIC_SRC)
music_start_idx = int(25.12 * RATE)
music_chunk = music_full[music_start_idx:music_start_idx + TOTAL_SAMPLES].copy()
if len(music_chunk) < TOTAL_SAMPLES:
    pad = np.zeros((TOTAL_SAMPLES - len(music_chunk), 2), dtype=np.float32)
    music_chunk = np.vstack([music_chunk, pad])

# Intro Low-Pass Filter
sos_lp = signal.butter(4, 700.0, 'lowpass', fs=RATE, output='sos')
music_filtered_intro = signal.sosfilt(sos_lp, music_chunk[:int(2.4 * RATE)], axis=0)
intro_samples = int(2.4 * RATE)
fade_w = int(0.4 * RATE)
t_blend = np.linspace(0.0, 1.0, fade_w)[:, None]
music_chunk[:intro_samples - fade_w] = music_filtered_intro[:intro_samples - fade_w]
music_chunk[intro_samples - fade_w:intro_samples] = (
    (1.0 - t_blend) * music_filtered_intro[intro_samples - fade_w:intro_samples] +
    t_blend * music_chunk[intro_samples - fade_w:intro_samples]
)

# Sidechain ducking on gunshots
duck_times = [2.68, 5.30, 7.21, 8.15]
for dt in duck_times:
    d_start = int((dt - 0.02) * RATE)
    d_len = int(0.18 * RATE)
    d_ramp = np.ones(d_len, dtype=np.float32)
    r_in = int(0.03 * RATE)
    r_out = int(0.10 * RATE)
    d_ramp[:r_in] = np.linspace(1.0, 0.67, r_in)
    d_ramp[r_in:r_in+int(0.05*RATE)] = 0.67
    d_ramp[-r_out:] = np.linspace(0.67, 1.0, r_out)
    if d_start + d_len < TOTAL_SAMPLES:
        music_chunk[d_start:d_start+d_len] *= d_ramp[:, None]

# Fade out 14.0s - 15.0s
fade_out_idx = int(14.0 * RATE)
fade_out_len = TOTAL_SAMPLES - fade_out_idx
music_chunk[fade_out_idx:] *= np.linspace(1.0, 0.0, fade_out_len)[:, None]

write_wav(AUDIO_DIR / "stem_a2_music_142bpm.wav", music_chunk * 0.85)

# ==============================================================================
# TRACK A3: Cinematic Sub-bass Impacts (Sonniss GDC)
# ==============================================================================
a3_impacts = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
sub_downer = load_resample(SFX_DIR / "1_cinematic_impacts/impact_sub_downer_fast16.wav")
sub_med = load_resample(SFX_DIR / "1_cinematic_impacts/impact_sub_downer_med04.wav")

def place_fade(dest, src, start_t, gain=1.0):
    start_idx = int(start_t * RATE)
    end_idx = min(start_idx + len(src), len(dest))
    actual_len = end_idx - start_idx
    if actual_len > 0:
        dest[start_idx:end_idx] += src[:actual_len] * gain

place_fade(a3_impacts, sub_downer, 2.68, gain=0.80)
place_fade(a3_impacts, sub_downer, 5.30, gain=0.65)
place_fade(a3_impacts, sub_med, 7.21, gain=0.90)
place_fade(a3_impacts, sub_downer, 8.15, gain=0.70)
place_fade(a3_impacts, sub_med, 8.95, gain=1.00)

write_wav(AUDIO_DIR / "stem_a3_cinematic_impacts.wav", a3_impacts)

# ==============================================================================
# TRACK A4: Transition Whooshes
# ==============================================================================
a4_whooshes = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
whip_whoosh = load_resample(SFX_DIR / "3_transitions/transition_wind_whip_turbulent.wav")
air_blast = load_resample(SFX_DIR / "2_whooshes/whoosh_air_blast_clean.wav")

place_fade(a4_whooshes, whip_whoosh, 2.05, gain=0.75)
place_fade(a4_whooshes, air_blast, 8.65, gain=0.80)

write_wav(AUDIO_DIR / "stem_a4_transition_whooshes.wav", a4_whooshes)

# ==============================================================================
# TRACK A5: Risers & Accents
# ==============================================================================
a5_accents = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
riser = load_resample(SFX_DIR / "4_risers/riser_cinematic_tension_swell.wav")
ricochet = load_resample(SFX_DIR / "7_gameplay_accents/accent_metal_ricochet_spin.wav")
click = load_resample(SFX_DIR / "5_glitch_digital/glitch_mechanism_counting_tick.wav")

riser_cut = riser[:int(2.2 * RATE)]
place_fade(a5_accents, riser_cut, 0.2, gain=0.60)
place_fade(a5_accents, ricochet, 7.21, gain=0.55)
place_fade(a5_accents, click, 2.70, gain=0.40)
place_fade(a5_accents, click, 5.32, gain=0.40)
place_fade(a5_accents, click, 7.23, gain=0.45)
place_fade(a5_accents, click, 8.17, gain=0.45)
place_fade(a5_accents, click, 8.95, gain=0.60)

write_wav(AUDIO_DIR / "stem_a5_risers_accents.wav", a5_accents)

# ==============================================================================
# TRACK A6: Atmosphere
# ==============================================================================
atmos_raw = load_resample(SFX_DIR / "6_atmospheric/atmos_open_air_subtle.wav")
atmos_chunk = atmos_raw[:TOTAL_SAMPLES].copy()
if len(atmos_chunk) < TOTAL_SAMPLES:
    pad = np.zeros((TOTAL_SAMPLES - len(atmos_chunk), 2), dtype=np.float32)
    atmos_chunk = np.vstack([atmos_chunk, pad])
atmos_chunk[:int(0.5 * RATE)] *= np.linspace(0.0, 1.0, int(0.5 * RATE))[:, None]
atmos_chunk[int(14.0 * RATE):] *= np.linspace(1.0, 0.0, TOTAL_SAMPLES - int(14.0 * RATE))[:, None]
a6_atmos = atmos_chunk * 0.30

write_wav(AUDIO_DIR / "stem_a6_atmosphere.wav", a6_atmos)

# ==============================================================================
# MASTER MIXDOWN & NORMALIZATION
# ==============================================================================
master = (
    a1_gameplay * 0.85 +
    music_chunk * 0.80 +
    a3_impacts * 0.50 +
    a4_whooshes * 0.40 +
    a5_accents * 0.45 +
    a6_atmos * 0.25
)

peak = np.max(np.abs(master))
print(f"Raw mix peak: {peak:.3f} ({20*math.log10(max(peak, 1e-6)):.1f} dBFS)")
if peak > 0.89:
    master = master * (0.89 / peak)

write_wav(AUDIO_DIR / "audio_master_v4.wav", master)
print("Synchronized V4 Master Audio successfully generated:", AUDIO_DIR / "audio_master_v4.wav")
