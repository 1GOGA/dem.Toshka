import json
import pathlib
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal

wav_path = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/audio/lovelydiller_malyshka_revnuet.wav")
rate, data = wavfile.read(str(wav_path))
mono = data.mean(axis=1).astype(np.float32) / 32768.0

# 142 BPM means beat duration is 60.0 / 142.0 = 0.422535 seconds
bpm = 142.0
beat_dur = 60.0 / bpm

# Detect the exact transient of the drop kick near 26s
# Window around 25.0 to 27.5s
w_start = int(25.0 * rate)
w_end = int(28.0 * rate)
chunk = mono[w_start:w_end]

# High-pass filter above 30Hz and low-pass below 160Hz for sub-bass kick transient
sos = signal.butter(4, [30.0, 150.0], btype='bandpass', fs=rate, output='sos')
kick_sub = signal.sosfilt(sos, chunk)
kick_env = np.abs(kick_sub)

# Find maximum transient
peak_idx = np.argmax(kick_env)
exact_drop_time = round(25.0 + peak_idx / float(rate), 3)
print(f"Exact beat drop timestamp: {exact_drop_time}s")

# Build beat grid backwards and forwards from drop time
beats = []
t = exact_drop_time
while t >= 0:
    beats.append(round(t, 4))
    t -= beat_dur
beats = sorted(beats)

t = exact_drop_time + beat_dur
total_dur = len(mono) / float(rate)
while t <= total_dur:
    beats.append(round(t, 4))
    t += beat_dur

# Find downbeats (every 4 beats)
drop_index = beats.index(exact_drop_time)
downbeats = [beats[i] for i in range(len(beats)) if (i - drop_index) % 4 == 0]

beat_map = {
    "track_name": "LOVELYDILLER — МАЛЫШКА РЕВНУЕТ",
    "artist": "LOVELYDILLER",
    "bpm": 142.0,
    "beat_duration_seconds": round(beat_dur, 4),
    "measure_duration_seconds": round(beat_dur * 4.0, 4),
    "drop_timestamp_seconds": exact_drop_time,
    "sections": [
        {"name": "Intro", "start_seconds": 0.0, "end_seconds": 13.5, "energy": "low_ambient"},
        {"name": "Vocal Build-up", "start_seconds": 13.5, "end_seconds": 25.5, "energy": "medium_rising"},
        {"name": "Pre-drop Tension", "start_seconds": 25.5, "end_seconds": exact_drop_time, "energy": "breath_pause"},
        {"name": "Main Hook / Beat Drop", "start_seconds": exact_drop_time, "end_seconds": 54.0, "energy": "high_explosive"},
        {"name": "Verse 2", "start_seconds": 54.0, "end_seconds": 78.0, "energy": "medium_groove"},
    ],
    "beats": beats,
    "downbeats": downbeats,
}

out_json = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/audio/music_beat_map.json")
out_json.write_text(json.dumps(beat_map, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Saved beat map with {len(beats)} beats and {len(downbeats)} downbeats to {out_json}")
