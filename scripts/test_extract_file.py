import pathlib
from test_remote_zip import inspect_remote_zip

zf, names = inspect_remote_zip("https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle1of5.zip", 1301592146)
# find a wav file
wavs = [n for n in names if n.endswith('.wav')]
print(f"Found {len(wavs)} WAV files in Bundle 1.")
first_wav = wavs[0]
print("Extracting:", first_wav)

dest = pathlib.Path("test_extract.wav")
with zf.open(first_wav) as src, open(dest, "wb") as dst:
    data = src.read()
    dst.write(data)

print(f"Extracted {len(data)} bytes to {dest.name}")
# Check with ffprobe
import subprocess, json
info = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(dest)], stdout=subprocess.PIPE, text=True)
s = json.loads(info.stdout)["streams"][0]
print(f"WAV Info: {s['sample_rate']}Hz, {s['channels']}ch, {s['codec_name']}, dur={s.get('duration', 'N/A')}s")
dest.unlink()
