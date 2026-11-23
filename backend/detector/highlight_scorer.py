"""Explainable multi-factor highlight scoring engine.

Calculates composite excitement scores for CS2 clips based on kill volume,
weapon prestige, timing tempo, headshot precision, clutch context, and wallbangs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from backend.parser.models import KillEvent


@dataclass
class ScoreFactor:
    """An individual contributor to the composite highlight score."""
    name: str
    points: float
    description: str


@dataclass
class ScoreBreakdown:
    """Detailed, explainable score breakdown with display badges."""
    total_score: float
    base_score: float
    bonus_score: float
    factors: list[ScoreFactor] = field(default_factory=list)
    badges: list[str] = field(default_factory=list)

    @property
    def normalized_100(self) -> float:
        """Clamp score to a standard 0-100 rating scale."""
        return max(0.0, min(100.0, self.total_score))


class SmartHighlightScorer:
    """Calculates explainable cinematic scores for candidate plays."""

    WEAPON_WEIGHTS = {
        "knife": 50.0,
        "taser": 40.0,
        "zeus": 40.0,
        "deagle": 25.0,
        "awp": 20.0,
        "ak47": 10.0,
        "m4a1": 10.0,
        "m4a1_silencer": 10.0,
        "usp_silencer": 15.0,
        "glock": 15.0,
        "molotov": 20.0,
        "hegrenade": 25.0,
    }

    def __init__(self, tickrate: float = 64.0) -> None:
        self.tickrate = max(1.0, float(tickrate))

    def score_sequence(
        self,
        kills: list[KillEvent],
        clutch_opponents: int = 0,
    ) -> ScoreBreakdown:
        """Score a cluster of kills with itemized explainable factors."""
        factors: list[ScoreFactor] = []
        badges: list[str] = []

        kill_count = len(kills)
        if kill_count == 0:
            return ScoreBreakdown(total_score=0.0, base_score=0.0, bonus_score=0.0)

        # 1. Base Kill Volume
        base_pts = kill_count * 10.0
        factors.append(ScoreFactor("Kill Count", base_pts, f"{kill_count} kills (+{base_pts:.0f} pts)"))

        if kill_count >= 5:
            factors.append(ScoreFactor("Ace Achievement", 45.0, "Full team elimination ACE (+45 pts)"))
            badges.append("ACE")
        elif kill_count == 4:
            factors.append(ScoreFactor("4K Multikill", 30.0, "Quad kill round (+30 pts)"))
            badges.append("4K")
        elif kill_count == 3:
            factors.append(ScoreFactor("3K Triple", 15.0, "Triple kill round (+15 pts)"))
            badges.append("3K")

        # 2. Precision & Special Kills
        headshots = sum(1 for k in kills if k.headshot)
        if headshots > 0:
            hs_pts = headshots * 5.0
            factors.append(ScoreFactor("Headshot Precision", hs_pts, f"{headshots} headshot kills (+{hs_pts:.0f} pts)"))
            if headshots == kill_count and kill_count >= 3:
                badges.append("100% HS")

        wallbangs = sum(1 for k in kills if k.wallbang)
        if wallbangs > 0:
            wb_pts = wallbangs * 10.0
            factors.append(ScoreFactor("Wallbang", wb_pts, f"{wallbangs} penetration kills (+{wb_pts:.0f} pts)"))
            badges.append("Wallbang")

        noscopes = sum(1 for k in kills if k.noscope)
        if noscopes > 0:
            ns_pts = noscopes * 15.0
            factors.append(ScoreFactor("Noscope", ns_pts, f"{noscopes} noscope sniper kills (+{ns_pts:.0f} pts)"))
            badges.append("Noscope")

        thru_smokes = sum(1 for k in kills if k.thru_smoke)
        if thru_smokes > 0:
            smoke_pts = thru_smokes * 10.0
            factors.append(ScoreFactor("Through Smoke", smoke_pts, f"{thru_smokes} through-smoke kills (+{smoke_pts:.0f} pts)"))
            badges.append("Smoke Kill")

        # 3. Weapon Prestige
        highest_prestige = 0.0
        prestige_weapon = ""
        for k in kills:
            w_name = (k.weapon or "").lower().replace("weapon_", "")
            weight = self.WEAPON_WEIGHTS.get(w_name, 5.0)
            if weight > highest_prestige:
                highest_prestige = weight
                prestige_weapon = w_name

        if highest_prestige >= 25.0:
            factors.append(ScoreFactor("Prestige Weapon", highest_prestige, f"High skill weapon ({prestige_weapon}) (+{highest_prestige:.0f} pts)"))
            badges.append(f"{prestige_weapon.upper()} FOCUS")

        # 4. Tempo / Time Delta
        sorted_kills = sorted(kills, key=lambda k: k.tick)
        rapid_pairs = 0
        for i in range(len(sorted_kills) - 1):
            delta_s = (sorted_kills[i + 1].tick - sorted_kills[i].tick) / self.tickrate
            if delta_s <= 1.5:
                rapid_pairs += 1

        if rapid_pairs > 0:
            tempo_pts = rapid_pairs * 8.0
            factors.append(ScoreFactor("Rapid Tempo", tempo_pts, f"{rapid_pairs} rapid succession kills (+{tempo_pts:.0f} pts)"))
            badges.append("Rapid Tempo")

        # 5. Clutch Bonus
        if clutch_opponents >= 1:
            clutch_pts = 15.0 + (clutch_opponents * 10.0)
            factors.append(ScoreFactor(f"1v{clutch_opponents} Clutch", clutch_pts, f"Won 1v{clutch_opponents} clutch scenario (+{clutch_pts:.0f} pts)"))
            badges.append(f"1v{clutch_opponents} Clutch")

        total = sum(f.points for f in factors)
        base = base_pts
        bonus = total - base

        return ScoreBreakdown(
            total_score=total,
            base_score=base,
            bonus_score=bonus,
            factors=factors,
            badges=badges,
        )
