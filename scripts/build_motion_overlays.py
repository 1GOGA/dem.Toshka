import pathlib
from PIL import Image, ImageDraw, ImageFont

OVERLAY_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/overlays")
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_PATH_HEAVY = r"C:\Windows\Fonts\impact.ttf"

def draw_pill(draw, xy, fill, outline=None, width=1, radius=8):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def draw_skull(draw, center_x, center_y, size=14, color=(255, 60, 60, 255)):
    # Simple crisp skull glyph
    # cranium circle
    r = size // 2
    draw.ellipse([center_x - r, center_y - r - 2, center_x + r, center_y + r - 2], fill=color)
    # jaw rect
    draw.rectangle([center_x - r + 3, center_y, center_x + r - 3, center_y + r + 3], fill=color)
    # eye sockets (transparent/dark cutout)
    eye_r = 2
    draw.ellipse([center_x - 4 - eye_r, center_y - 2 - eye_r, center_x - 4 + eye_r, center_y - 2 + eye_r], fill=(20, 20, 25, 255))
    draw.ellipse([center_x + 4 - eye_r, center_y - 2 - eye_r, center_x + 4 + eye_r, center_y - 2 + eye_r], fill=(20, 20, 25, 255))

# ----------------- 16:9 Master Overlays (1920x1080) -----------------
def create_16x9_badge(kill_num, killer, victim, weapon, is_headshot, multikill_text, glow_color):
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Position in upper right killfeed area
    w, h = 480, 56
    x1, y1 = 1920 - w - 60, 70
    x2, y2 = x1 + w, y1 + h
    
    # Glow / shadow back
    draw_pill(draw, (x1 - 2, y1 - 2, x2 + 2, y2 + 2), fill=(glow_color[0], glow_color[1], glow_color[2], 60), radius=10)
    # Background pill
    draw_pill(draw, (x1, y1, x2, y2), fill=(16, 20, 28, 225), outline=glow_color, width=2, radius=8)
    
    # Left multikill badge
    f_badge = ImageFont.truetype(FONT_PATH_HEAVY, 22)
    b_w = 75
    draw_pill(draw, (x1, y1, x1 + b_w, y2), fill=glow_color, radius=6)
    badge_label = f"{kill_num}K"
    bbox = draw.textbbox((0, 0), badge_label, font=f_badge)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x1 + (b_w - tw)//2, y1 + (h - th)//2 - 2), badge_label, fill=(255, 255, 255, 255), font=f_badge)
    
    # Text info
    f_info = ImageFont.truetype(FONT_PATH_BOLD, 19)
    f_sub = ImageFont.truetype(FONT_PATH_BOLD, 13)
    
    # Killer name
    draw.text((x1 + b_w + 14, y1 + 9), killer, fill=(255, 215, 0, 255), font=f_info)
    # Weapon
    weap_text = f"[{weapon.upper()}]"
    draw.text((x1 + b_w + 125, y1 + 10), weap_text, fill=(200, 215, 230, 255), font=f_info)
    
    # Headshot icon if applicable
    cur_x = x1 + b_w + 195
    if is_headshot:
        draw_skull(draw, cur_x + 8, y1 + 22, size=15, color=(255, 70, 70, 255))
        cur_x += 24
        
    # Victim name
    draw.text((cur_x + 6, y1 + 9), victim, fill=(225, 225, 230, 255), font=f_info)
    
    # Subtitle: Multikill tier
    draw.text((x1 + b_w + 14, y1 + 34), multikill_text.upper(), fill=glow_color, font=f_sub)
    
    return img

# ----------------- 9:16 Vertical TikTok Overlays (1080x1920) -----------------
def create_tiktok_badge(kill_num, killer, victim, weapon, is_headshot, multikill_text, glow_color):
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Centered in safe zone above crosshair (y=340)
    w, h = 640, 84
    x1, y1 = (1080 - w)//2, 340
    x2, y2 = x1 + w, y1 + h
    
    # Glow / shadow back
    draw_pill(draw, (x1 - 3, y1 - 3, x2 + 3, y2 + 3), fill=(glow_color[0], glow_color[1], glow_color[2], 80), radius=14)
    # Background pill
    draw_pill(draw, (x1, y1, x2, y2), fill=(14, 18, 26, 235), outline=glow_color, width=3, radius=12)
    
    # Left multikill badge
    f_badge = ImageFont.truetype(FONT_PATH_HEAVY, 36)
    b_w = 110
    draw_pill(draw, (x1, y1, x1 + b_w, y2), fill=glow_color, radius=10)
    badge_label = f"{kill_num}K"
    bbox = draw.textbbox((0, 0), badge_label, font=f_badge)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x1 + (b_w - tw)//2, y1 + (h - th)//2 - 4), badge_label, fill=(255, 255, 255, 255), font=f_badge)
    
    # Text info
    f_info = ImageFont.truetype(FONT_PATH_BOLD, 26)
    f_sub = ImageFont.truetype(FONT_PATH_BOLD, 17)
    
    # Killer name
    draw.text((x1 + b_w + 18, y1 + 12), killer, fill=(255, 215, 0, 255), font=f_info)
    # Weapon
    weap_text = f"[{weapon.upper()}]"
    draw.text((x1 + b_w + 170, y1 + 13), weap_text, fill=(200, 215, 230, 255), font=f_info)
    
    # Headshot icon if applicable
    cur_x = x1 + b_w + 265
    if is_headshot:
        draw_skull(draw, cur_x + 12, y1 + 28, size=20, color=(255, 70, 70, 255))
        cur_x += 32
        
    # Victim name
    draw.text((cur_x + 8, y1 + 12), victim, fill=(230, 235, 245, 255), font=f_info)
    
    # Subtitle: Multikill tier
    draw.text((x1 + b_w + 18, y1 + 50), multikill_text.upper(), fill=glow_color, font=f_sub)
    
    return img

# ----------------- ACE Domination Climax Card (Full Width) -----------------
def create_ace_card(width, height):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    card_w = int(width * 0.75)
    card_h = 130 if width > height else 180
    cx = (width - card_w) // 2
    cy = int(height * 0.72)
    
    # Glowing backdrop
    gold = (255, 195, 0, 255)
    draw_pill(draw, (cx - 4, cy - 4, cx + card_w + 4, cy + card_h + 4), fill=(255, 180, 0, 90), radius=16)
    draw_pill(draw, (cx, cy, cx + card_w, cy + card_h), fill=(18, 16, 22, 240), outline=gold, width=3, radius=14)
    
    f_title = ImageFont.truetype(FONT_PATH_HEAVY, 44 if width > height else 48)
    f_sub = ImageFont.truetype(FONT_PATH_BOLD, 20 if width > height else 22)
    
    title_text = "5K ACE — ROUND DOMINATION"
    sub_text = "PLAYER: pytoshka_ • 5 KILLS • DE_ANUBIS ROUND 19"
    
    bbox1 = draw.textbbox((0, 0), title_text, font=f_title)
    w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
    draw.text((cx + (card_w - w1)//2, cy + 18), title_text, fill=gold, font=f_title)
    
    bbox2 = draw.textbbox((0, 0), sub_text, font=f_sub)
    w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    draw.text((cx + (card_w - w2)//2, cy + 18 + h1 + 14), sub_text, fill=(230, 240, 255, 255), font=f_sub)
    
    return img

# ----------------- Intro Title Card -----------------
def create_intro_card(width, height):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    f_super = ImageFont.truetype(FONT_PATH_BOLD, 18 if width > height else 22)
    f_main = ImageFont.truetype(FONT_PATH_HEAVY, 54 if width > height else 58)
    f_sub = ImageFont.truetype(FONT_PATH_BOLD, 22 if width > height else 24)
    
    super_text = "DEM.TOSHKA CINEMATIC STUDIO PRESENTS"
    main_text = "DE_ANUBIS • ACE CLUTCH"
    sub_text = "FEATURING: pytoshka_ • ROUND 19"
    
    cy = int(height * 0.45)
    
    bbox0 = draw.textbbox((0, 0), super_text, font=f_super)
    w0 = bbox0[2] - bbox0[0]
    draw.text(((width - w0)//2, cy - 65), super_text, fill=(200, 215, 235, 220), font=f_super)
    
    bbox1 = draw.textbbox((0, 0), main_text, font=f_main)
    w1 = bbox1[2] - bbox1[0]
    # Gold gradient accent line
    line_y = cy + 10
    draw.text(((width - w1)//2, cy - 35), main_text, fill=(255, 215, 0, 255), font=f_main)
    draw.line([(width - w1)//2, line_y + 35, (width + w1)//2, line_y + 35], fill=(255, 215, 0, 200), width=3)
    
    bbox2 = draw.textbbox((0, 0), sub_text, font=f_sub)
    w2 = bbox2[2] - bbox2[0]
    draw.text(((width - w2)//2, cy + 55), sub_text, fill=(240, 245, 255, 240), font=f_sub)
    
    return img

kills = [
    (1, "pytoshka_", "Tiger07", "m4a1", False, "First Blood", (255, 140, 0, 255)),
    (2, "pytoshka_", "zuuuuuhhhhn", "m4a1", False, "Double Kill", (255, 100, 0, 255)),
    (3, "pytoshka_", "ProfyfGames", "m4a1", True, "Triple Kill • Headshot", (255, 40, 40, 255)),
    (4, "pytoshka_", "freekjkeee", "m4a1", False, "Quadra Kill", (220, 30, 220, 255)),
    (5, "pytoshka_", "axuenchik002", "m4a1", False, "Ace — Round Won", (255, 215, 0, 255))
]

# Generate 16:9 Overlays
for k, killer, victim, weap, hs, tier, glow in kills:
    b16 = create_16x9_badge(k, killer, victim, weap, hs, tier, glow)
    p = OVERLAY_DIR / f"badge_16x9_kill_{k}.png"
    b16.save(str(p), "PNG")
    print(f"Saved {p.name}")

# Generate 9:16 TikTok Overlays
for k, killer, victim, weap, hs, tier, glow in kills:
    b9 = create_tiktok_badge(k, killer, victim, weap, hs, tier, glow)
    p = OVERLAY_DIR / f"badge_tiktok_kill_{k}.png"
    b9.save(str(p), "PNG")
    print(f"Saved {p.name}")

# ACE Card
ace16 = create_ace_card(1920, 1080)
ace16.save(str(OVERLAY_DIR / "ace_card_16x9.png"), "PNG")
ace9 = create_ace_card(1080, 1920)
ace9.save(str(OVERLAY_DIR / "ace_card_tiktok.png"), "PNG")

# Intro Cards
intro16 = create_intro_card(1920, 1080)
intro16.save(str(OVERLAY_DIR / "intro_card_16x9.png"), "PNG")
intro9 = create_intro_card(1080, 1920)
intro9.save(str(OVERLAY_DIR / "intro_card_tiktok.png"), "PNG")

print("All motion graphics overlays generated successfully.")
