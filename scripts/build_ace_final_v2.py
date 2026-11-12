import json
import os
import pathlib
import subprocess
import time

OUT_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TAKES_DIR = pathlib.Path("renders/cinematic_studio_phase3/takes")
OVERLAYS_DIR = OUT_DIR / "overlays"
COLOR_DIR = OUT_DIR / "color"
AUDIO_DIR = OUT_DIR / "audio"

# Input Takes
TAKE_SHOULDER = TAKES_DIR / "shot_anubis_ace_r19_02_shoulder_approach.mp4"
TAKE_HERO = TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4"
TAKE_VICTIM = TAKES_DIR / "shot_anubis_ace_r19_03_victim_reaction.mp4"
TAKE_ORBIT = TAKES_DIR / "shot_anubis_ace_r19_04_climax_orbit.mp4"

LUT_PATH = COLOR_DIR / "egyptian_sandstone_cinematic.cube"
AUDIO_MASTER = AUDIO_DIR / "audio_master_5track.wav"

def assemble_master_16x9(output_path, preview=False):
    print(f"\n--- Assembling 16:9 {'Preview' if preview else 'Master'} -> {output_path} ---")
    t0 = time.time()
    
    # We build the multi-clip transition pipeline
    # Clip 1: Shoulder (0.0 to 2.5s) -> 2.5s
    # Clip 2: Hero POV pt1 (0.0 to 9.2s) -> 9.2s
    # Clip 3: Victim POV (0.0 to 1.4s) -> 1.4s
    # Clip 4: Hero POV pt2 (10.6 to 13.0s) -> 2.4s
    # Clip 5: Climax Orbit (0.0 to 3.0s) -> 3.0s
    
    # Transitions:
    # xfade 1: Clip 1 + Clip 2 (slideleft, offset 2.25s, dur 0.25s) -> len = 2.5 + 9.2 - 0.25 = 11.45s
    # xfade 2: + Clip 3 (zoomin, offset 11.20s, dur 0.25s) -> len = 11.45 + 1.4 - 0.25 = 12.60s
    # xfade 3: + Clip 4 (zoomin, offset 12.40s, dur 0.20s) -> len = 12.60 + 2.4 - 0.20 = 14.80s
    # xfade 4: + Clip 5 (smoothleft, offset 14.45s, dur 0.35s) -> len = 14.80 + 3.0 - 0.35 = 17.45s
    # Wait, let's tune the clip durations so final length is exactly 18.5s!
    # Let:
    # c1 = 2.6s
    # c2 = 9.5s
    # c3 = 1.6s
    # c4 = 2.6s
    # c5 = 3.25s
    # Total overlaps = 0.25 + 0.25 + 0.20 + 0.35 = 1.05s
    # 2.6 + 9.5 + 1.6 + 2.6 + 3.25 - 1.05 = 18.50s! Perfect!
    
    lut_fwd = str(LUT_PATH).replace("\\", "/")
    
    # Inputs list:
    # 0: Shoulder
    # 1: Hero POV
    # 2: Victim Reaction
    # 3: Climax Orbit
    # 4: intro_card
    # 5: badge 1
    # 6: badge 2
    # 7: badge 3
    # 8: badge 4
    # 9: badge 5
    # 10: ace_card
    # 11: audio_master_5track.wav
    
    filter_complex = f"""
    [0:v]trim=start=0.0:end=2.6,setpts=PTS-STARTPTS,fps=60[c1];
    [1:v]trim=start=0.0:end=9.5,setpts=PTS-STARTPTS,fps=60[c2];
    [2:v]trim=start=0.0:end=1.6,setpts=PTS-STARTPTS,fps=60[c3];
    [1:v]trim=start=10.4:end=13.0,setpts=PTS-STARTPTS,fps=60[c4];
    [3:v]trim=start=0.0:end=3.25,setpts=PTS-STARTPTS,fps=60[c5];

    [c1][c2]xfade=transition=slideleft:duration=0.25:offset=2.35[x1];
    [x1][c3]xfade=transition=zoomin:duration=0.25:offset=11.35[x2];
    [x2][c4]xfade=transition=zoomin:duration=0.20:offset=12.45[x3];
    [x3][c5]xfade=transition=smoothleft:duration=0.35:offset=14.65[base_video];

    [base_video]lut3d='{lut_fwd}',eq=brightness=0.35:contrast=1.3:enable='between(t,12.38,12.45)'[graded];

    [graded][4:v]overlay=0:0:enable='between(t,0.3,2.2)'[v_intro];
    [v_intro][5:v]overlay=0:0:enable='between(t,8.18,10.72)'[v_k1];
    [v_k1][6:v]overlay=0:0:enable='between(t,10.72,12.41)'[v_k2];
    [v_k2][7:v]overlay=0:0:enable='between(t,12.41,13.25)'[v_k3];
    [v_k3][8:v]overlay=0:0:enable='between(t,13.25,15.79)'[v_k4];
    [v_k4][9:v]overlay=0:0:enable='between(t,15.79,18.50)'[v_k5];
    [v_k5][10:v]overlay=0:0:enable='between(t,16.00,18.50)'[v_ace];

    [v_ace]fade=t=out:st=17.5:d=1.0[v_final]
    """

    cmd = [
        "ffmpeg", "-y",
        "-i", str(TAKE_SHOULDER),
        "-i", str(TAKE_HERO),
        "-i", str(TAKE_VICTIM),
        "-i", str(TAKE_ORBIT),
        "-i", str(OVERLAYS_DIR / "intro_card_16x9.png"),
        "-i", str(OVERLAYS_DIR / "badge_16x9_kill_1.png"),
        "-i", str(OVERLAYS_DIR / "badge_16x9_kill_2.png"),
        "-i", str(OVERLAYS_DIR / "badge_16x9_kill_3.png"),
        "-i", str(OVERLAYS_DIR / "badge_16x9_kill_4.png"),
        "-i", str(OVERLAYS_DIR / "badge_16x9_kill_5.png"),
        "-i", str(OVERLAYS_DIR / "ace_card_16x9.png"),
        "-i", str(AUDIO_MASTER),
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "11:a",
        "-t", "18.5",
        "-pix_fmt", "yuv420p"
    ]
    
    if preview:
        cmd += ["-c:v", "h264_amf", "-quality", "speed", "-b:v", "8M", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-c:v", "h264_amf", "-quality", "quality", "-b:v", "24M", "-c:a", "aac", "-b:a", "320k"]
        
    cmd.append(str(output_path))
    
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr[-800:])
        # Fallback to libx264 if AMF fails
        print("Falling back to libx264...")
        cmd_fallback = cmd.copy()
        idx_cv = cmd_fallback.index("-c:v")
        cmd_fallback[idx_cv+1] = "libx264"
        cmd_fallback[idx_cv+2] = "-preset"
        cmd_fallback[idx_cv+3] = "fast"
        res = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed: {res.stderr[-500:]}")
            
    elapsed = time.time() - t0
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Render completed in {elapsed:.2f}s, size: {size_mb:.2f} MB")

def assemble_tiktok_9x16(output_path):
    print(f"\n--- Assembling 9:16 TikTok Vertical -> {output_path} ---")
    t0 = time.time()
    
    lut_fwd = str(LUT_PATH).replace("\\", "/")
    
    # 9:16 Vertical:
    # 1. Base video assemble
    # 2. Crop 608x1080 centered on crosshair (x=656), scale to 1080x1920
    # 3. Apply color grade
    # 4. Impact flash on headshot
    # 5. TikTok vertical badges & cards
    filter_complex = f"""
    [0:v]trim=start=0.0:end=2.6,setpts=PTS-STARTPTS,fps=60[c1];
    [1:v]trim=start=0.0:end=9.5,setpts=PTS-STARTPTS,fps=60[c2];
    [2:v]trim=start=0.0:end=1.6,setpts=PTS-STARTPTS,fps=60[c3];
    [1:v]trim=start=10.4:end=13.0,setpts=PTS-STARTPTS,fps=60[c4];
    [3:v]trim=start=0.0:end=3.25,setpts=PTS-STARTPTS,fps=60[c5];

    [c1][c2]xfade=transition=slideleft:duration=0.25:offset=2.35[x1];
    [x1][c3]xfade=transition=zoomin:duration=0.25:offset=11.35[x2];
    [x2][c4]xfade=transition=zoomin:duration=0.20:offset=12.45[x3];
    [x3][c5]xfade=transition=smoothleft:duration=0.35:offset=14.65[base_video];

    [base_video]crop=608:1080:656:0,scale=1080:1920:flags=lanczos,lut3d='{lut_fwd}',eq=brightness=0.35:contrast=1.3:enable='between(t,12.38,12.45)'[graded_vertical];

    [graded_vertical][4:v]overlay=0:0:enable='between(t,0.3,2.2)'[v_intro];
    [v_intro][5:v]overlay=0:0:enable='between(t,8.18,10.72)'[v_k1];
    [v_k1][6:v]overlay=0:0:enable='between(t,10.72,12.41)'[v_k2];
    [v_k2][7:v]overlay=0:0:enable='between(t,12.41,13.25)'[v_k3];
    [v_k3][8:v]overlay=0:0:enable='between(t,13.25,15.79)'[v_k4];
    [v_k4][9:v]overlay=0:0:enable='between(t,15.79,18.50)'[v_k5];
    [v_k5][10:v]overlay=0:0:enable='between(t,16.00,18.50)'[v_ace];

    [v_ace]fade=t=out:st=17.5:d=1.0[v_final]
    """

    cmd = [
        "ffmpeg", "-y",
        "-i", str(TAKE_SHOULDER),
        "-i", str(TAKE_HERO),
        "-i", str(TAKE_VICTIM),
        "-i", str(TAKE_ORBIT),
        "-i", str(OVERLAYS_DIR / "intro_card_tiktok.png"),
        "-i", str(OVERLAYS_DIR / "badge_tiktok_kill_1.png"),
        "-i", str(OVERLAYS_DIR / "badge_tiktok_kill_2.png"),
        "-i", str(OVERLAYS_DIR / "badge_tiktok_kill_3.png"),
        "-i", str(OVERLAYS_DIR / "badge_tiktok_kill_4.png"),
        "-i", str(OVERLAYS_DIR / "badge_tiktok_kill_5.png"),
        "-i", str(OVERLAYS_DIR / "ace_card_tiktok.png"),
        "-i", str(AUDIO_MASTER),
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "11:a",
        "-t", "18.5",
        "-pix_fmt", "yuv420p",
        "-c:v", "h264_amf", "-quality", "quality", "-b:v", "20M",
        "-c:a", "aac", "-b:a", "320k",
        str(output_path)
    ]
    
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr[-800:])
        print("Falling back to libx264...")
        cmd_fallback = cmd.copy()
        idx_cv = cmd_fallback.index("-c:v")
        cmd_fallback[idx_cv+1] = "libx264"
        cmd_fallback[idx_cv+2] = "-preset"
        cmd_fallback[idx_cv+3] = "fast"
        res = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg vertical render failed: {res.stderr[-500:]}")
            
    elapsed = time.time() - t0
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Vertical TikTok render completed in {elapsed:.2f}s, size: {size_mb:.2f} MB")

if __name__ == "__main__":
    preview_mp4 = OUT_DIR / "ACE_FINAL_V2_PREVIEW.mp4"
    master_mp4 = OUT_DIR / "ACE_FINAL_V2_MASTER.mp4"
    tiktok_mp4 = OUT_DIR / "ACE_FINAL_V2_TIKTOK.mp4"
    
    assemble_master_16x9(preview_mp4, preview=True)
    assemble_master_16x9(master_mp4, preview=False)
    assemble_tiktok_9x16(tiktok_mp4)
    print("\nAll 3 post-production video deliverables rendered successfully!")
