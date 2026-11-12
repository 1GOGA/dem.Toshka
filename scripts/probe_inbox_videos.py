import json
import subprocess
from pathlib import Path

inbox = Path("reference_library/inbox")
for f in sorted(inbox.glob("*.mp4")):
    res = subprocess.run([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration,codec_name",
        "-of", "json", str(f)
    ], capture_output=True, text=True)
    try:
        info = json.loads(res.stdout)
        stream = info.get("streams", [{}])[0]
        print(f"[{f.name}]")
        print(f"  Width: {stream.get('width')}, Height: {stream.get('height')}, FPS: {stream.get('r_frame_rate')}, Duration: {stream.get('duration')}s, Codec: {stream.get('codec_name')}")
    except Exception as e:
        print(f"Error reading {f.name}: {e}")
