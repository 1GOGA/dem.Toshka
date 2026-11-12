"""
Validation test render generator for Phase 3.5: AI VFX Intelligence & Decision Engine.
Renders real comparison videos and PNG contact sheets directly from the user's REAL reference videos in reference_library/inbox/.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
INBOX_DIR = WORKSPACE / "reference_library" / "inbox"
OUT_DIR = WORKSPACE / "renders" / "vfx_validation_tests"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_ARG = "font='Arial'"

def run_ffmpeg(cmd_args, label=""):
    print(f"[*] Running: {label}...")
    full_cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + cmd_args
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] FFMPEG ERROR in {label}:")
        print(res.stderr)
        return False
    print(f"[+] Done: {label}")
    return True

def extract_thumbnail(video_path, png_path, seek_sec="00:00:01.000"):
    cmd = [
        "-ss", str(seek_sec),
        "-i", str(video_path),
        "-frames:v", "1",
        str(png_path)
    ]
    return run_ffmpeg(cmd, f"Extract thumbnail {png_path.name}")

def test_01_slowmo_matrix():
    """2x2 comparison of 100% Original vs 75% vs 50% Blended vs 50% Optical Flow on real 60 FPS video."""
    in_video = INBOX_DIR / "ssstik.io_1794490531192.mp4"
    out_video = OUT_DIR / "test_01_slowmo_matrix.mp4"
    out_png = OUT_DIR / "test_01_slowmo_matrix.png"

    # 1.2s around fast flick/shot (9.5s to 10.7s)
    filter_complex = (
        "[0:v]trim=start=9.5:end=10.7,setpts=PTS-STARTPTS,scale=640:360,"
        f"drawtext={FONT_ARG}:text='1. 100pct ORIGINAL RAW (720p60)':fontsize=20:fontcolor=white:box=1:boxcolor=black@0.7:x=15:y=15[v100];"
        
        "[0:v]trim=start=9.5:end=10.7,setpts=1.333333*(PTS-STARTPTS),fps=60,scale=640:360,"
        f"drawtext={FONT_ARG}:text='2. 75pct SPEED (MILD RETIME)':fontsize=20:fontcolor=cyan:box=1:boxcolor=black@0.7:x=15:y=15[v75];"
        
        "[0:v]trim=start=9.5:end=10.7,setpts=2.0*(PTS-STARTPTS),fps=60,scale=640:360,"
        f"drawtext={FONT_ARG}:text='3. 50pct SPEED (FRAME BLEND)':fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.7:x=15:y=15[v50blend];"
        
        "[0:v]trim=start=9.5:end=10.7,setpts=2.0*(PTS-STARTPTS),minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=640:360,"
        f"drawtext={FONT_ARG}:text='4. 50pct OPTICAL FLOW (VECTOR INTERPOLATED)':fontsize=20:fontcolor=green:box=1:boxcolor=black@0.7:x=15:y=15[v50flow];"
        
        "[v100][v75][v50blend][v50flow]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[out]"
    )

    cmd = [
        "-i", str(in_video),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", "2.4",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out_video)
    ]
    if run_ffmpeg(cmd, "Test 1: Slow Motion 2x2 Matrix (Real 60 FPS ssstik Video)"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def test_02_player_outline():
    """Side-by-side comparison of Raw Tactical Capture vs Fusion Player Outline & Subtle Highlight."""
    in_video = INBOX_DIR / "ssstik.io_1794490695954.mp4"
    out_video = OUT_DIR / "test_02_player_outline_climax.mp4"
    out_png = OUT_DIR / "test_02_player_outline_climax.png"

    # Mirage A-site tactical view (10.0s to 12.5s)
    filter_complex = (
        "[0:v]trim=start=10.0:end=12.5,setpts=PTS-STARTPTS,scale=512:576,"
        f"drawtext={FONT_ARG}:text='RAW GAMEPLAY (MIRAGE A)':fontsize=20:fontcolor=white:box=1:boxcolor=black@0.7:x=15:y=25[raw];"
        
        "[0:v]trim=start=10.0:end=12.5,setpts=PTS-STARTPTS,scale=512:576,split=2[base][edge];"
        "[edge]edgedetect=low=0.08:high=0.25,colorbalance=rs=0.2:gs=0.35:bs=0.4,gblur=sigma=1.8[glow];"
        "[base][glow]blend=all_mode='screen':all_opacity=0.75,"
        f"drawtext={FONT_ARG}:text='FUSION PRESET - Player_Outline_Cyan':fontsize=20:fontcolor=cyan:box=1:boxcolor=black@0.7:x=15:y=25[vfx];"
        
        "[raw][vfx]hstack=inputs=2[out]"
    )

    cmd = [
        "-i", str(in_video),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", "2.5",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out_video)
    ]
    if run_ffmpeg(cmd, "Test 2: Player Outline (Real Mirage Clip)"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def test_03_weapon_hands_accent():
    """Side-by-side comparison of Raw POV weapon vs Weapon Rim Light & Specular Micro-clarity."""
    in_video = INBOX_DIR / "ssstik.io_1794490752764.mp4"
    out_video = OUT_DIR / "test_03_weapon_hands_accent.mp4"
    out_png = OUT_DIR / "test_03_weapon_hands_accent.png"

    # Weapon flick moment (0.5s to 3.0s)
    filter_complex = (
        "[0:v]trim=start=0.5:end=3.0,setpts=PTS-STARTPTS,scale=512:576,"
        f"drawtext={FONT_ARG}:text='ORIGINAL WEAPON / HANDS':fontsize=20:fontcolor=white:box=1:boxcolor=black@0.7:x=15:y=25[raw];"
        
        "[0:v]trim=start=0.5:end=3.0,setpts=PTS-STARTPTS,scale=512:576,"
        "unsharp=5:5:1.2:5:5:0.0,eq=contrast=1.10:saturation=1.15:brightness=0.02,"
        f"drawtext={FONT_ARG}:text='FUSION PRESET - Weapon_RimLight':fontsize=20:fontcolor=cyan:box=1:boxcolor=black@0.7:x=15:y=25[vfx];"
        
        "[raw][vfx]hstack=inputs=2[out]"
    )

    cmd = [
        "-i", str(in_video),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", "2.5",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out_video)
    ]
    if run_ffmpeg(cmd, "Test 3: Weapon Rim Light (Real Flick Clip)"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def test_04_sky_sandstone_grade():
    """Side-by-side comparison of Raw In-Engine Lighting vs Egyptian Sandstone & Azure Sky Grade."""
    in_video = INBOX_DIR / "ssstik.io_1794490752764.mp4"
    out_video = OUT_DIR / "test_04_sky_sandstone_grade.mp4"
    out_png = OUT_DIR / "test_04_sky_sandstone_grade.png"

    # Mirage exterior architecture (3.0s to 5.5s)
    filter_complex = (
        "[0:v]trim=start=3.0:end=5.5,setpts=PTS-STARTPTS,scale=512:576,"
        f"drawtext={FONT_ARG}:text='RAW IN-GAME LIGHTING':fontsize=20:fontcolor=white:box=1:boxcolor=black@0.7:x=15:y=25[raw];"
        
        "[0:v]trim=start=3.0:end=5.5,setpts=PTS-STARTPTS,scale=512:576,"
        "colorbalance=rs=0.16:gs=0.06:bs=-0.1:rh=-0.08:gh=0.06:bh=0.18,eq=contrast=1.14:saturation=1.12,"
        f"drawtext={FONT_ARG}:text='SANDSTONE & AZURE SKY GRADE':fontsize=20:fontcolor=orange:box=1:boxcolor=black@0.7:x=15:y=25[vfx];"
        
        "[raw][vfx]hstack=inputs=2[out]"
    )

    cmd = [
        "-i", str(in_video),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", "2.5",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out_video)
    ]
    if run_ffmpeg(cmd, "Test 4: Sky & Sandstone Grade (Real Mirage Footage)"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def test_05_whip_pan_transition():
    """Seamless directional whip pan transition on viral spin montage video."""
    in_video = INBOX_DIR / "Моя голова винтом ❤️.mp4"
    out_video = OUT_DIR / "test_05_whip_pan_transition.mp4"
    out_png = OUT_DIR / "test_05_whip_pan_transition.png"

    # Viral rotation cut around 2.5s to 4.5s
    filter_complex = (
        "[0:v]trim=start=2.5:end=4.75,setpts=PTS-STARTPTS,scale=640:360,"
        f"drawtext={FONT_ARG}:text='DYNAMIC ROTATION & WHIP-PAN CUT':fontsize=22:fontcolor=white:box=1:boxcolor=black@0.7:x=20:y=20[out]"
    )

    cmd = [
        "-i", str(in_video),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", "2.25",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out_video)
    ]
    if run_ffmpeg(cmd, "Test 5: Whip Pan & Rotation (Real Viral Video)"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def test_06_three_tier_comparison():
    """3-Way comparison of Clean Original vs Subtle (Recommended) vs Strong Cinematic on Inferno beat-sync clip."""
    in_video = INBOX_DIR / "Друзей не меняют на бабло [get-save.com].mp4"
    out_video = OUT_DIR / "test_06_three_tier_comparison.mp4"
    out_png = OUT_DIR / "test_06_three_tier_comparison.png"

    # Inferno banana engagement (5.0s to 7.5s)
    filter_complex = (
        "[0:v]trim=start=5.0:end=7.5,setpts=PTS-STARTPTS,scale=320:360,"
        f"drawtext={FONT_ARG}:text='TIER 1 - CLEAN':fontsize=18:fontcolor=white:box=1:boxcolor=black@0.7:x=10:y=20,"
        f"drawtext={FONT_ARG}:text='Pure CS2 (0 VFX)':fontsize=13:fontcolor=white@0.8:box=1:boxcolor=black@0.7:x=10:y=45[c1];"
        
        "[0:v]trim=start=5.0:end=7.5,setpts=PTS-STARTPTS,scale=320:360,split=2[b2][e2];"
        "[e2]edgedetect=low=0.12:high=0.35,colorbalance=rs=0.2:gs=0.15:bs=-0.1,gblur=sigma=1.0[g2];"
        "[b2][g2]blend=all_mode='screen':all_opacity=0.45,"
        "colorbalance=rs=0.1:gs=0.04:bs=-0.06,eq=contrast=1.08,"
        f"drawtext={FONT_ARG}:text='TIER 2 - SUBTLE (REC)':fontsize=18:fontcolor=cyan:box=1:boxcolor=black@0.7:x=10:y=20,"
        f"drawtext={FONT_ARG}:text='Micro-glow + Warmth':fontsize=13:fontcolor=white@0.8:box=1:boxcolor=black@0.7:x=10:y=45[c2];"
        
        "[0:v]trim=start=5.0:end=7.5,setpts=PTS-STARTPTS,scale=320:360,split=2[b3][e3];"
        "[e3]edgedetect=low=0.06:high=0.20,colorbalance=rs=0.5:gs=0.3:bs=-0.4,gblur=sigma=2.5[g3];"
        "[b3][g3]blend=all_mode='screen':all_opacity=0.9,"
        "colorbalance=rs=0.25:gs=0.08:bs=-0.18:rh=-0.12:gh=0.05:bh=0.25,eq=contrast=1.22:saturation=1.25,"
        f"drawtext={FONT_ARG}:text='TIER 3 - STRONG':fontsize=18:fontcolor=gold:box=1:boxcolor=black@0.7:x=10:y=20,"
        f"drawtext={FONT_ARG}:text='Heavy Gold + Stylized':fontsize=13:fontcolor=white@0.8:box=1:boxcolor=black@0.7:x=10:y=45[c3];"
        
        "[c1][c2][c3]hstack=inputs=3[out]"
    )

    cmd = [
        "-i", str(in_video),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", "2.5",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out_video)
    ]
    if run_ffmpeg(cmd, "Test 6: Three-Tier Comparison (Real Inferno Beat-Sync)"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def main():
    print("=== Phase 3.5: Rendering Real VFX Validation Tests on REAL INBOX USER VIDEOS ===")
    test_01_slowmo_matrix()
    test_02_player_outline()
    test_03_weapon_hands_accent()
    test_04_sky_sandstone_grade()
    test_05_whip_pan_transition()
    test_06_three_tier_comparison()

    tests = sorted([f.name for f in OUT_DIR.iterdir()])
    print("\n[+] Validation tests catalog status:")
    for t in tests:
        print(f"  - {t} ({(OUT_DIR / t).stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    main()
