"""Versioned data models for CS2 Highlights Studio parser output.

All fields that may be absent from the demo are typed Optional[...] and
default to None.  Do NOT mix tick and seconds — they are separate fields.

Schema version is embedded so the storage layer can detect stale cache.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

SCHEMA_VERSION = "1"


@dataclass
class PlayerInfo:
    """Stable, normalised player record.

    `steam_id` may be None for bots or offline/LAN demos where the field is
    absent.  Use `name` only for display; do NOT use it as a stable key.
    """

    name: str
    steam_id: Optional[str]  # None for bots / missing field
    team: Optional[str]      # "ct" | "t" | "spectator" | "unassigned" | None


@dataclass
class KillEvent:
    """A single player_death event from the demo.

    Fields present in Awpy 2.0.2 player_death:
        tick, attacker_name, attacker_steamid, attacker_team_name,
        attacker_X/Y/Z, victim (user_*→victim_*), weapon, headshot,
        hitgroup, assister_name, assister_steamid, noscope, thrusmoke,
        attackerblind, penetrated (wallbang), round_num.

    Fields NOT available in Awpy 2.0.2:
        time_seconds — not provided in kill events; use tick / tickrate if needed.

    CONFIRMED on real CS2 demo (2026-10-05) — special kill encodings:
        weapon='world' (fall damage):
            attacker_steamid == victim_steamid  →  is_suicide=True (engine convention).
            This is a fall-damage death, NOT a deliberate player action.
            Highlight Detector: check weapon to distinguish accidental vs deliberate.

        weapon='planted_c4' (bomb explosion):
            attacker_steamid is None, attacker_name is None.
            Kill occurs AFTER round end_tick, before official_end_tick.
            is_suicide=False, is_teamkill=False.

    is_suicide derivation:
        True if attacker_steam_id == victim_steam_id (includes world/fall damage).
        Use `weapon` to distinguish accidental deaths from deliberate suicides.

    is_teamkill derivation:
        True if same team, not suicide, both teams known.
    """

    tick: int
    round_num: Optional[int]

    # Attacker
    attacker_name: Optional[str]
    attacker_steam_id: Optional[str]
    attacker_team: Optional[str]

    # Victim
    victim_name: Optional[str]
    victim_steam_id: Optional[str]
    victim_team: Optional[str]

    weapon: Optional[str]
    headshot: Optional[bool]
    hitgroup: Optional[str]       # e.g. "head", "chest", "stomach" …
    noscope: Optional[bool]
    thru_smoke: Optional[bool]
    attacker_blind: Optional[bool]
    wallbang: Optional[bool]      # penetrated > 0

    # Assister (may be absent)
    assister_name: Optional[str]
    assister_steam_id: Optional[str]

    # Derived flags — computed by the adapter, never guessed
    is_suicide: bool = field(init=False)
    is_teamkill: bool = field(init=False)

    def __post_init__(self) -> None:
        # Suicide: attacker and victim are the same player
        self.is_suicide = bool(
            self.attacker_steam_id
            and self.victim_steam_id
            and self.attacker_steam_id == self.victim_steam_id
        )
        # Team-kill: same team, not a suicide, both sides are known
        self.is_teamkill = bool(
            not self.is_suicide
            and self.attacker_team
            and self.victim_team
            and self.attacker_team == self.victim_team
        )


@dataclass
class RoundInfo:
    """One match round with boundary ticks and outcome.

    CONFIRMED on real CS2 demo (2026-10-05):
      - end_tick:          tick of round_end event (game declares result).
      - official_end_tick: tick of round_officially_ended event.
      - Bomb-explosion kills (weapon='planted_c4') occur AFTER end_tick but
        BEFORE official_end_tick.
      - Awpy assigns round_num using official_end_tick as the upper bound.

    Rule for all downstream code (Highlight Detector, storage, UI):
      Use official_end_tick as the authoritative round upper boundary.
      Fall back to end_tick only if official_end_tick is None.
    """

    round_num: int
    start_tick: int
    freeze_end_tick: Optional[int]
    end_tick: int
    official_end_tick: Optional[int]
    winner: Optional[str]       # "ct" | "t" | None
    reason: Optional[str]       # human-readable from ROUND_END_REASON_MAP
    bomb_plant_tick: Optional[int]
    bomb_site: Optional[str]    # "bombsite_a" | "bombsite_b" | "not_planted"


@dataclass
class ParsedDemo:
    """Top-level result returned by the adapter after parsing one .dem file.

    `schema_version` must be checked by storage layer before using cached data.
    """

    schema_version: str
    demo_path: str
    map_name: Optional[str]
    tickrate: int
    rounds: list[RoundInfo]
    players: list[PlayerInfo]
    kills: list[KillEvent]
    # Raw header dict — keep for debugging; do NOT expose to UI directly
    _raw_header: dict = field(default_factory=dict, repr=False)
