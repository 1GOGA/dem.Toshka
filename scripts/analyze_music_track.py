import json
import pathlib
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal

wav_path = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/audio/lovelydiller_malyshka_revnuet.wav")
rate, data = wavfile.read(str(wav_path))

# Convert to mono float32
if data.ndim > 1:
    mono = data.mean(axis=1).astype(np.float32) / 32768.0
else:
    mono = data.astype(np.float32) / 32768.0

total_duration = len(mono) / float(rate)
print(f"Loaded audio: {total_duration:.2f}s, sample rate: {rate} Hz")

# Downsample to 1000 Hz for envelope analysis
hop = rate // 1000
env = np.abs(mono[::hop])
# Lowpass filter the envelope at 12 Hz
b, a = signal.butter(2, 12.0 / (500.0), btype='low')
smooth_env = signal.filtfilt(b, a, env)
diff_env = np.maximum(0, np.diff(smooth_env))

# Autocorrelation for BPM estimation between 90 and 170 BPM
# Lag range in 1000 Hz samples:
# 60 / 170 * 1000 = 353 samples
# 60 / 90 * 1000 = 667 samples
min_lag = int(60.0 / 170.0 * 1000)
max_lag = int(60.0 / 85.0 * 1000)

corr = signal.correlate(diff_env[:30000], diff_env[:30000], mode='full')
corr = corr[len(corr)//2:]
search_window = corr[min_lag:max_lag]
best_lag = min_lag + np.argmax(search_window)
estimated_bpm = round(60.0 * 1000.0 / best_lag, 1)

# Check half-time or double-time harmonics
print(f"Initial estimated BPM: {estimated_bpm} (lag={best_lag})")

# Sub-band analysis: energy in 2-second windows across first 60 seconds
window_sec = 2.0
win_size = int(window_sec * rate)
num_windows = int(60.0 / window_sec)
energies = []
for i in range(num_windows):
    chunk = mono[i * win_size : (i + 1) * win_size]
    rms = float(np.sqrt(np.mean(chunk**2)))
    energies.append((i * window_sec, rms))

print("\nEnergy progression (first 60s):")
for t, e in energies:
    bar = "#" * int(e * 100)
    print(f"  {t:4.1f}s: {e:.3f} {bar}")

# Identify peaks and drops
# The drop is where energy surges after a build-up
max_diff = 0.0
drop_time = 0.0
for i in range(1, len(energies)):
    d = energies[i][1] - energies[i-1][1]
    if d > max_diff:
        max_diff = d
        drop_time = energies[i][0]

print(f"\nDetected Drop / Major Accent around: {drop_time:.2f}s")
