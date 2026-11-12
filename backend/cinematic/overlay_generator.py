"""Graphical Overlays and Custom Killfeed Generator.

Generates high-contrast esports/cinematic kill-feed graphics and DaVinci Resolve
track-4 overlay compositions based on real CS2 demo events.

Supports 3 visual styles:
1. cinematic (sleek gold & cyan accents, subtle glassmorphic gradients)
2. dark (tactical stealth carbon with neon crimson accents)
3. broadcast (tier-1 tournament esports broadcast with team badges and kill counters)
"""

from __future__ import annotations

import pathlib
from typing import Any, Optional
from PIL import Image, ImageDraw, ImageFont

from backend.cinematic.models import OverlayKillEvent


def generate_svg_killfeed_badge(event: OverlayKillEvent, style: str = "cinematic") -> str:
    """Generate high-resolution transparent SVG killfeed badge."""
    style_key = style.lower().strip()

    # Style palettes
    if style_key == "dark":
        bg_fill = "#111827"
        bg_stroke = "#f43f5e"
        bg_stroke_opacity = "0.7"
        killer_color = "#f43f5e"
        victim_color = "#94a3b8"
        weapon_bg = "#1e293b"
        weapon_text = "#f8fafc"
        counter_fill = "#e11d48"
    elif style_key == "broadcast":
        bg_fill = "#090d16"
        bg_stroke = "#3b82f6"
        bg_stroke_opacity = "0.9"
        killer_color = "#60a5fa"
        victim_color = "#f1f5f9"
        weapon_bg = "#1e3a8a"
        weapon_text = "#ffffff"
        counter_fill = "#2563eb"
    else:  # cinematic default
        bg_fill = "url(#bgGrad)"
        bg_stroke = "#38bdf8"
        bg_stroke_opacity = "0.4"
        killer_color = "#38bdf8"
        victim_color = "#e2e8f0"
        weapon_bg = "#334155"
        weapon_text = "#f8fafc"
        counter_fill = "#dc2626"

    hs_icon = ""
    if event.headshot:
        hs_icon = (
            '<circle cx="280" cy="24" r="8" fill="none" stroke="#ef4444" stroke-width="2.5"/>'
            '<circle cx="280" cy="24" r="3" fill="#ef4444"/>'
        )

    wallbang_badge = ""
    if event.wallbang:
        wallbang_badge = (
            '<rect x="296" y="14" width="20" height="20" rx="3" fill="#f59e0b" opacity="0.9"/>'
            '<text x="306" y="28" font-family="monospace" font-size="11" font-weight="900" '
            'fill="#000" text-anchor="middle">WB</text>'
        )

    noscope_badge = ""
    if event.noscope:
        noscope_badge = (
            '<rect x="320" y="14" width="22" height="20" rx="3" fill="#38bdf8" opacity="0.9"/>'
            '<text x="331" y="28" font-family="monospace" font-size="10" font-weight="900" '
            'fill="#000" text-anchor="middle">NS</text>'
        )

    ace_banner = ""
    if event.is_ace or event.kill_number_in_round >= 5:
        ace_banner = (
            '<g transform="translate(10, 52)">'
            '<rect width="460" height="32" rx="6" fill="url(#goldGrad)" opacity="0.95"/>'
            '<text x="230" y="22" font-family="sans-serif" font-size="14" font-weight="900" '
            'letter-spacing="3" fill="#000" text-anchor="middle">★ A C E — ROUND DOMINATION ★</text>'
            '</g>'
        )

    height = 92 if ace_banner else 48
    weapon_clean = event.weapon.replace("weapon_", "").upper()

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 {height}" width="480" height="{height}">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0f172a" stop-opacity="0.92"/>
      <stop offset="100%" stop-color="#1e293b" stop-opacity="0.80"/>
    </linearGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="50%" stop-color="#fef08a"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="480" height="46" rx="8" fill="{bg_fill}" stroke="{bg_stroke}" stroke-width="1.5" stroke-opacity="{bg_stroke_opacity}"/>
  
  <!-- Killer -->
  <text x="16" y="29" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="15" font-weight="800" fill="{killer_color}">{event.killer_name}</text>
  
  <!-- Weapon -->
  <rect x="180" y="12" width="70" height="22" rx="4" fill="{weapon_bg}" opacity="0.85"/>
  <text x="215" y="27" font-family="monospace" font-size="11" font-weight="700" fill="{weapon_text}" text-anchor="middle">{weapon_clean}</text>
  
  <!-- Modifiers -->
  {hs_icon}
  {wallbang_badge}
  {noscope_badge}
  
  <!-- Victim -->
  <text x="350" y="29" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="15" font-weight="700" fill="{victim_color}">{event.victim_name}</text>
  
  <!-- Counter badge -->
  <circle cx="458" cy="23" r="11" fill="{counter_fill}"/>
  <text x="458" y="27" font-family="sans-serif" font-size="11" font-weight="900" fill="#fff" text-anchor="middle">{event.kill_number_in_round}</text>
  
  {ace_banner}
</svg>"""
    return svg


def generate_multikill_badge(count: int, is_ace: bool = False, style: str = "cinematic") -> str:
    """Generate a glowing multikill status badge (2K, 3K, 4K, ACE)."""
    if count >= 5 or is_ace:
        label = "ACE"
        subtitle = "ROUND DOMINATION"
        grad_color1 = "#f59e0b"
        grad_color2 = "#fef08a"
        border_color = "#f59e0b"
    elif count == 4:
        label = "QUAD KILL"
        subtitle = "4 ELIMINATIONS"
        grad_color1 = "#ea580c"
        grad_color2 = "#fed7aa"
        border_color = "#f97316"
    elif count == 3:
        label = "TRIPLE KILL"
        subtitle = "3 ELIMINATIONS"
        grad_color1 = "#9333ea"
        grad_color2 = "#e9d5ff"
        border_color = "#a855f7"
    else:
        label = "DOUBLE KILL"
        subtitle = "2 ELIMINATIONS"
        grad_color1 = "#0284c7"
        grad_color2 = "#bae6fd"
        border_color = "#38bdf8"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 100" width="320" height="100">
  <defs>
    <linearGradient id="mkGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{grad_color1}"/>
      <stop offset="100%" stop-color="{grad_color2}"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="316" height="96" rx="12" fill="#0f172a" fill-opacity="0.9" stroke="{border_color}" stroke-width="2.5"/>
  <text x="160" y="48" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="28" font-weight="900" letter-spacing="2" fill="url(#mkGrad)" text-anchor="middle">{label}</text>
  <text x="160" y="76" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="800" letter-spacing="4" fill="#94a3b8" text-anchor="middle">{subtitle}</text>
</svg>"""
    return svg


def export_svg_killfeed(
    events: list[OverlayKillEvent],
    output_dir: pathlib.Path,
    style: str = "cinematic",
) -> list[pathlib.Path]:
    """Generate individual SVG overlay files for each kill event."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[pathlib.Path] = []
    for idx, ev in enumerate(events):
        svg_content = generate_svg_killfeed_badge(ev, style=style)
        out_file = output_dir / f"overlay_kill_{idx+1:02d}_t{ev.tick}.svg"
        out_file.write_text(svg_content, encoding="utf-8")
        generated.append(out_file)

    # If there's an ace or high multikill, generate multikill badge
    if events and (events[-1].is_ace or len(events) >= 2):
        mk_svg = generate_multikill_badge(len(events), is_ace=events[-1].is_ace, style=style)
        mk_file = output_dir / f"overlay_multikill_badge_{len(events)}k.svg"
        mk_file.write_text(mk_svg, encoding="utf-8")
        generated.append(mk_file)

    return generated


def render_killfeed_png_badge(
    event: OverlayKillEvent,
    output_path: pathlib.Path,
    style: str = "cinematic",
    width: int = 540,
    height: int = 64,
) -> pathlib.Path:
    """Render a crisp, transparent RGBA PNG killfeed badge for video track overlay."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Card background (rounded rect)
    bg_color = (15, 23, 42, 220)  # Dark slate glass
    border_color = (56, 189, 248, 200) if style == "cinematic" else (244, 63, 94, 220)
    draw.rounded_rectangle([(4, 4), (width - 4, height - 4)], radius=8, fill=bg_color, outline=border_color, width=2)

    # Killer Name
    killer_color = (56, 189, 248, 255) if style == "cinematic" else (244, 63, 94, 255)
    draw.text((20, 20), event.killer_name[:16], fill=killer_color)

    # Weapon Badge
    weapon_clean = event.weapon.replace("weapon_", "").upper()
    draw.rounded_rectangle([(190, 16), (280, 48)], radius=4, fill=(51, 65, 85, 230))
    draw.text((205, 24), weapon_clean[:8], fill=(248, 250, 252, 255))

    # Modifier indicator
    mod_x = 295
    if event.headshot:
        draw.ellipse([(mod_x, 22), (mod_x + 18, 40)], outline=(239, 68, 68, 255), width=2)
        draw.ellipse([(mod_x + 6, 28), (mod_x + 12, 34)], fill=(239, 68, 68, 255))
        mod_x += 24
    if event.wallbang:
        draw.rounded_rectangle([(mod_x, 20), (mod_x + 24, 42)], radius=3, fill=(245, 158, 11, 230))
        draw.text((mod_x + 4, 24), "WB", fill=(0, 0, 0, 255))
        mod_x += 28

    # Victim Name
    victim_color = (226, 232, 240, 255)
    draw.text((360, 20), event.victim_name[:14], fill=victim_color)

    # Counter circle
    counter_color = (220, 38, 38, 255) if event.kill_number_in_round < 5 else (245, 158, 11, 255)
    draw.ellipse([(width - 44, 18), (width - 16, 46)], fill=counter_color)
    draw.text((width - 34, 24), str(event.kill_number_in_round), fill=(255, 255, 255, 255))

    img.save(str(output_path), "PNG")
    return output_path
