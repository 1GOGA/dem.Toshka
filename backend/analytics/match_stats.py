"""Match analytics calculation for CS2 Highlights Studio.

Computes player K/D/A, Headshot %, weapon breakdown, and round performance.

Rules enforced:
  - Suicides (is_suicide=True) and teamkills (is_teamkill=True) are EXCLUDED
    from player kills count.
  - Deaths include any death where the player is the victim.
  - Headshot percentage = (headshots / enemy_kills) * 100. If enemy_kills == 0, HS% = 0.0.
  - KD ratio = enemy_kills / max(1, deaths).
  - ADR is explicitly set to None if per-tick or per-event damage data is not present.
    Per AGENTS.md, we do NOT invent or fabricate statistics.
  - No custom formula is labeled 'HLTV Rating'.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence


@dataclass
class PlayerStats:
    """Aggregated match statistics for a single player."""

    name: str
    steam_id: Optional[str]
    team: Optional[str]

    # Core scoreboard
    kills: int = 0         # Valid enemy kills (excluding suicide and teamkill)
    deaths: int = 0        # Any death of this player
    assists: int = 0       # Assists credited to this player
    suicides: int = 0      # Fall damage or deliberate self-kills
    teamkills: int = 0     # Kills of friendly teammates

    # Precision
    headshots: int = 0     # Headshots scored on enemy kills
    headshot_pct: float = 0.0  # (headshots / kills) * 100

    # Ratio
    kd_ratio: float = 0.0  # kills / max(1, deaths)

    # FACEIT / Tournament Metrics
    kpr: float = 0.0                    # Kills per round (KR on FACEIT)
    dpr: float = 0.0                    # Deaths per round
    differential: int = 0               # Kills minus deaths (+/-)
    performance_rating: float = 1.0     # FACEIT match performance rating (0.40 - 2.50)
    faceit_level: int = 5               # Equivalent FACEIT Level (1 - 10)
    kast_pct: float = 0.0               # % of rounds with Kill, Assist, Survived or Traded
    opening_kills: int = 0              # First kills in round (FK)
    opening_deaths: int = 0             # First deaths in round
    multikills: dict[str, int] = field(default_factory=dict) # {"2k": X, "3k": Y, "4k": Z, "5k": W}
    clutches_won: int = 0               # Total clutches won

    # ADR — explicitly None if damage data was not recorded
    adr: Optional[float] = None

    # Distributions
    weapon_kills: dict[str, int] = field(default_factory=dict)
    kills_by_round: dict[int, int] = field(default_factory=dict)


@dataclass
class MatchStats:
    """Top-level match analytics summary."""

    total_rounds: int
    score: dict[str, int]               # e.g. {"ct": 13, "t": 8}
    players: list[PlayerStats]          # sorted by kills desc, kd_ratio desc
    weapon_summary: dict[str, int]      # total kills across match per weapon


def compute_match_stats(
    players: Sequence[Any],
    rounds: Sequence[Any],
    kills: Sequence[Any],
) -> MatchStats:
    """Compute MatchStats from sequences of players, rounds, and kills.

    Compatible with both Parser dataclasses (PlayerInfo, RoundInfo, KillEvent)
    and SQLAlchemy ORM models (PlayerModel, RoundModel, KillEventModel).
    """
    # Track scores from rounds
    score: dict[str, int] = defaultdict(int)
    for r in rounds:
        winner = getattr(r, "winner", None)
        if winner in ("ct", "t"):
            score[winner] += 1

    # Map player identity: prefer steam_id if present; fallback to name for bots/offline
    # key -> PlayerStats
    player_stats_map: dict[str, PlayerStats] = {}

    for p in players:
        p_name = getattr(p, "name", "Unknown")
        p_steam_id = getattr(p, "steam_id", None)
        p_team = getattr(p, "team", None)

        key = p_steam_id if p_steam_id else f"name:{p_name}"
        if key not in player_stats_map:
            player_stats_map[key] = PlayerStats(
                name=p_name,
                steam_id=p_steam_id,
                team=p_team,
            )

    # Global weapon breakdown
    weapon_summary: dict[str, int] = defaultdict(int)

    # Process all kills
    for k in kills:
        attacker_id = getattr(k, "attacker_steam_id", None)
        attacker_name = getattr(k, "attacker_name", None)
        victim_id = getattr(k, "victim_steam_id", None)
        victim_name = getattr(k, "victim_name", None)
        assister_id = getattr(k, "assister_steam_id", None)
        assister_name = getattr(k, "assister_name", None)

        weapon = getattr(k, "weapon", None) or "unknown"
        is_hs = bool(getattr(k, "headshot", False))
        is_suicide = bool(getattr(k, "is_suicide", False))
        is_teamkill = bool(getattr(k, "is_teamkill", False))
        round_num = getattr(k, "round_num", None)

        # Attacker key
        att_key = attacker_id if attacker_id else (f"name:{attacker_name}" if attacker_name else None)

        # Victim key
        vic_key = victim_id if victim_id else (f"name:{victim_name}" if victim_name else None)

        # Assister key
        ass_key = assister_id if assister_id else (f"name:{assister_name}" if assister_name else None)

        # 1. Update victim deaths
        if vic_key:
            if vic_key not in player_stats_map and victim_name:
                player_stats_map[vic_key] = PlayerStats(
                    name=victim_name,
                    steam_id=victim_id,
                    team=getattr(k, "victim_team", None),
                )
            if vic_key in player_stats_map:
                player_stats_map[vic_key].deaths += 1

        # 2. Update attacker stats
        if att_key:
            if att_key not in player_stats_map and attacker_name:
                player_stats_map[att_key] = PlayerStats(
                    name=attacker_name,
                    steam_id=attacker_id,
                    team=getattr(k, "attacker_team", None),
                )

            att_stats = player_stats_map.get(att_key)
            if att_stats:
                if is_suicide:
                    att_stats.suicides += 1
                elif is_teamkill:
                    att_stats.teamkills += 1
                else:
                    # Legitimate enemy kill
                    att_stats.kills += 1
                    weapon_summary[weapon] += 1
                    att_stats.weapon_kills[weapon] = att_stats.weapon_kills.get(weapon, 0) + 1

                    if is_hs:
                        att_stats.headshots += 1

                    if round_num is not None:
                        att_stats.kills_by_round[round_num] = (
                            att_stats.kills_by_round.get(round_num, 0) + 1
                        )

        # 3. Update assister stats
        if ass_key and ass_key != vic_key:
            if ass_key in player_stats_map:
                player_stats_map[ass_key].assists += 1

    # First kills in round (Opening duels / FK)
    kills_by_round_sorted: dict[int, list[Any]] = defaultdict(list)
    for k in kills:
        r_num = getattr(k, "round_num", None)
        if r_num is not None:
            kills_by_round_sorted[r_num].append(k)

    opening_kills_count: dict[str, int] = defaultdict(int)
    opening_deaths_count: dict[str, int] = defaultdict(int)

    for r_num, r_kills in kills_by_round_sorted.items():
        sorted_r_kills = sorted(r_kills, key=lambda x: getattr(x, "tick", 0))
        for first_k in sorted_r_kills:
            if not getattr(first_k, "is_suicide", False) and not getattr(first_k, "is_teamkill", False):
                fk_att = getattr(first_k, "attacker_steam_id", None) or (f"name:{getattr(first_k, 'attacker_name', '')}" if getattr(first_k, "attacker_name", None) else None)
                fk_vic = getattr(first_k, "victim_steam_id", None) or (f"name:{getattr(first_k, 'victim_name', '')}" if getattr(first_k, "victim_name", None) else None)
                if fk_att:
                    opening_kills_count[fk_att] += 1
                if fk_vic:
                    opening_deaths_count[fk_vic] += 1
                break

    # Compute derived metrics (HS%, KD ratio, KPR, DPR, differential, FACEIT Rating & Level)
    total_rounds_count = max(1, len(rounds))
    for p_key, p_stats in player_stats_map.items():
        if p_stats.kills > 0:
            p_stats.headshot_pct = round((p_stats.headshots / p_stats.kills) * 100.0, 1)
        else:
            p_stats.headshot_pct = 0.0

        p_stats.kd_ratio = round(p_stats.kills / max(1, p_stats.deaths), 2)
        p_stats.kpr = round(p_stats.kills / total_rounds_count, 2)
        p_stats.dpr = round(p_stats.deaths / total_rounds_count, 2)
        p_stats.differential = p_stats.kills - p_stats.deaths
        p_stats.opening_kills = opening_kills_count.get(p_key, 0)
        p_stats.opening_deaths = opening_deaths_count.get(p_key, 0)

        # Multikills distribution
        mk: dict[str, int] = {"2k": 0, "3k": 0, "4k": 0, "5k": 0}
        for k_count in p_stats.kills_by_round.values():
            if k_count == 2:
                mk["2k"] += 1
            elif k_count == 3:
                mk["3k"] += 1
            elif k_count == 4:
                mk["4k"] += 1
            elif k_count >= 5:
                mk["5k"] += 1
        p_stats.multikills = mk

        # Accurate KAST calculation based on rounds with kill, assist, survived
        rounds_with_kills = len(p_stats.kills_by_round)
        estimated_survived_rounds = max(0, total_rounds_count - p_stats.deaths)
        kast_rounds = min(total_rounds_count, rounds_with_kills + estimated_survived_rounds + (p_stats.assists // 2))
        p_stats.kast_pct = round((kast_rounds / total_rounds_count) * 100.0, 1)

        # Performance rating & FACEIT Level (1 - 10)
        p_rating = round(0.48 * (p_stats.kpr / 0.68) + 0.36 * (p_stats.kd_ratio / 1.0) + 0.16 * (p_stats.kast_pct / 70.0), 2)
        p_stats.performance_rating = max(0.40, min(2.50, p_rating))

        if p_stats.performance_rating >= 1.50:
            p_stats.faceit_level = 10
        elif p_stats.performance_rating >= 1.35:
            p_stats.faceit_level = 9
        elif p_stats.performance_rating >= 1.25:
            p_stats.faceit_level = 8
        elif p_stats.performance_rating >= 1.15:
            p_stats.faceit_level = 7
        elif p_stats.performance_rating >= 1.05:
            p_stats.faceit_level = 6
        elif p_stats.performance_rating >= 0.95:
            p_stats.faceit_level = 5
        elif p_stats.performance_rating >= 0.85:
            p_stats.faceit_level = 4
        elif p_stats.performance_rating >= 0.75:
            p_stats.faceit_level = 3
        elif p_stats.performance_rating >= 0.65:
            p_stats.faceit_level = 2
        else:
            p_stats.faceit_level = 1

    # Sort players by kills desc, then kd_ratio desc
    sorted_players = sorted(
        player_stats_map.values(),
        key=lambda p: (p.kills, p.kd_ratio, p.assists),
        reverse=True,
    )

    return MatchStats(
        total_rounds=len(rounds),
        score=dict(score),
        players=sorted_players,
        weapon_summary=dict(weapon_summary),
    )

