"""Awpy 2.0.2 adapter — translates Awpy Polars DataFrames into our models.

This is the ONLY place that knows about Awpy internals.  All other code
uses `models.ParsedDemo`.  If we ever swap parsers, only this file changes.

Verified against Awpy 2.0.2 source:
  - demo.py  (Demo class, DEFAULT_EVENT_LIST, DEFAULT_PLAYER_PROPS)
  - parsers/events.py  (parse_kills renames user_* → victim_*)
  - parsers/rounds.py  (create_round_df columns: round_num, start, freeze_end,
                         end, official_end, winner, reason, bomb_plant, bomb_site)
  - converters.py  (HITGROUP_MAP, ROUND_END_REASON_MAP, TEAM_MAP)

Known limitations of Awpy 2.0.2:
  - player_death does NOT include time_seconds; use tick / tickrate.
  - `penetrated` column name may vary by CS2 version — we guard with .get().
  - SteamID may be None for bots.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _safe_str(value) -> Optional[str]:
    """Convert a value to str, returning None for None/NaN/empty."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s and s.lower() not in ("none", "nan", "") else None


def _safe_bool(value) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return None


def _safe_int(value) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _row_get(row: dict, *keys) -> Optional[object]:
    """Try multiple column name aliases, return first non-None hit."""
    for k in keys:
        v = row.get(k)
        if v is not None:
            return v
    return None


# ---------------------------------------------------------------------------
# Public adapter entry point
# ---------------------------------------------------------------------------

def parse_demo(path: Path) -> "ParsedDemo":  # noqa: F821 — imported below
    """Parse a CS2 .dem file with Awpy 2.0.2.

    Args:
        path: Absolute path to the .dem file.  Caller must validate existence
              and extension before calling this function.

    Returns:
        ParsedDemo with all available fields populated.  Missing fields are None.

    Raises:
        DemoParseError: wraps any Awpy / demoparser2 exception with a message
                        safe to show in the UI.
    """
    # Import here so models can be imported without awpy installed in tests
    from awpy.demo import Demo
    from awpy.converters import ROUND_END_REASON_MAP
    from backend.parser.models import (
        KillEvent, ParsedDemo, PlayerInfo, RoundInfo, SCHEMA_VERSION
    )
    from backend.parser.errors import DemoParseError

    try:
        dem = Demo(path=path)
        dem.parse()
    except FileNotFoundError:
        raise  # caller already checks; re-raise as-is
    except Exception as exc:
        raise DemoParseError(f"Awpy failed to parse demo: {exc}") from exc

    header = dem.header or {}
    tickrate: int = dem.tickrate

    # ------------------------------------------------------------------ rounds
    rounds: list[RoundInfo] = []
    try:
        for row in dem.rounds.to_dicts():
            rounds.append(RoundInfo(
                round_num=int(row["round_num"]),
                start_tick=int(row["start"]),
                freeze_end_tick=_safe_int(row.get("freeze_end")),
                end_tick=int(row["end"]),
                official_end_tick=_safe_int(row.get("official_end")),
                winner=_safe_str(row.get("winner")),
                reason=_safe_str(
                    ROUND_END_REASON_MAP.get(row.get("reason")) if row.get("reason") is not None else None
                ),
                bomb_plant_tick=_safe_int(row.get("bomb_plant")),
                bomb_site=_safe_str(row.get("bomb_site")),
            ))
    except Exception as exc:
        logger.warning("Could not parse rounds: %s", exc)

    # ------------------------------------------------------------------ players
    # Build from ticks DataFrame (has steamid, name, side)
    players: list[PlayerInfo] = []
    try:
        player_rows = (
            dem.ticks
            .select(["name", "steamid", "side"])
            .unique(subset=["steamid"])
            .to_dicts()
        )
        for row in player_rows:
            players.append(PlayerInfo(
                name=_safe_str(row.get("name")) or "unknown",
                steam_id=_safe_str(row.get("steamid")),
                team=_safe_str(row.get("side")),
            ))
    except Exception as exc:
        logger.warning("Could not parse players: %s", exc)

    # ------------------------------------------------------------------ kills
    kills: list[KillEvent] = []
    try:
        for row in dem.kills.to_dicts():
            # Awpy 2.0.2: parse_kills renames user_* → victim_*
            # wallbang = penetrated > 0  (column may be absent in some demos)
            penetrated = row.get("penetrated")
            wallbang: Optional[bool] = (
                bool(int(penetrated) > 0)
                if penetrated is not None
                else None
            )
            kills.append(KillEvent(
                tick=int(row["tick"]),
                round_num=_safe_int(row.get("round_num")),
                attacker_name=_safe_str(row.get("attacker_name")),
                attacker_steam_id=_safe_str(row.get("attacker_steamid")),
                attacker_team=_safe_str(row.get("attacker_team_name")),
                victim_name=_safe_str(row.get("victim_name")),
                victim_steam_id=_safe_str(row.get("victim_steamid")),
                victim_team=_safe_str(row.get("victim_team_name")),
                weapon=_safe_str(row.get("weapon")),
                headshot=_safe_bool(row.get("headshot")),
                hitgroup=_safe_str(row.get("hitgroup")),
                noscope=_safe_bool(row.get("noscope")),
                thru_smoke=_safe_bool(row.get("thrusmoke")),
                attacker_blind=_safe_bool(row.get("attackerblind")),
                wallbang=wallbang,
                assister_name=_safe_str(row.get("assister_name")),
                assister_steam_id=_safe_str(row.get("assister_steamid")),
            ))
    except Exception as exc:
        logger.warning("Could not parse kills: %s", exc)

    map_name = _safe_str(header.get("map_name"))

    return ParsedDemo(
        schema_version=SCHEMA_VERSION,
        demo_path=str(path),
        map_name=map_name,
        tickrate=tickrate,
        rounds=rounds,
        players=players,
        kills=kills,
        _raw_header=header,
    )
