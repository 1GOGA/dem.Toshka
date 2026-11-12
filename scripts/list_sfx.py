from pathlib import Path

sfx_dir = Path("renders/ACE_FINAL_V3_AUDIO_KILLFEED/sfx_library")
wavs = list(sfx_dir.rglob("*.wav"))
print(f"Found {len(wavs)} wav files in sfx_library:")
for w in wavs:
    print(f" - {w.relative_to(sfx_dir)} ({w.stat().st_size} bytes)")
