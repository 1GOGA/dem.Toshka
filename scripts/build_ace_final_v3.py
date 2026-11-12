import json
import os
import pathlib
import subprocess
import time

V3_DIR = pathlib.Path("renders/ACE_FINAL_V3_AUDIO_KILLFEED")
V3_DIR.mkdir(parents=True, exist_ok=True)

TAKES_DIR = pathlib.Path("renders/cinematic_studio_phase3/takes")
OVERLAYS_DIR = V3_DIR / "overlays"
COLOR_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/color")
AUDIO_DIR = V3_DIR / "audio"

TAKE_SHOULDER = TAKES_DIR / "shot_anubis_ace_r19_02_shoulder_approach.mp4"
TAKE_HERO = TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4"
TAKE_VICTIM = TAKES_DIR / "shot_anubis_ace_r19_03_victim_reaction.mp4"
TAKE_ORBIT = TAKES_DIR / "shot_anubis_ace_r19_04_climax_orbit.mp4"

LUT_PATH = COLOR_DIR / "egyptian_sandstone_cinematic.cube"
AUDIO_MASTER = AUDIO_DIR / "audio_master_v3.wav"

def assemble_v3_master_16x9(output_path, preview=False):
    print(f"\n--- Assembling Phase 3.2 16:9 {'Preview' if preview else 'Master'} -> {output_path} ---")
    t0 = time.time()
    
    lut_fwd = str(LUT_PATH).replace("\\", "/")
    
    # 5 video clips + xfade transitions:
    # c1: Shoulder (0.0 to 2.35s)
    # c2: Hero POV pt1 (0.0 to 9.35s)
    # c3: Victim POV (0.0 to 1.45s)
    # c4: Hero POV pt2 (10.50 to 13.65s) -> 3.15s
    # c5: Orbit (0.0 to 2.80s)
    # xfade 1: offset 2.15s, dur 0.20s -> len = 2.35 + 9.35 - 0.20 = 11.50s
    # xfade 2: offset 11.35s, dur 0.20s -> len = 11.50 + 1.45 - 0.20 = 12.75s
    # xfade 3: offset 12.60s, dur 0.15s -> len = 12.75 + 3.15 - 0.15 = 15.75s
    # xfade 4: offset 15.50s, dur 0.25s -> len = 15.75 + 2.80 - 0.25 = 18.30s
    # Let's adjust c4 and c5 slightly so total duration is exactly 18.50s:
    # c1 = 2.35s
    # c2 = 9.35s  (xfade1: offset 2.15, dur 0.20 -> ends at 11.50s)
    # c3 = 1.45s  (xfade2: offset 11.30, dur 0.20 -> ends at 12.75s)
    # c4 = 3.35s  (xfade3: offset 12.60, dur 0.15 -> ends at 15.95s)
    # c5 = 2.80s  (xfade4: offset 15.70, dur 0.25 -> ends at 18.50s!)
    
    filter_complex = f"""
    [0:v]trim=start=0.0:end=2.35,setpts=PTS-STARTPTS,fps=60[c1];
    [1:v]trim=start=0.0:end=9.35,setpts=PTS-STARTPTS,fps=60[c2];
    [2:v]trim=start=0.0:end=1.45,setpts=PTS-STARTPTS,fps=60[c3];
    [1:v]trim=start=10.5:end=13.85,setpts=PTS-STARTPTS,fps=60[c4];
    [3:v]trim=start=0.0:end=2.80,setpts=PTS-STARTPTS,fps=60[c5];

    [c1][c2]xfade=transition=slideleft:duration=0.20:offset=2.15[x1];
    [x1][c3]xfade=transition=zoomin:duration=0.20:offset=11.30[x2];
    [x2][c4]xfade=transition=zoomin:duration=0.15:offset=12.60[x3];
    [x3][c5]xfade=transition=smoothleft:duration=0.25:offset=15.70[base_video];

    [base_video]lut3d='{lut_fwd}',eq=brightness=0.30:contrast=1.25:enable='between(t,12.18,12.25)+between(t,15.52,15.60)'[graded];

    [graded][4:v]overlay=0:0:enable='between(t,0.3,2.0)'[v_intro];
    [v_intro][5:v]overlay=0:0:enable='between(t,7.83,10.45)'[v_s1];
    [v_s1][6:v]overlay=0:0:enable='between(t,10.45,12.20)'[v_s2];
    [v_s2][7:v]overlay=0:0:enable='between(t,12.20,13.00)'[v_s3];
    [v_s3][8:v]overlay=0:0:enable='between(t,13.00,15.54)'[v_s4];
    [v_s4][9:v]overlay=0:0:enable='between(t,15.54,18.50)'[v_s5];
    [v_s5][10:v]overlay=0:0:enable='between(t,15.80,18.50)'[v_ace];

    [v_ace]fade=t=out:st=17.5:d=1.0[v_final]
    """

    cmd = [
        "ffmpeg", "-y",
        "-i", str(TAKE_SHOULDER),
        "-i", str(TAKE_HERO),
        "-i", str(TAKE_VICTIM),
        "-i", str(TAKE_ORBIT),
        "-i", str(OVERLAYS_DIR / "intro_card_16x9.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_16x9_state_1_kill1.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_16x9_state_2_kill1_2.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_16x9_state_3_kill1_2_3.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_16x9_state_4_kill2_3_4.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_16x9_state_5_kill3_4_5.png"),
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
        print("FFmpeg AMF error, falling back to libx264:", res.stderr[-400:])
        cmd_fb = cmd.copy()
        idx_cv = cmd_fb.index("-c:v")
        cmd_fb[idx_cv+1] = "libx264"
        cmd_fb[idx_cv+2] = "-preset"
        cmd_fb[idx_cv+3] = "fast"
        res = subprocess.run(cmd_fb, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed: {res.stderr[-500:]}")
            
    elapsed = time.time() - t0
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Master render completed in {elapsed:.2f}s, size: {size_mb:.2f} MB")

def assemble_v3_tiktok_9x16(output_path):
    print(f"\n--- Assembling Phase 3.2 9:16 TikTok Vertical -> {output_path} ---")
    t0 = time.time()
    
    lut_fwd = str(LUT_PATH).replace("\\", "/")
    
    filter_complex = f"""
    [0:v]trim=start=0.0:end=2.35,setpts=PTS-STARTPTS,fps=60[c1];
    [1:v]trim=start=0.0:end=9.35,setpts=PTS-STARTPTS,fps=60[c2];
    [2:v]trim=start=0.0:end=1.45,setpts=PTS-STARTPTS,fps=60[c3];
    [1:v]trim=start=10.5:end=13.85,setpts=PTS-STARTPTS,fps=60[c4];
    [3:v]trim=start=0.0:end=2.80,setpts=PTS-STARTPTS,fps=60[c5];

    [c1][c2]xfade=transition=slideleft:duration=0.20:offset=2.15[x1];
    [x1][c3]xfade=transition=zoomin:duration=0.20:offset=11.30[x2];
    [x2][c4]xfade=transition=zoomin:duration=0.15:offset=12.60[x3];
    [x3][c5]xfade=transition=smoothleft:duration=0.25:offset=15.70[base_video];

    [base_video]crop=608:1080:656:0,scale=1080:1920:flags=lanczos,lut3d='{lut_fwd}',eq=brightness=0.30:contrast=1.25:enable='between(t,12.18,12.25)+between(t,15.52,15.60)'[graded_vertical];

    [graded_vertical][4:v]overlay=0:0:enable='between(t,0.3,2.0)'[v_intro];
    [v_intro][5:v]overlay=0:0:enable='between(t,7.83,10.45)'[v_s1];
    [v_s1][6:v]overlay=0:0:enable='between(t,10.45,12.20)'[v_s2];
    [v_s2][7:v]overlay=0:0:enable='between(t,12.20,13.00)'[v_s3];
    [v_s3][8:v]overlay=0:0:enable='between(t,13.00,15.54)'[v_s4];
    [v_s4][9:v]overlay=0:0:enable='between(t,15.54,18.50)'[v_s5];
    [v_s5][10:v]overlay=0:0:enable='between(t,15.80,18.50)'[v_ace];

    [v_ace]fade=t=out:st=17.5:d=1.0[v_final]
    """

    cmd = [
        "ffmpeg", "-y",
        "-i", str(TAKE_SHOULDER),
        "-i", str(TAKE_HERO),
        "-i", str(TAKE_VICTIM),
        "-i", str(TAKE_ORBIT),
        "-i", str(OVERLAYS_DIR / "intro_card_tiktok.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_tiktok_state_1_kill1.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_tiktok_state_2_kill1_2.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_tiktok_state_3_kill1_2_3.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_tiktok_state_4_kill2_3_4.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_tiktok_state_5_kill3_4_5.png"),
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
        print("FFmpeg vertical AMF error, falling back to libx264:", res.stderr[-400:])
        cmd_fb = cmd.copy()
        idx_cv = cmd_fb.index("-c:v")
        cmd_fb[idx_cv+1] = "libx264"
        cmd_fb[idx_cv+2] = "-preset"
        cmd_fb[idx_cv+3] = "fast"
        res = subprocess.run(cmd_fb, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg vertical render failed: {res.stderr[-500:]}")
            
    elapsed = time.time() - t0
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Vertical TikTok render completed in {elapsed:.2f}s, size: {size_mb:.2f} MB")

if __name__ == "__main__":
    preview_mp4 = V3_DIR / "ACE_FINAL_V3_PREVIEW.mp4"
    master_mp4 = V3_DIR / "ACE_FINAL_V3_MASTER.mp4"
    tiktok_mp4 = V3_DIR / "ACE_FINAL_V3_TIKTOK.mp4"
    
    assemble_v3_master_16x9(preview_mp4, preview=True)
    assemble_v3_master_16x9(master_mp4, preview=False)
    assemble_v3_tiktok_9x16(tiktok_mp4)
    print("\nPhase 3.2: All 3 Master Deliverables Rendered Successfully!")
