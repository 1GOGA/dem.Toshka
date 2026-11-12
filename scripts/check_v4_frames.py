from PIL import Image
import numpy as np
from pathlib import Path

v4_dir = Path("renders/vfx_validation_tests/v4_cut_verification")

for p in sorted(v4_dir.glob("*.jpg")):
    img = Image.open(p)
    arr = np.array(img)
    # Check center (540, 960)
    c_patch = arr[400:680, 750:1170]
    print(f"{p.name}: size={img.size}, mean RGB={c_patch.mean(axis=(0, 1)).astype(int)}")
