import json
import pathlib
import subprocess
from PIL import Image, ImageDraw, ImageFont

V3_DIR = pathlib.Path("renders/ACE_FINAL_V3_AUDIO_KILLFEED")
QA_DIR = V3_DIR / "qa"
QA_DIR.mkdir(parents=True, exist_ok=True)

HERO_TAKE = pathlib.Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_01_hero_pov.mp4")
VICTIM_TAKE = pathlib.Path("renders/cinematic_studio_phase3/takes/shot_anubis_ace_r19_03_victim_reaction.mp4")
PHASE31_MASTER = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/ACE_FINAL_V2_MASTER.mp4")

FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_HEAVY = r"C:\Windows\Fonts\impact.ttf"

manifest = json.loads((V3_DIR / "killfeed_event_manifest.json").read_text(encoding="utf-8"))

# We want 5 rows (one per kill), and 4 columns:
# Col 1: -0.5s before kill (weapon aiming / peeking)
# Col 2: EXACT KILL FRAME (bullet discharge & death confirmation tick)
# Col 3: +0.5s after kill (elimination confirmed / victim falling)
# Col 4: Phase 3.1 comparison (showing the previous timing discrepancy)

thumb_w = 480
thumb_h = 270
pad = 14
header_h = 70
left_label_w = 120

grid_cols = 4
grid_rows = 5

sheet_w = left_label_w + grid_cols * thumb_w + (grid_cols + 1) * pad
sheet_h = header_h + grid_rows * thumb_h + (grid_rows + 1) * pad

sheet = Image.new("RGB", (sheet_w, sheet_h), (16, 18, 24))
draw = ImageDraw.Draw(sheet)

# Header
f_h = ImageFont.truetype(FONT_HEAVY, 30)
f_sub = ImageFont.truetype(FONT_BOLD, 15)
f_cell = ImageFont.truetype(FONT_BOLD, 13)
f_row_lbl = ImageFont.truetype(FONT_HEAVY, 18)

draw.text((pad + 10, 14), "DEM.TOSHKA CINEMATIC STUDIO — PHASE 3.2 KILL EVENT SYNCHRONIZATION QA", fill=(255, 215, 0), font=f_h)
draw.text((pad + 10, 48), "FRAME-BY-FRAME TIMING VERIFICATION (DEMO TICKS vs VISIBLE HIT vs TIMELINE OVERLAYS)", fill=(200, 215, 235), font=f_sub)

col_headers = [
    "A: -0.50s (Weapon Peeking)",
    "B: EXACT KILL FRAME (Hit Tick)",
    "C: +0.50s (Elimination / Fall)",
    "D: Phase 3.1 Comparison (Pre-Correction)"
]

f_ch = ImageFont.truetype(FONT_BOLD, 14)
for c_idx, ch_text in enumerate(col_headers):
    cx = left_label_w + pad + c_idx * (thumb_w + pad)
    draw.text((cx + 10, header_h - 18), ch_text, fill=(255, 200, 100), font=f_ch)

# Phase 3.1 reference times
p31_times = [8.18, 10.72, 12.41, 13.25, 15.79]

temp_dir = QA_DIR / "temp_frames"
temp_dir.mkdir(parents=True, exist_ok=True)

for r_idx, k_data in enumerate(manifest):
    k_num = k_data["kill_num"]
    t_hit = k_data["timeline_timestamp"]
    f_hit = k_data["timeline_frame"]
    victim = k_data["victim"]
    weap = k_data["weapon"].upper()
    hs_txt = " [HEADSHOT]" if k_data["headshot"] else ""
    
    # Left row label
    ry = header_h + pad + r_idx * (thumb_h + pad)
    draw.rectangle([pad, ry, left_label_w, ry + thumb_h], fill=(22, 26, 36), outline=(60, 80, 110), width=1)
    draw.text((pad + 8, ry + 20), f"KILL #{k_num}", fill=(255, 215, 0), font=f_row_lbl)
    draw.text((pad + 8, ry + 50), f"Tick: {k_data['tick']}", fill=(200, 215, 235), font=f_sub)
    draw.text((pad + 8, ry + 75), f"F: {f_hit}", fill=(100, 255, 150), font=f_row_lbl)
    draw.text((pad + 8, ry + 105), f"{weap}", fill=(220, 220, 220), font=f_sub)
    draw.text((pad + 8, ry + 130), f"-> {victim}", fill=(255, 180, 180), font=f_sub)
    if k_data["headshot"]:
        draw.text((pad + 8, ry + 160), "HEADSHOT!", fill=(255, 50, 50), font=f_sub)

    # 4 columns for this kill
    timestamps = [
        (max(0.0, t_hit - 0.50), "before", False),
        (t_hit, "hit", False),
        (t_hit + 0.50, "after", False),
        (p31_times[r_idx], "phase31", True)
    ]
    
    for c_idx, (t_sec, tag, is_p31) in enumerate(timestamps):
        cx = left_label_w + pad + c_idx * (thumb_w + pad)
        cy = ry
        
        frame_img_path = temp_dir / f"sync_k{k_num}_{tag}_{t_sec:.3f}s.png"
        
        # Source video
        src_video = PHASE31_MASTER if is_p31 else (VICTIM_TAKE if (k_num == 3 and not is_p31) else HERO_TAKE)
        # Calculate time in src_video
        if not is_p31:
            t_in_src = k_data["source_timestamp"] + (t_sec - t_hit)
        else:
            t_in_src = t_sec
            
        cmd = ["ffmpeg", "-y", "-ss", f"{t_in_src:.3f}", "-i", str(src_video), "-frames:v", "1", "-q:v", "2", str(frame_img_path)]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if frame_img_path.exists():
            im = Image.open(frame_img_path).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (cx, cy))
            
            # Border: Green for exact hit, Red/Orange for Phase 3.1, Slate for before/after
            border_col = (50, 220, 100) if tag == "hit" else ((220, 80, 80) if is_p31 else (70, 90, 120))
            draw.rectangle([cx, cy, cx + thumb_w, cy + thumb_h], outline=border_col, width=2)
            
            # Label
            draw.rectangle([cx, cy + thumb_h - 26, cx + thumb_w, cy + thumb_h], fill=(12, 14, 20))
            lbl_text = f"t={t_sec:.3f}s (Frame {round(t_sec*60)}) | {tag.upper()}"
            if is_p31:
                lbl_text += f" [Δ = {round((t_sec - t_hit)*60):+d}f]"
            draw.text((cx + 8, cy + thumb_h - 22), lbl_text, fill=(255, 255, 255), font=f_cell)

contact_sheet_path = QA_DIR / "qa_kill_sync_contact_sheet.png"
sheet.save(str(contact_sheet_path), "PNG")
print(f"Generated Kill Sync Timing QA Sheet: {contact_sheet_path}")

# Cleanup temp frames
for f in temp_dir.glob("*.png"):
    f.unlink()
temp_dir.rmdir()
