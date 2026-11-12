from PIL import Image
import numpy as np
from pathlib import Path

frames_dir = Path("renders/vfx_validation_tests/hero_pov_frames")

for p in sorted(frames_dir.glob("frame_*.jpg")):
    img = Image.open(p)
    arr = np.array(img)
    # Check center (pillar is warm yellowish stone, open sky/mid has different tones)
    # In 1920x1080, center is 540, 960
    center_patch = arr[400:600, 800:1120]
    mean_rgb = center_patch.mean(axis=(0, 1))
    # Also check if top-right has any text/hud
    tr_patch = arr[30:80, 1400:1900]
    tr_mean = tr_patch.mean()
    print(f"{p.name}: center mean RGB=({mean_rgb[0]:.1f}, {mean_rgb[1]:.1f}, {mean_rgb[2]:.1f})")
