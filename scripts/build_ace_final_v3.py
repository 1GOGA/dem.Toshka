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

def assemble_v3_master_16x9(output_path, preview=False, show_killfeed=False):
    mode_str = "Broadcast Killfeed" if show_killfeed else "Pure Cinematic"
    print(f"\n--- Assembling Phase 3.2 16:9 {'Preview' if preview else 'Master'} [{mode_str}] -> {output_path} ---")
    t0 = time.time()
    
    lut_fwd = str(LUT_PATH).replace("\\", "/")
    
    fx_filters = (
        "crop=1600:900:160:90,scale=1920:1080:flags=lanczos,"
        "crop=w='iw*(1-0.04*between(t,7.71,7.85)-0.06*between(t,12.18,12.30)-0.05*between(t,16.48,16.65))':"
        "h='ih*(1-0.04*between(t,7.71,7.85)-0.06*between(t,12.18,12.30)-0.05*between(t,16.48,16.65))':"
        "x='(iw-ow)/2':y='(ih-oh)/2',scale=1920:1080:flags=bicubic,"
        f"lut3d='{lut_fwd}',"
        "eq=brightness=0.25:contrast=1.25:enable='between(t,7.71,7.76)+between(t,10.43,10.48)+between(t,12.18,12.26)+between(t,13.48,13.54)+between(t,16.48,16.58)'"
    )

    if not show_killfeed:
        # PURE CINEMATIC FRAGMOVIE CUT: Clean, no obstructive killfeed badges!
        filter_complex = f"""
        [0:v]trim=start=0.0:end=2.35,setpts=PTS-STARTPTS,fps=60,settb=1/60[c1];
        [1:v]trim=start=5.77:end=12.20,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2a];
        [1:v]trim=start=12.20:end=15.80,setpts=0.25*(PTS-STARTPTS),fps=60,settb=1/60[c2b];
        [1:v]trim=start=15.80:end=17.70,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2c];
        [c2a][c2b][c2c]concat=n=3:v=1:a=0,fps=60,settb=1/60[c2];
        [2:v]trim=start=0.0:end=1.45,setpts=PTS-STARTPTS,fps=60,settb=1/60[c3];
        [1:v]trim=start=18.60:end=21.80,setpts=PTS-STARTPTS,fps=60,settb=1/60[c4];
        [3:v]trim=start=0.70:end=3.50,setpts=PTS-STARTPTS,fps=60,settb=1/60[c5];

        [c1][c2]xfade=transition=slideleft:duration=0.20:offset=2.15[x1];
        [x1][c3]xfade=transition=zoomin:duration=0.20:offset=11.30[x2];
        [x2][c4]xfade=transition=zoomin:duration=0.15:offset=12.60[x3];
        [x3][c5]xfade=transition=smoothleft:duration=0.25:offset=15.70[raw_montage];

        [raw_montage]{fx_filters}[graded];

        [graded][4:v]overlay=0:0:enable='between(t,0.3,2.0)'[v_intro];
        [v_intro][5:v]overlay=0:0:enable='between(t,16.60,18.50)'[v_ace];

        [v_ace]fade=t=out:st=17.5:d=1.0[v_final]
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", str(TAKE_SHOULDER),
            "-i", str(TAKE_HERO),
            "-i", str(TAKE_VICTIM),
            "-i", str(TAKE_ORBIT),
            "-i", str(OVERLAYS_DIR / "intro_card_16x9.png"),
            "-i", str(OVERLAYS_DIR / "ace_card_16x9.png"),
            "-i", str(AUDIO_MASTER),
            "-filter_complex", filter_complex,
            "-map", "[v_final]",
            "-map", "6:a",
            "-t", "18.5",
            "-pix_fmt", "yuv420p"
        ]
    else:
        # ESPORTS BROADCAST CUT: Frame-accurate killfeed badges (state 5 strictly at 16.50s)
        filter_complex = f"""
        [0:v]trim=start=0.0:end=2.35,setpts=PTS-STARTPTS,fps=60,settb=1/60[c1];
        [1:v]trim=start=5.77:end=12.20,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2a];
        [1:v]trim=start=12.20:end=15.80,setpts=0.25*(PTS-STARTPTS),fps=60,settb=1/60[c2b];
        [1:v]trim=start=15.80:end=17.70,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2c];
        [c2a][c2b][c2c]concat=n=3:v=1:a=0,fps=60,settb=1/60[c2];
        [2:v]trim=start=0.0:end=1.45,setpts=PTS-STARTPTS,fps=60,settb=1/60[c3];
        [1:v]trim=start=18.60:end=21.80,setpts=PTS-STARTPTS,fps=60,settb=1/60[c4];
        [3:v]trim=start=0.70:end=3.50,setpts=PTS-STARTPTS,fps=60,settb=1/60[c5];

        [c1][c2]xfade=transition=slideleft:duration=0.20:offset=2.15[x1];
        [x1][c3]xfade=transition=zoomin:duration=0.20:offset=11.30[x2];
        [x2][c4]xfade=transition=zoomin:duration=0.15:offset=12.60[x3];
        [x3][c5]xfade=transition=smoothleft:duration=0.25:offset=15.70[raw_montage];

        [raw_montage]{fx_filters}[graded];

        [graded][4:v]overlay=0:0:enable='between(t,0.3,2.0)'[v_intro];
        [v_intro][5:v]overlay=0:0:enable='between(t,7.83,10.45)'[v_s1];
        [v_s1][6:v]overlay=0:0:enable='between(t,10.45,12.20)'[v_s2];
        [v_s2][7:v]overlay=0:0:enable='between(t,12.20,13.50)'[v_s3];
        [v_s3][8:v]overlay=0:0:enable='between(t,13.50,16.50)'[v_s4];
        [v_s4][9:v]overlay=0:0:enable='between(t,16.50,18.50)'[v_s5];
        [v_s5][10:v]overlay=0:0:enable='between(t,16.60,18.50)'[v_ace];

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
    print(f"\n--- Assembling Phase 3.2 9:16 TikTok Vertical (Clean Cinematic) -> {output_path} ---")
    t0 = time.time()
    
    lut_fwd = str(LUT_PATH).replace("\\", "/")
    
    filter_complex = f"""
    [0:v]trim=start=0.0:end=2.35,setpts=PTS-STARTPTS,fps=60,settb=1/60[c1];
    [1:v]trim=start=5.77:end=12.20,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2a];
    [1:v]trim=start=12.20:end=15.80,setpts=0.25*(PTS-STARTPTS),fps=60,settb=1/60[c2b];
    [1:v]trim=start=15.80:end=17.70,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2c];
    [c2a][c2b][c2c]concat=n=3:v=1:a=0,fps=60,settb=1/60[c2];
    [2:v]trim=start=0.0:end=1.45,setpts=PTS-STARTPTS,fps=60,settb=1/60[c3];
    [1:v]trim=start=18.60:end=21.80,setpts=PTS-STARTPTS,fps=60,settb=1/60[c4];
    [3:v]trim=start=0.70:end=3.50,setpts=PTS-STARTPTS,fps=60,settb=1/60[c5];

    [c1][c2]xfade=transition=slideleft:duration=0.20:offset=2.15[x1];
    [x1][c3]xfade=transition=zoomin:duration=0.20:offset=11.30[x2];
    [x2][c4]xfade=transition=zoomin:duration=0.15:offset=12.60[x3];
    [x3][c5]xfade=transition=smoothleft:duration=0.25:offset=15.70[base_video];

    [base_video]crop=608:1080:656:0,scale=1080:1920:flags=lanczos,crop=w='iw*(1-0.04*between(t,7.71,7.85)-0.06*between(t,12.18,12.30)-0.05*between(t,16.48,16.65))':h='ih*(1-0.04*between(t,7.71,7.85)-0.06*between(t,12.18,12.30)-0.05*between(t,16.48,16.65))':x='(iw-ow)/2':y='(ih-oh)/2',scale=1080:1920:flags=bicubic,lut3d='{lut_fwd}',eq=brightness=0.25:contrast=1.25:enable='between(t,7.71,7.76)+between(t,10.43,10.48)+between(t,12.18,12.26)+between(t,13.48,13.54)+between(t,16.48,16.58)'[graded_vertical];

    [graded_vertical][4:v]overlay=0:0:enable='between(t,0.3,2.0)'[v_intro];
    [v_intro][5:v]overlay=0:0:enable='between(t,16.60,18.50)'[v_ace];

    [v_ace]fade=t=out:st=17.5:d=1.0[v_final]
    """

    cmd = [
        "ffmpeg", "-y",
        "-i", str(TAKE_SHOULDER),
        "-i", str(TAKE_HERO),
        "-i", str(TAKE_VICTIM),
        "-i", str(TAKE_ORBIT),
        "-i", str(OVERLAYS_DIR / "intro_card_tiktok.png"),
        "-i", str(OVERLAYS_DIR / "ace_card_tiktok.png"),
        "-i", str(AUDIO_MASTER),
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "6:a",
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
    broadcast_mp4 = V3_DIR / "ACE_FINAL_V3_BROADCAST_KILLFEED.mp4"
    tiktok_mp4 = V3_DIR / "ACE_FINAL_V3_TIKTOK.mp4"
    
    # 1. Clean Cinematic Preview (Fast 1080p60)
    assemble_v3_master_16x9(preview_mp4, preview=True, show_killfeed=False)
    # 2. Pure Cinematic Master (24 Mbps AMF, clean combat focus, no obstructive badges)
    assemble_v3_master_16x9(master_mp4, preview=False, show_killfeed=False)
    # 3. Esports Broadcast Master (With frame-accurate tournament killfeed)
    assemble_v3_master_16x9(broadcast_mp4, preview=False, show_killfeed=True)
    # 4. Vertical TikTok Master (1080x1920)
    assemble_v3_tiktok_9x16(tiktok_mp4)
    print("\nPhase 3.2: All Master Deliverables (Pure Cinematic & Broadcast) Rendered Successfully!")
