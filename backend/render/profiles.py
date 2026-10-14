"""Render HUD, Crosshair and Visual Profiles for CS2 Highlights Studio.

Profiles define how the in-game display appears during HLAE recording:
- CLEAN_COMPETITIVE: Killfeed only in top-right, clean static pro crosshair,
  no radar, no health/armor bars, no player avatars, no demo UI, no TrueView.
- CINEMATIC: Absolutely zero HUD/killfeed/crosshair for cinematic fragmovies.
- CUSTOM: User-defined combinations of HUD, X-Ray, Crosshair, and camera perspective.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RenderProfileType(str, Enum):
    CLEAN_COMPETITIVE = "clean_competitive"
    CINEMATIC = "cinematic"
    CUSTOM = "custom"


@dataclass
class RenderProfile:
    name: RenderProfileType
    description: str
    draw_hud: bool
    deathnotices_only: bool
    xray: bool
    custom_crosshair: bool
    trueview_suppressed: bool = True
    demo_ui_suppressed: bool = True
    spec_bindings_suppressed: bool = True


PROFILES: dict[RenderProfileType, RenderProfile] = {
    RenderProfileType.CLEAN_COMPETITIVE: RenderProfile(
        name=RenderProfileType.CLEAN_COMPETITIVE,
        description="Чистый киберспортивный вид: только киллфид в правом углу, без радара, без полосы перемотки и без TrueView",
        draw_hud=True,
        deathnotices_only=True,
        xray=True,
        custom_crosshair=True,
        trueview_suppressed=True,
        demo_ui_suppressed=True,
        spec_bindings_suppressed=True,
    ),
    RenderProfileType.CINEMATIC: RenderProfile(
        name=RenderProfileType.CINEMATIC,
        description="Кинематографичный вид: полный ноу-худ, без прицела, без киллфида, чистый ракурс для мувиков",
        draw_hud=False,
        deathnotices_only=False,
        xray=False,
        custom_crosshair=False,
        trueview_suppressed=True,
        demo_ui_suppressed=True,
        spec_bindings_suppressed=True,
    ),
    RenderProfileType.CUSTOM: RenderProfile(
        name=RenderProfileType.CUSTOM,
        description="Пользовательский профиль с ручным выбором всех параметров",
        draw_hud=True,
        deathnotices_only=False,
        xray=True,
        custom_crosshair=True,
        trueview_suppressed=True,
        demo_ui_suppressed=True,
        spec_bindings_suppressed=True,
    ),
}


def get_profile(profile_type: str | RenderProfileType) -> RenderProfile:
    """Return configured profile or fallback to Clean Competitive."""
    try:
        ptype = RenderProfileType(profile_type)
        return PROFILES.get(ptype, PROFILES[RenderProfileType.CLEAN_COMPETITIVE])
    except ValueError:
        return PROFILES[RenderProfileType.CLEAN_COMPETITIVE]

