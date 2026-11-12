import json
import os
import pathlib
import subprocess
import time

V4_DIR = pathlib.Path("renders/ACE_FINAL_V4_MASTER_CUT")
V4_DIR.mkdir(parents=True, exist_ok=True)

TAKES_DIR = pathlib.Path("renders/cinematic_studio_phase3/takes")
OVERLAYS_DIR = V4_DIR / "overlays"
COLOR_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/color")
AUDIO_DIR = V4_DIR / "audio"

TAKE_SHOULDER = TAKES_DIR / "shot_anubis_ace_r19_02_shoulder_approach.mp4"
TAKE_HERO = TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4"
TAKE_ORBIT = TAKES_DIR / "shot_anubis_ace_r19_04_climax_orbit.mp4"

LUT_PATH = COLOR_DIR / "egyptian_sandstone_cinematic.cube"
AUDIO_MASTER = AUDIO_DIR / "audio_master_v4.wav"

lut_fwd = str(LUT_PATH).replace("\\", "/")

def assemble_master(out_path):
    print(f"\n==========================================")
    print(f"1. RENDERING 16:9 MASTER -> {out_path.name}")
    print(f"==========================================")
    t0 = time.time()
    
    fx_filters = (
        f"lut3d='{lut_fwd}',"
        "crop=w='iw*(1-0.05*between(t,7.18,7.35))':"
        "h='ih*(1-0.05*between(t,7.18,7.35))':"
        "x='(iw-ow)/2':y='(ih-oh)/2',scale=1920:1080:flags=bicubic,"
        "eq=brightness=0.18:contrast=1.18:enable='between(t,2.68,2.74)+between(t,5.30,5.36)+between(t,7.21,7.28)+between(t,8.15,8.21)+between(t,8.85,8.95)',"
        "curves=master='0/0 0.5/0.52 1/1':red='0/0 0.5/0.56 1/1':blue='0/0 0.5/0.46 1/1':enable='between(t,9.0,15.0)'"
    )

    filter_complex = f"""
    [0:v]trim=start=0.0:end=2.40,setpts=PTS-STARTPTS,fps=60,settb=1/60[c1];
    [1:v]trim=start=5.20:end=9.95,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2a];
    [1:v]trim=start=9.95:end=10.20,setpts=2.0*(PTS-STARTPTS),fps=60,settb=1/60[c2b];
    [1:v]trim=start=10.20:end=11.80,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2c];
    [c2a][c2b][c2c]concat=n=3:v=1:a=0,fps=60,settb=1/60[c2];
    [2:v]trim=start=0.0:end=6.30,setpts=PTS-STARTPTS,fps=60,settb=1/60[c3];

    [c1][c2]xfade=transition=slideleft:duration=0.20:offset=2.20[x1];
    [x1][c3]xfade=transition=circlecrop:duration=0.20:offset=8.85[raw_montage];

    [raw_montage]{fx_filters}[graded];

    [graded][3:v]overlay=0:0:enable='between(t,0.30,2.10)'[v_intro];
    [v_intro][4:v]overlay=0:0:enable='between(t,2.70,5.32)'[v_k1];
    [v_k1][5:v]overlay=0:0:enable='between(t,5.32,7.23)'[v_k2];
    [v_k2][6:v]overlay=0:0:enable='between(t,7.23,8.17)'[v_k3];
    [v_k3][7:v]overlay=0:0:enable='between(t,8.17,8.95)'[v_k4];
    [v_k4][8:v]overlay=0:0:enable='between(t,8.95,14.50)'[v_k5];
    [v_k5][9:v]overlay=0:0:enable='between(t,9.20,13.80)'[v_ace];

    [v_ace]fade=t=out:st=14.2:d=0.8[v_final]
    """

    cmd = [
        "ffmpeg", "-y",
        "-i", str(TAKE_SHOULDER),
        "-i", str(TAKE_HERO),
        "-i", str(TAKE_ORBIT),
        "-i", str(OVERLAYS_DIR / "intro_card_16x9.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_16x9_state_1.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_16x9_state_2.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_16x9_state_3.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_16x9_state_4.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_16x9_state_5.png"),
        "-i", str(OVERLAYS_DIR / "ace_card_16x9.png"),
        "-i", str(AUDIO_MASTER),
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "10:a",
        "-t", "15.0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "320k",
        "-pix_fmt", "yuv420p",
        str(out_path)
    ]
    subprocess.run(cmd, check=True)
    print(f"Master rendered in {time.time()-t0:.1f}s ({out_path.stat().st_size} bytes)")

def assemble_cinematic(out_path):
    print(f"\n==========================================")
    print(f"2. RENDERING 2.39:1 CINEMASCOPE -> {out_path.name}")
    print(f"==========================================")
    t0 = time.time()
    
    fx_filters = (
        f"lut3d='{lut_fwd}',"
        "crop=w='iw*(1-0.05*between(t,7.18,7.35))':"
        "h='ih*(1-0.05*between(t,7.18,7.35))':"
        "x='(iw-ow)/2':y='(ih-oh)/2',scale=1920:1080:flags=bicubic,"
        "eq=brightness=0.18:contrast=1.18:enable='between(t,2.68,2.74)+between(t,5.30,5.36)+between(t,7.21,7.28)+between(t,8.15,8.21)+between(t,8.85,8.95)',"
        "curves=master='0/0 0.5/0.52 1/1':red='0/0 0.5/0.56 1/1':blue='0/0 0.5/0.46 1/1':enable='between(t,9.0,15.0)',"
        "drawbox=y=0:h=138:color=black:t=fill,"
        "drawbox=y=942:h=138:color=black:t=fill"
    )

    filter_complex = f"""
    [0:v]trim=start=0.0:end=2.40,setpts=PTS-STARTPTS,fps=60,settb=1/60[c1];
    [1:v]trim=start=5.20:end=9.95,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2a];
    [1:v]trim=start=9.95:end=10.20,setpts=2.0*(PTS-STARTPTS),fps=60,settb=1/60[c2b];
    [1:v]trim=start=10.20:end=11.80,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2c];
    [c2a][c2b][c2c]concat=n=3:v=1:a=0,fps=60,settb=1/60[c2];
    [2:v]trim=start=0.0:end=6.30,setpts=PTS-STARTPTS,fps=60,settb=1/60[c3];

    [c1][c2]xfade=transition=slideleft:duration=0.20:offset=2.20[x1];
    [x1][c3]xfade=transition=circlecrop:duration=0.20:offset=8.85[raw_montage];

    [raw_montage]{fx_filters}[graded];

    [graded][3:v]overlay=0:0:enable='between(t,0.30,2.10)'[v_intro];
    [v_intro][4:v]overlay=0:0:enable='between(t,9.20,13.80)'[v_ace];

    [v_ace]fade=t=out:st=14.2:d=0.8[v_final]
    """

    cmd = [
        "ffmpeg", "-y",
        "-i", str(TAKE_SHOULDER),
        "-i", str(TAKE_HERO),
        "-i", str(TAKE_ORBIT),
        "-i", str(OVERLAYS_DIR / "intro_card_16x9.png"),
        "-i", str(OVERLAYS_DIR / "ace_card_16x9.png"),
        "-i", str(AUDIO_MASTER),
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "5:a",
        "-t", "15.0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "320k",
        "-pix_fmt", "yuv420p",
        str(out_path)
    ]
    subprocess.run(cmd, check=True)
    print(f"Cinemascope rendered in {time.time()-t0:.1f}s ({out_path.stat().st_size} bytes)")

def assemble_tiktok(out_path):
    print(f"\n==========================================")
    print(f"3. RENDERING 9:16 TIKTOK VERTICAL -> {out_path.name}")
    print(f"==========================================")
    t0 = time.time()
    
    fx_filters = (
        f"lut3d='{lut_fwd}',"
        "crop=608:1080:656:0,scale=1080:1920:flags=lanczos,"
        "crop=w='iw*(1-0.05*between(t,7.18,7.35))':"
        "h='ih*(1-0.05*between(t,7.18,7.35))':"
        "x='(iw-ow)/2':y='(ih-oh)/2',scale=1080:1920:flags=bicubic,"
        "eq=brightness=0.18:contrast=1.18:enable='between(t,2.68,2.74)+between(t,5.30,5.36)+between(t,7.21,7.28)+between(t,8.15,8.21)+between(t,8.85,8.95)',"
        "curves=master='0/0 0.5/0.52 1/1':red='0/0 0.5/0.56 1/1':blue='0/0 0.5/0.46 1/1':enable='between(t,9.0,15.0)'"
    )

    filter_complex = f"""
    [0:v]trim=start=0.0:end=2.40,setpts=PTS-STARTPTS,fps=60,settb=1/60[c1];
    [1:v]trim=start=5.20:end=9.95,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2a];
    [1:v]trim=start=9.95:end=10.20,setpts=2.0*(PTS-STARTPTS),fps=60,settb=1/60[c2b];
    [1:v]trim=start=10.20:end=11.80,setpts=PTS-STARTPTS,fps=60,settb=1/60[c2c];
    [c2a][c2b][c2c]concat=n=3:v=1:a=0,fps=60,settb=1/60[c2];
    [2:v]trim=start=0.0:end=6.30,setpts=PTS-STARTPTS,fps=60,settb=1/60[c3];

    [c1][c2]xfade=transition=slideleft:duration=0.20:offset=2.20[x1];
    [x1][c3]xfade=transition=circlecrop:duration=0.20:offset=8.85[raw_montage];

    [raw_montage]{fx_filters}[graded];

    [graded][3:v]overlay=0:0:enable='between(t,2.70,5.32)'[v_k1];
    [v_k1][4:v]overlay=0:0:enable='between(t,5.32,7.23)'[v_k2];
    [v_k2][5:v]overlay=0:0:enable='between(t,7.23,8.17)'[v_k3];
    [v_k3][6:v]overlay=0:0:enable='between(t,8.17,8.95)'[v_k4];
    [v_k4][7:v]overlay=0:0:enable='between(t,8.95,14.50)'[v_k5];

    [v_k5]fade=t=out:st=14.2:d=0.8[v_final]
    """

    cmd = [
        "ffmpeg", "-y",
        "-i", str(TAKE_SHOULDER),
        "-i", str(TAKE_HERO),
        "-i", str(TAKE_ORBIT),
        "-i", str(OVERLAYS_DIR / "killfeed_tiktok_state_1.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_tiktok_state_2.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_tiktok_state_3.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_tiktok_state_4.png"),
        "-i", str(OVERLAYS_DIR / "killfeed_tiktok_state_5.png"),
        "-i", str(AUDIO_MASTER),
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "8:a",
        "-t", "15.0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-c:a", "aac", "-b:a", "320k",
        "-pix_fmt", "yuv420p",
        str(out_path)
    ]
    subprocess.run(cmd, check=True)
    print(f"TikTok vertical rendered in {time.time()-t0:.1f}s ({out_path.stat().st_size} bytes)")

def assemble_preview(in_master, out_preview):
    print(f"\n==========================================")
    print(f"4. RENDERING FAST 720p PREVIEW -> {out_preview.name}")
    print(f"==========================================")
    t0 = time.time()
    cmd = [
        "ffmpeg", "-y",
        "-i", str(in_master),
        "-vf", "scale=1280:720:flags=bicubic",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out_preview)
    ]
    subprocess.run(cmd, check=True)
    print(f"Preview rendered in {time.time()-t0:.1f}s ({out_preview.stat().st_size} bytes)")

if __name__ == "__main__":
    p_master = V4_DIR / "ACE_FINAL_V4_MASTER.mp4"
    p_cinematic = V4_DIR / "ACE_FINAL_V4_CINEMATIC.mp4"
    p_tiktok = V4_DIR / "ACE_FINAL_V4_TIKTOK.mp4"
    p_prev = V4_DIR / "ACE_FINAL_V4_PREVIEW.mp4"
    
    assemble_master(p_master)
    assemble_cinematic(p_cinematic)
    assemble_tiktok(p_tiktok)
    assemble_preview(p_master, p_prev)
    print("\nALL 4 DELIVERABLES SUCCESSFULLY PRODUCED IN", V4_DIR)
