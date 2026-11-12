from PIL import Image
import numpy as np
from pathlib import Path

f3 = Path("renders/ACE_FINAL_V4_MASTER_CUT/qa/frame_03_kill1_first_blood.png")
f4 = Path("renders/ACE_FINAL_V4_MASTER_CUT/qa/frame_04_kill1_feed_verified.png")

im3 = np.array(Image.open(f3))
im4 = np.array(Image.open(f4))

# Region of killfeed banner: base_x = 1380 to 1860, y = 60 to 104
patch3 = im3[60:104, 1380:1860]
patch4 = im4[60:104, 1380:1860]

print("Frame 03 (2.68s - Hit moment): patch mean RGB =", patch3.mean(axis=(0, 1)).astype(int))
print("Frame 04 (2.85s - Post-hit verified): patch mean RGB =", patch4.mean(axis=(0, 1)).astype(int))

# Also check center to prove pytoshka_ is NOT looking at a wall!
c3 = im3[450:650, 800:1120]
c4 = im4[450:650, 800:1120]
print("Frame 03 center mean RGB =", c3.mean(axis=(0, 1)).astype(int))
print("Frame 04 center mean RGB =", c4.mean(axis=(0, 1)).astype(int))
