"""Event normalization and fast tick indexing for Counter-Strike 2 demos."""

from __future__ import annotations

import bisect
from typing import Optional

from backend.parser.models import KillEvent, ParsedDemo, RoundInfo


class EventNormalizer:
    """Normalizes raw weapon names, teams, and event flags."""

    WEAPON_CLEAN_MAP = {
        "weapon_ak47": "ak47",
        "weapon_m4a1": "m4a1",
        "weapon_m4a1_silencer": "m4a1_silencer",
        "weapon_awp": "awp",
        "weapon_deagle": "deagle",
        "weapon_usp_silencer": "usp_silencer",
        "weapon_glock": "glock",
        "weapon_mp9": "mp9",
        "weapon_mac10": "mac10",
        "inferno": "molotov",
    }

    @classmethod
    def clean_weapon_name(cls, weapon: Optional[str]) -> str:
        """Strip engine prefixes and map to canonical weapon identifier."""
        if not weapon:
            return "unknown"
        w = weapon.lower().strip()
        if w in cls.WEAPON_CLEAN_MAP:
            return cls.WEAPON_CLEAN_MAP[w]
        if w.startswith("weapon_"):
            return w[7:]
        return w

    @staticmethod
    def normalize_team(team: Optional[str]) -> str:
        """Standardize team string to 'ct', 't', or 'spec'."""
        if not team:
            return "unknown"
        t = team.lower().strip()
        if "ct" in t or "counter" in t:
            return "ct"
        if "t" in t or "terror" in t:
            return "t"
        return "spec"

    @staticmethod
    def is_fall_damage(kill: KillEvent) -> bool:
        """Determine if death was caused by gravity / fall damage rather than player combat."""
        return kill.weapon == "world" or (
            kill.attacker_steam_id is not None
            and kill.attacker_steam_id == kill.victim_steam_id
            and kill.weapon in ("world", None)
        )

    @staticmethod
    def tick_to_seconds(tick: int, tickrate: float = 64.0) -> float:
        """Convert tick integer to elapsed seconds with safe denominator guard."""
        rate = max(1.0, float(tickrate))
        return tick / rate


class TickIndex:
    """High-performance chronological index for demo navigation and queries."""

    def __init__(self, demo: ParsedDemo) -> None:
        self.demo = demo
        self.tickrate = max(1.0, float(demo.tickrate) if demo.tickrate else 64.0)

        # Sorted lists for binary searching
        self._rounds: list[RoundInfo] = sorted(demo.rounds, key=lambda r: r.start_tick)
        self._round_starts: list[int] = [r.start_tick for r in self._rounds]

        self._kills: list[KillEvent] = sorted(demo.kills, key=lambda k: k.tick)
        self._kill_ticks: list[int] = [k.tick for k in self._kills]

        # Player-keyed index
        self._kills_by_attacker: dict[str, list[KillEvent]] = {}
        for k in self._kills:
            if k.attacker_steam_id:
                self._kills_by_attacker.setdefault(k.attacker_steam_id, []).append(k)

    def get_round_for_tick(self, tick: int) -> Optional[RoundInfo]:
        """Find the active round containing the specified demo tick via binary search."""
        if not self._rounds:
            return None

        idx = bisect.bisect_right(self._round_starts, tick) - 1
        if idx >= 0:
            candidate = self._rounds[idx]
            if candidate.start_tick <= tick <= candidate.end_tick:
                return candidate
        return None

    def get_kills_in_range(self, start_tick: int, end_tick: int) -> list[KillEvent]:
        """Return all kill events occurring between start_tick and end_tick inclusive."""
        if not self._kill_ticks:
            return []

        left = bisect.bisect_left(self._kill_ticks, start_tick)
        right = bisect.bisect_right(self._kill_ticks, end_tick)
        return self._kills[left:right]

    def get_nearest_kill(self, tick: int) -> Optional[KillEvent]:
        """Return the closest kill event in time relative to a given tick."""
        if not self._kills:
            return None

        idx = bisect.bisect_left(self._kill_ticks, tick)
        if idx == 0:
            return self._kills[0]
        if idx >= len(self._kills):
            return self._kills[-1]

        before = self._kills[idx - 1]
        after = self._kills[idx]
        return before if abs(tick - before.tick) <= abs(after.tick - tick) else after

    def get_kills_by_attacker(self, steam_id: str) -> list[KillEvent]:
        """Return chronological list of all kills scored by a player."""
        return self._kills_by_attacker.get(steam_id, [])
