"""
Validation test render generator for Phase 3.5: AI VFX Intelligence & Decision Engine.
Renders real comparison videos and PNG contact sheets from Anubis ACE footage into renders/vfx_validation_tests/.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
TAKES_DIR = WORKSPACE / "renders" / "cinematic_studio_phase3" / "takes"
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
    """2x2 comparison of 100% Original vs 75% vs 50% Blended vs 50% Optical Flow."""
    in_video = TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4"
    out_video = OUT_DIR / "test_01_slowmo_matrix.mp4"
    out_png = OUT_DIR / "test_01_slowmo_matrix.png"

    filter_complex = (
        "[0:v]trim=start=9.8:end=11.0,setpts=PTS-STARTPTS,scale=960:540,"
        f"drawtext={FONT_ARG}:text='1. 100pct ORIGINAL (60 FPS RAW)':fontsize=24:fontcolor=white:box=1:boxcolor=black@0.7:x=20:y=20[v100];"
        
        "[0:v]trim=start=9.8:end=11.0,setpts=1.333333*(PTS-STARTPTS),fps=60,scale=960:540,"
        f"drawtext={FONT_ARG}:text='2. 75pct SPEED (MILD RETIME - NO WARP)':fontsize=24:fontcolor=cyan:box=1:boxcolor=black@0.7:x=20:y=20[v75];"
        
        "[0:v]trim=start=9.8:end=11.0,setpts=2.0*(PTS-STARTPTS),fps=60,scale=960:540,"
        f"drawtext={FONT_ARG}:text='3. 50pct SPEED (FRAME BLEND)':fontsize=24:fontcolor=yellow:box=1:boxcolor=black@0.7:x=20:y=20[v50blend];"
        
        "[0:v]trim=start=9.8:end=11.0,setpts=2.0*(PTS-STARTPTS),minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=960:540,"
        f"drawtext={FONT_ARG}:text='4. 50pct OPTICAL FLOW (VECTOR INTERPOLATED)':fontsize=24:fontcolor=green:box=1:boxcolor=black@0.7:x=20:y=20[v50flow];"
        
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
    if run_ffmpeg(cmd, "Test 1: Slow Motion 2x2 Matrix"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def test_02_player_outline():
    """Side-by-side comparison of Raw Hero Orbit vs Fusion Player Outline & Gold Climax Bloom."""
    in_video = TAKES_DIR / "shot_anubis_ace_r19_04_climax_orbit.mp4"
    out_video = OUT_DIR / "test_02_player_outline_climax.mp4"
    out_png = OUT_DIR / "test_02_player_outline_climax.png"

    filter_complex = (
        "[0:v]trim=start=0.5:end=3.0,setpts=PTS-STARTPTS,scale=960:1080,"
        f"drawtext={FONT_ARG}:text='RAW IN-GAME CAPTURE':fontsize=28:fontcolor=white:box=1:boxcolor=black@0.7:x=20:y=40[raw];"
        
        "[0:v]trim=start=0.5:end=3.0,setpts=PTS-STARTPTS,scale=960:1080,split=2[base][edge];"
        "[edge]edgedetect=low=0.08:high=0.25,colorbalance=rs=0.4:gs=0.25:bs=-0.3,gblur=sigma=1.8[glow];"
        "[base][glow]blend=all_mode='screen':all_opacity=0.75,"
        f"drawtext={FONT_ARG}:text='FUSION PRESET - Player_Outline_Gold':fontsize=28:fontcolor=gold:box=1:boxcolor=black@0.7:x=20:y=40[vfx];"
        
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
    if run_ffmpeg(cmd, "Test 2: Player Outline Climax"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def test_03_weapon_hands_accent():
    """Side-by-side comparison of Raw POV weapon vs Weapon Rim Light & Specular Micro-clarity."""
    in_video = TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4"
    out_video = OUT_DIR / "test_03_weapon_hands_accent.mp4"
    out_png = OUT_DIR / "test_03_weapon_hands_accent.png"

    filter_complex = (
        "[0:v]trim=start=9.5:end=12.0,setpts=PTS-STARTPTS,scale=960:1080,"
        f"drawtext={FONT_ARG}:text='ORIGINAL WEAPON AND HANDS':fontsize=28:fontcolor=white:box=1:boxcolor=black@0.7:x=20:y=40[raw];"
        
        "[0:v]trim=start=9.5:end=12.0,setpts=PTS-STARTPTS,scale=960:1080,"
        "unsharp=5:5:1.2:5:5:0.0,eq=contrast=1.08:saturation=1.12:brightness=0.02,"
        f"drawtext={FONT_ARG}:text='FUSION PRESET - Weapon_RimLight':fontsize=28:fontcolor=cyan:box=1:boxcolor=black@0.7:x=20:y=40[vfx];"
        
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
    if run_ffmpeg(cmd, "Test 3: Weapon & Hands Accent"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def test_04_sky_sandstone_grade():
    """Side-by-side comparison of Raw In-Engine Lighting vs Egyptian Sandstone & Azure Sky Grade."""
    in_video = TAKES_DIR / "shot_anubis_ace_r19_02_shoulder_approach.mp4"
    out_video = OUT_DIR / "test_04_sky_sandstone_grade.mp4"
    out_png = OUT_DIR / "test_04_sky_sandstone_grade.png"

    filter_complex = (
        "[0:v]trim=start=1.0:end=3.5,setpts=PTS-STARTPTS,scale=960:1080,"
        f"drawtext={FONT_ARG}:text='ENGINE DEFAULT LIGHTING':fontsize=28:fontcolor=white:box=1:boxcolor=black@0.7:x=20:y=40[raw];"
        
        "[0:v]trim=start=1.0:end=3.5,setpts=PTS-STARTPTS,scale=960:1080,"
        "colorbalance=rs=0.15:gs=0.06:bs=-0.1:rh=-0.08:gh=0.06:bh=0.18,eq=contrast=1.12:saturation=1.10,"
        f"drawtext={FONT_ARG}:text='EGYPTIAN SANDSTONE & AZURE SKY':fontsize=28:fontcolor=orange:box=1:boxcolor=black@0.7:x=20:y=40[vfx];"
        
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
    if run_ffmpeg(cmd, "Test 4: Sky & Sandstone Grade"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def test_05_whip_pan_transition():
    """Seamless directional whip pan transition between approach take and POV take."""
    vid_approach = TAKES_DIR / "shot_anubis_ace_r19_02_shoulder_approach.mp4"
    vid_pov = TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4"
    out_video = OUT_DIR / "test_05_whip_pan_transition.mp4"
    out_png = OUT_DIR / "test_05_whip_pan_transition.png"

    filter_complex = (
        "[0:v]trim=start=5.0:end=6.0,setpts=PTS-STARTPTS[c1];"
        "[1:v]trim=start=4.0:end=5.0,setpts=PTS-STARTPTS[c2];"
        "[c1][c2]xfade=transition=slideleft:duration=0.25:offset=0.75,"
        f"drawtext={FONT_ARG}:text='DYNAMIC WHIP-PAN TRANSITION':fontsize=28:fontcolor=white:box=1:boxcolor=black@0.7:x=40:y=40[out]"
    )

    cmd = [
        "-i", str(vid_approach),
        "-i", str(vid_pov),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", "1.75",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out_video)
    ]
    if run_ffmpeg(cmd, "Test 5: Whip Pan Transition"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:00.850")

def test_06_three_tier_comparison():
    """3-Way comparison of Clean Original vs Subtle (Recommended) vs Strong Cinematic."""
    in_video = TAKES_DIR / "shot_anubis_ace_r19_04_climax_orbit.mp4"
    out_video = OUT_DIR / "test_06_three_tier_comparison.mp4"
    out_png = OUT_DIR / "test_06_three_tier_comparison.png"

    filter_complex = (
        "[0:v]trim=start=0.5:end=3.0,setpts=PTS-STARTPTS,scale=640:1080,"
        f"drawtext={FONT_ARG}:text='TIER 1 - CLEAN':fontsize=26:fontcolor=white:box=1:boxcolor=black@0.7:x=20:y=40,"
        f"drawtext={FONT_ARG}:text='Pure CS2 (0 VFX)':fontsize=18:fontcolor=white@0.8:box=1:boxcolor=black@0.7:x=20:y=75[c1];"
        
        "[0:v]trim=start=0.5:end=3.0,setpts=PTS-STARTPTS,scale=640:1080,split=2[b2][e2];"
        "[e2]edgedetect=low=0.12:high=0.35,colorbalance=rs=0.2:gs=0.15:bs=-0.1,gblur=sigma=1.0[g2];"
        "[b2][g2]blend=all_mode='screen':all_opacity=0.45,"
        "colorbalance=rs=0.1:gs=0.04:bs=-0.06,eq=contrast=1.08,"
        f"drawtext={FONT_ARG}:text='TIER 2 - SUBTLE (REC)':fontsize=26:fontcolor=cyan:box=1:boxcolor=black@0.7:x=20:y=40,"
        f"drawtext={FONT_ARG}:text='Micro-glow + Warmth':fontsize=18:fontcolor=white@0.8:box=1:boxcolor=black@0.7:x=20:y=75[c2];"
        
        "[0:v]trim=start=0.5:end=3.0,setpts=PTS-STARTPTS,scale=640:1080,split=2[b3][e3];"
        "[e3]edgedetect=low=0.06:high=0.20,colorbalance=rs=0.5:gs=0.3:bs=-0.4,gblur=sigma=2.5[g3];"
        "[b3][g3]blend=all_mode='screen':all_opacity=0.9,"
        "colorbalance=rs=0.25:gs=0.08:bs=-0.18:rh=-0.12:gh=0.05:bh=0.25,eq=contrast=1.22:saturation=1.25,"
        f"drawtext={FONT_ARG}:text='TIER 3 - STRONG':fontsize=26:fontcolor=gold:box=1:boxcolor=black@0.7:x=20:y=40,"
        f"drawtext={FONT_ARG}:text='Heavy Gold + Stylized':fontsize=18:fontcolor=white@0.8:box=1:boxcolor=black@0.7:x=20:y=75[c3];"
        
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
    if run_ffmpeg(cmd, "Test 6: Three-Tier Comparison"):
        extract_thumbnail(out_video, out_png, seek_sec="00:00:01.000")

def main():
    print("=== Phase 3.5: Rendering Real VFX Validation Tests on Anubis ACE Footage ===")
    if not (OUT_DIR / "test_01_slowmo_matrix.mp4").is_file() or (OUT_DIR / "test_01_slowmo_matrix.mp4").stat().st_size == 0:
        test_01_slowmo_matrix()
    if not (OUT_DIR / "test_02_player_outline_climax.mp4").is_file() or (OUT_DIR / "test_02_player_outline_climax.mp4").stat().st_size == 0:
        test_02_player_outline()
    if not (OUT_DIR / "test_03_weapon_hands_accent.mp4").is_file() or (OUT_DIR / "test_03_weapon_hands_accent.mp4").stat().st_size == 0:
        test_03_weapon_hands_accent()
    if not (OUT_DIR / "test_04_sky_sandstone_grade.mp4").is_file() or (OUT_DIR / "test_04_sky_sandstone_grade.mp4").stat().st_size == 0:
        test_04_sky_sandstone_grade()
    if not (OUT_DIR / "test_05_whip_pan_transition.mp4").is_file() or (OUT_DIR / "test_05_whip_pan_transition.mp4").stat().st_size == 0:
        test_05_whip_pan_transition()
    if not (OUT_DIR / "test_06_three_tier_comparison.mp4").is_file() or (OUT_DIR / "test_06_three_tier_comparison.mp4").stat().st_size == 0:
        test_06_three_tier_comparison()

    tests = sorted([f.name for f in OUT_DIR.iterdir()])
    print("\n[+] Validation tests catalog status:")
    for t in tests:
        print(f"  - {t} ({(OUT_DIR / t).stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    main()
