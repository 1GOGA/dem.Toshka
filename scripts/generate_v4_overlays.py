import pathlib
from PIL import Image, ImageDraw, ImageFont

V4_DIR = pathlib.Path("renders/ACE_FINAL_V4_MASTER_CUT")
V4_DIR.mkdir(parents=True, exist_ok=True)
OVERLAYS_DIR = V4_DIR / "overlays"
OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = V4_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR = V4_DIR / "qa"
QA_DIR.mkdir(parents=True, exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_HEAVY = r"C:\Windows\Fonts\impact.ttf"

try:
    font_badge = ImageFont.truetype(FONT_HEAVY, 28)
    font_name = ImageFont.truetype(FONT_BOLD, 22)
    font_weapon = ImageFont.truetype(FONT_BOLD, 20)
    font_title_large = ImageFont.truetype(FONT_HEAVY, 72)
    font_sub_large = ImageFont.truetype(FONT_BOLD, 32)
except Exception:
    font_badge = ImageFont.load_default()
    font_name = ImageFont.load_default()
    font_weapon = ImageFont.load_default()
    font_title_large = ImageFont.load_default()
    font_sub_large = ImageFont.load_default()

KILL_DATA = [
    {"num": 1, "killer": "pytoshka_", "victim": "Tiger07", "weapon": "M4A1", "badge_col": (255, 140, 0), "hs": False},
    {"num": 2, "killer": "pytoshka_", "victim": "zuuuuuhhhhn", "weapon": "M4A1", "badge_col": (255, 100, 0), "hs": False},
    {"num": 3, "killer": "pytoshka_", "victim": "ProfyfGames", "weapon": "M4A1", "badge_col": (230, 40, 40), "hs": True},
    {"num": 4, "killer": "pytoshka_", "victim": "freekjkeee", "weapon": "M4A1", "badge_col": (210, 30, 180), "hs": False},
    {"num": 5, "killer": "pytoshka_", "victim": "axuenchik002", "weapon": "M4A1", "badge_col": (255, 215, 0), "hs": False},
]

def render_killfeed_banner_16x9(active_kills):
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    base_x = 1380
    base_y = 60
    row_h = 44
    gap = 6
    
    for i, k in enumerate(active_kills):
        y = base_y + i * (row_h + gap)
        # Background pill
        bg_col = (18, 18, 22, 220)
        border_col = k["badge_col"] + (200,)
        draw.rounded_rectangle([base_x, y, base_x + 480, y + row_h], radius=6, fill=bg_col, outline=border_col, width=2)
        
        # Badge box
        badge_w = 64
        draw.rounded_rectangle([base_x, y, base_x + badge_w, y + row_h], radius=4, fill=k["badge_col"] + (255,))
        badge_txt = f"{k['num']}K"
        draw.text((base_x + 14, y + 6), badge_txt, fill=(255, 255, 255), font=font_badge)
        
        # Killer
        draw.text((base_x + 78, y + 10), k["killer"], fill=(255, 210, 60), font=font_name)
        
        # Weapon & HS icon
        wpn_text = f"[{k['weapon']}]"
        draw.text((base_x + 210, y + 11), wpn_text, fill=(200, 200, 200), font=font_weapon)
        if k["hs"]:
            draw.text((base_x + 295, y + 8), "🎯", fill=(255, 50, 50), font=font_name)
            draw.text((base_x + 325, y + 10), k["victim"], fill=(255, 255, 255), font=font_name)
        else:
            draw.text((base_x + 295, y + 10), k["victim"], fill=(255, 255, 255), font=font_name)
            
    return img

def render_killfeed_banner_tiktok(active_kills):
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    base_x = 180
    base_y = 320
    row_h = 60
    gap = 10
    
    for i, k in enumerate(active_kills):
        y = base_y + i * (row_h + gap)
        bg_col = (16, 16, 20, 230)
        border_col = k["badge_col"] + (220,)
        draw.rounded_rectangle([base_x, y, base_x + 720, y + row_h], radius=8, fill=bg_col, outline=border_col, width=2)
        
        # Badge box
        badge_w = 90
        draw.rounded_rectangle([base_x, y, base_x + badge_w, y + row_h], radius=6, fill=k["badge_col"] + (255,))
        badge_txt = f"{k['num']}K"
        draw.text((base_x + 20, y + 12), badge_txt, fill=(255, 255, 255), font=font_badge)
        
        # Killer
        draw.text((base_x + 110, y + 16), k["killer"], fill=(255, 210, 60), font=font_name)
        
        # Weapon
        wpn_text = f"[{k['weapon']}]"
        draw.text((base_x + 290, y + 17), wpn_text, fill=(200, 200, 200), font=font_weapon)
        if k["hs"]:
            draw.text((base_x + 400, y + 14), "🎯", fill=(255, 50, 50), font=font_name)
            draw.text((base_x + 440, y + 16), k["victim"], fill=(255, 255, 255), font=font_name)
        else:
            draw.text((base_x + 400, y + 16), k["victim"], fill=(255, 255, 255), font=font_name)
            
    return img

def render_intro_card_16x9():
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((120, 840), "PYTOSHKA_", fill=(255, 215, 0, 240), font=font_title_large)
    draw.text((125, 930), "DE_ANUBIS // ROUND 19 ACE", fill=(220, 220, 230, 200), font=font_sub_large)
    return img

def render_ace_card_16x9():
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Radiant gold box
    draw.rounded_rectangle([460, 440, 1460, 640], radius=16, fill=(15, 15, 20, 220), outline=(255, 215, 0, 255), width=4)
    draw.text((580, 465), "★ ACE DOMINATION ★", fill=(255, 215, 0, 255), font=font_title_large)
    draw.text((710, 560), "1v5 CLUTCH // M4A1 CLEAN 5K", fill=(255, 255, 255, 230), font=font_sub_large)
    return img

# Generate 5 states for 16x9 and TikTok
for count in range(1, 6):
    active = KILL_DATA[:count]
    img16 = render_killfeed_banner_16x9(active)
    img16.save(OVERLAYS_DIR / f"killfeed_16x9_state_{count}.png")
    
    img_tt = render_killfeed_banner_tiktok(active)
    img_tt.save(OVERLAYS_DIR / f"killfeed_tiktok_state_{count}.png")

render_intro_card_16x9().save(OVERLAYS_DIR / "intro_card_16x9.png")
render_ace_card_16x9().save(OVERLAYS_DIR / "ace_card_16x9.png")

print("Generated V4 overlays successfully in", OVERLAYS_DIR)
