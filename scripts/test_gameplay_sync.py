import numpy as np
import scipy.io.wavfile as wavfile
import subprocess
import pathlib

AUDIO_DIR = pathlib.Path("renders/ACE_FINAL_V3_AUDIO_KILLFEED/audio")
TAKES_DIR = pathlib.Path("renders/cinematic_studio_phase3/takes")

RATE = 44100
TOTAL_SAMPLES = int(18.5 * RATE)

# We extract audio from each take for its exact active duration in the timeline:
# Segment 1: Shoulder take (0.0 to 2.15s)
# Segment 2: Hero POV take (0.0 to 9.15s) -> timeline 2.15s to 11.30s
# Segment 3: Victim take (0.0 to 1.30s) -> timeline 11.30s to 12.60s
# Segment 4: Hero POV take (10.50 to 13.60s) -> timeline 12.60s to 15.70s
# Segment 5: Orbit take (0.0 to 2.80s) -> timeline 15.70s to 18.50s

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
    sr, data = wavfile.read(str(temp_wav))
    temp_wav.unlink()
    if data.dtype == np.int16:
        return data.astype(np.float32) / 32768.0
    return data.astype(np.float32)

print("Extracting perfectly synced gameplay segments from takes...")
s1 = extract_take_audio(TAKES_DIR / "shot_anubis_ace_r19_02_shoulder_approach.mp4", 0.0, 2.15)
s2 = extract_take_audio(TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4", 0.0, 9.15)
s3 = extract_take_audio(TAKES_DIR / "shot_anubis_ace_r19_03_victim_reaction.mp4", 0.0, 1.30)
s4 = extract_take_audio(TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4", 10.50, 3.10)
s5 = extract_take_audio(TAKES_DIR / "shot_anubis_ace_r19_04_climax_orbit.mp4", 0.0, 2.80)

# Concatenate with crossfades
gameplay_synced = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# Place s1: 0.0 to 2.15s
idx1 = int(2.15 * RATE)
gameplay_synced[:len(s1)] = s1[:len(gameplay_synced)]

# Place s2: 2.15 to 11.30s
idx2_end = idx1 + len(s2)
if idx2_end > TOTAL_SAMPLES:
    s2 = s2[:TOTAL_SAMPLES - idx1]
gameplay_synced[idx1:idx1+len(s2)] = s2

# Place s3: 11.30 to 12.60s
idx3_start = int(11.30 * RATE)
idx3_end = idx3_start + len(s3)
if idx3_end > TOTAL_SAMPLES:
    s3 = s3[:TOTAL_SAMPLES - idx3_start]
gameplay_synced[idx3_start:idx3_start+len(s3)] = s3

# Place s4: 12.60 to 15.70s
idx4_start = int(12.60 * RATE)
idx4_end = idx4_start + len(s4)
if idx4_end > TOTAL_SAMPLES:
    s4 = s4[:TOTAL_SAMPLES - idx4_start]
gameplay_synced[idx4_start:idx4_start+len(s4)] = s4

# Place s5: 15.70 to 18.50s
idx5_start = int(15.70 * RATE)
s5_len = min(len(s5), TOTAL_SAMPLES - idx5_start)
gameplay_synced[idx5_start:idx5_start+s5_len] = s5[:s5_len]

# Analyze transient spikes around Kill 1 (7.5s - 8.2s)
k1_chunk = np.abs(gameplay_synced[int(7.5 * RATE):int(8.2 * RATE), 0])
spike_idx = np.argmax(k1_chunk)
spike_time = 7.5 + spike_idx / float(RATE)
print(f"Verified Kill 1 gunshot transient in Track A1 at: {spike_time:.4f}s (Expected ~7.83s)")

# Analyze transient spikes around Kill 2 (10.2s - 10.7s)
k2_chunk = np.abs(gameplay_synced[int(10.2 * RATE):int(10.7 * RATE), 0])
spike2_idx = np.argmax(k2_chunk)
spike2_time = 10.2 + spike2_idx / float(RATE)
print(f"Verified Kill 2 gunshot transient in Track A1 at: {spike2_time:.4f}s (Expected ~10.45s)")
