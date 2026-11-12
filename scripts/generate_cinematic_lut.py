import math
import pathlib
import numpy as np

LUT_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/color")
LUT_DIR.mkdir(parents=True, exist_ok=True)
lut_path = LUT_DIR / "egyptian_sandstone_cinematic.cube"

# 33x33x33 3D LUT
N = 33

def s_curve(x):
    # Smooth cinematic contrast S-curve
    # Using smoothstep variant: 3x^2 - 2x^3 blended with linear
    s = 3.0 * (x ** 2) - 2.0 * (x ** 3)
    return 0.25 * x + 0.75 * s

def apply_grade(r, g, b):
    # 1. Base S-curve contrast
    rc = s_curve(r)
    gc = s_curve(g)
    bc = s_curve(b)
    
    # Luminance
    lum = 0.2126 * rc + 0.7152 * gc + 0.0722 * bc
    
    # 2. Split Toning:
    # Shadow factor: 1.0 at black, 0.0 at midtone (0.5)
    shadow_factor = max(0.0, 1.0 - (lum / 0.45)) ** 1.5
    # Highlight factor: 0.0 at midtone (0.5), 1.0 at white
    highlight_factor = max(0.0, (lum - 0.45) / 0.55) ** 1.3
    # Midtone factor: peaking around 0.5
    midtone_factor = math.sin(lum * math.pi) ** 1.2
    
    # Shadow Teal/Slate Lift (subtle cyan-blue lift in shadows)
    rc += shadow_factor * (-0.03)
    gc += shadow_factor * (+0.01)
    bc += shadow_factor * (+0.04)
    
    # Midtone Warm Egyptian Amber / Sandstone (sunlit stone look)
    rc += midtone_factor * (+0.065)
    gc += midtone_factor * (+0.025)
    bc += midtone_factor * (-0.045)
    
    # Highlight Warm Golden Soft Roll-off
    rc += highlight_factor * (+0.035)
    gc += highlight_factor * (+0.020)
    bc += highlight_factor * (-0.015)
    
    # 3. Controlled Vibrance / Saturation (+12%)
    new_lum = 0.2126 * rc + 0.7152 * gc + 0.0722 * bc
    sat_factor = 1.12
    # slight desaturation in extreme shadows to keep blacks clean
    if lum < 0.15:
        sat_factor = 0.95 + (lum / 0.15) * 0.17
        
    rf = new_lum + (rc - new_lum) * sat_factor
    gf = new_lum + (gc - new_lum) * sat_factor
    bf = new_lum + (bc - new_lum) * sat_factor
    
    # Soft clamp 0..1
    rf = max(0.0, min(1.0, rf))
    gf = max(0.0, min(1.0, gf))
    bf = max(0.0, min(1.0, bf))
    return rf, gf, bf

# Write .cube file
lines = [
    '# Title: CS2 Cinematic - Egyptian Sandstone (Anubis Warm Cinema Look)',
    '# Created for dem.Toshka Cinematic Studio Phase 3.1',
    '# LUT size: 33x33x33',
    'LUT_3D_SIZE 33',
    'DOMAIN_MIN 0.0 0.0 0.0',
    'DOMAIN_MAX 1.0 1.0 1.0',
]

for b_idx in range(N):
    b_val = b_idx / (N - 1)
    for g_idx in range(N):
        g_val = g_idx / (N - 1)
        for r_idx in range(N):
            r_val = r_idx / (N - 1)
            gr_r, gr_g, gr_b = apply_grade(r_val, g_val, b_val)
            lines.append(f"{gr_r:.6f} {gr_g:.6f} {gr_b:.6f}")

lut_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Generated 3D LUT: {lut_path} ({len(lines)} lines)")
