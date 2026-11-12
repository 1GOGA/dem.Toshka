from PIL import Image
import numpy as np
from pathlib import Path

frames_dir = Path("renders/vfx_validation_tests/shoulder_frames")

for p in sorted(frames_dir.glob("shoulder_*.jpg")):
    img = Image.open(p)
    w, h = img.size
    arr = np.array(img)
    mean_val = arr.mean()
    print(f"{p.name}: size={w}x{h}, mean_val={mean_val:.1f}")
