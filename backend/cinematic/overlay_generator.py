"""Graphical Overlays and Custom Killfeed Generator.

Generates high-contrast esports/cinematic kill-feed graphics and DaVinci Resolve
Fusion text/graphics compositions based on real demo events.
"""

from __future__ import annotations

import pathlib
from typing import Any, Optional

from backend.cinematic.models import OverlayKillEvent


def generate_svg_killfeed_badge(event: OverlayKillEvent, style: str = "cinematic_916") -> str:
    """Generate high-resolution transparent SVG killfeed badge."""
    hs_icon = (
        '<circle cx="280" cy="24" r="8" fill="none" stroke="#ef4444" stroke-width="2.5"/>'
        '<circle cx="280" cy="24" r="3" fill="#ef4444"/>'
        if event.headshot else ""
    )
    wallbang_badge = (
        '<rect x="296" y="14" width="20" height="20" rx="3" fill="#f59e0b" opacity="0.9"/>'
        '<text x="306" y="28" font-family="monospace" font-size="11" font-weight="900" '
        'fill="#000" text-anchor="middle">WB</text>'
        if event.wallbang else ""
    )
    noscope_badge = (
        '<rect x="320" y="14" width="22" height="20" rx="3" fill="#38bdf8" opacity="0.9"/>'
        '<text x="331" y="28" font-family="monospace" font-size="10" font-weight="900" '
        'fill="#000" text-anchor="middle">NS</text>'
        if event.noscope else ""
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

    height = 90 if ace_banner else 48
    weapon_clean = event.weapon.replace("weapon_", "").upper()

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 {height}" width="480" height="{height}">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0f172a" stop-opacity="0.90"/>
      <stop offset="100%" stop-color="#1e293b" stop-opacity="0.75"/>
    </linearGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="50%" stop-color="#fef08a"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="480" height="46" rx="8" fill="url(#bgGrad)" stroke="#38bdf8" stroke-width="1.5" stroke-opacity="0.4"/>
  
  <!-- Killer -->
  <text x="16" y="29" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="15" font-weight="800" fill="#38bdf8">{event.killer_name}</text>
  
  <!-- Weapon -->
  <rect x="180" y="12" width="70" height="22" rx="4" fill="#334155" opacity="0.8"/>
  <text x="215" y="27" font-family="monospace" font-size="11" font-weight="700" fill="#f8fafc" text-anchor="middle">{weapon_clean}</text>
  
  <!-- Modifiers -->
  {hs_icon}
  {wallbang_badge}
  {noscope_badge}
  
  <!-- Victim -->
  <text x="350" y="29" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="15" font-weight="700" fill="#e2e8f0">{event.victim_name}</text>
  
  <!-- Counter badge -->
  <circle cx="458" cy="23" r="11" fill="#dc2626"/>
  <text x="458" y="27" font-family="sans-serif" font-size="11" font-weight="900" fill="#fff" text-anchor="middle">{event.kill_number_in_round}</text>
  
  {ace_banner}
</svg>"""
    return svg


def export_svg_killfeed(
    events: list[OverlayKillEvent],
    output_dir: pathlib.Path,
) -> list[pathlib.Path]:
    """Generate individual SVG overlay files for each kill event."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[pathlib.Path] = []
    for idx, ev in enumerate(events):
        svg_content = generate_svg_killfeed_badge(ev)
        out_file = output_dir / f"overlay_kill_{idx+1:02d}_t{ev.tick}.svg"
        out_file.write_text(svg_content, encoding="utf-8")
        generated.append(out_file)
    return generated
