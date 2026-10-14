"""CS2 Highlight Detector — Stage D.

Public API:
    detect_highlights(parsed_demo, settings=None) -> list[HighlightCandidate]

Design rules enforced here:
  - All times are in TICKS.  Never use seconds.
  - Kills with round_num=None are skipped entirely.
  - Suicides (is_suicide=True) do NOT count toward an attacker's multikill.
  - Teamkills do NOT count as enemy kills.
  - Clip bounds are clamped: [round.start_tick, round.official_end_tick].
  - ACE supersedes 4K supersedes 3K supersedes 2K (maximal deduplication).
  - Clutch detection is HEURISTIC — is_heuristic=True always set.
  - Tags extracted only from confirmed True values (None fields → no tag).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from backend.parser.models import KillEvent, ParsedDemo, RoundInfo
from backend.detector.models import (
    DetectorSettings,
    HighlightCandidate,
    HighlightType,
)

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def detect_highlights(
    parsed_demo: ParsedDemo,
    settings: Optional[DetectorSettings] = None,
) -> list[HighlightCandidate]:
    """Detect highlight candidates from a parsed demo.

    Returns a list of HighlightCandidate, deduplicated and sorted by
    (round_num, kill_start_tick).

    Skips kills with round_num=None.
    """
    if settings is None:
        settings = DetectorSettings()

    # Build fast lookup: round_num → RoundInfo
    round_map: dict[int, RoundInfo] = {r.round_num: r for r in parsed_demo.rounds}

    # Group kills by round; skip round_num=None
    kills_by_round: dict[int, list[KillEvent]] = _group_kills_by_round(parsed_demo.kills)

    candidates: list[HighlightCandidate] = []

    for round_num, kills in kills_by_round.items():
        if round_num not in round_map:
            # Round appeared in kills but not in rounds list — skip defensively
            continue

        bounds = round_map[round_num]
        round_candidates = _detect_round_highlights(round_num, kills, bounds, settings)
        candidates.extend(round_candidates)

    candidates = _deduplicate(candidates)
    candidates.sort(key=lambda h: (h.round_num, h.kill_start_tick))
    return candidates


# ---------------------------------------------------------------------------
# Per-round detection
# ---------------------------------------------------------------------------


def _detect_round_highlights(
    round_num: int,
    kills: list[KillEvent],
    bounds: RoundInfo,
    settings: DetectorSettings,
) -> list[HighlightCandidate]:
    results: list[HighlightCandidate] = []

    multikill_highlights = _detect_multikills(round_num, kills, bounds, settings)
    results.extend(multikill_highlights)

    clutch_highlights = _detect_clutch_candidates(round_num, kills, bounds, settings)
    results.extend(clutch_highlights)

    return results


# ---------------------------------------------------------------------------
# Multi-kill detection
# ---------------------------------------------------------------------------


def _detect_multikills(
    round_num: int,
    kills: list[KillEvent],
    bounds: RoundInfo,
    settings: DetectorSettings,
) -> list[HighlightCandidate]:
    """Detect kill / 2K / 3K / 4K / ACE per attacker in this round."""
    # Group enemy kills by attacker_steam_id (skip suicides, teamkills, no attacker)
    kills_by_attacker: dict[str, list[KillEvent]] = defaultdict(list)

    for kill in kills:
        if kill.attacker_steam_id is None:
            continue
        if kill.is_suicide:
            continue
        if kill.is_teamkill:
            continue
        kills_by_attacker[kill.attacker_steam_id].append(kill)

    candidates: list[HighlightCandidate] = []

    for steam_id, attacker_kills in kills_by_attacker.items():
        # Sort by tick ascending
        attacker_kills.sort(key=lambda k: k.tick)

        # Find the maximal multikill sequence using sliding window & 4-second max gap
        sequences = _find_maximal_multikill_sequences(
            attacker_kills,
            window_ticks=settings.multikill_window_ticks,
            max_kill_gap_ticks=settings.max_kill_gap_ticks,
        )

        for seq in sequences:
            if not seq:
                continue

            kill_start = seq[0].tick
            kill_end = seq[-1].tick
            n = len(seq)

            hl_type = _kill_count_to_type(n)
            clip_start, clip_end = _make_clip_bounds(
                kill_start, kill_end, bounds, settings
            )
            tags = _extract_tags(seq)
            pov_name = seq[0].attacker_name

            candidate = HighlightCandidate(
                id=_make_id(round_num, hl_type, steam_id, kill_start),
                highlight_type=hl_type,
                round_num=round_num,
                pov_steam_id=steam_id,
                pov_name=pov_name,
                kill_start_tick=kill_start,
                kill_end_tick=kill_end,
                clip_start_tick=clip_start,
                clip_end_tick=clip_end,
                kill_count=n,
                tags=tags,
                is_heuristic=False,
                detection_reason=(
                    f"{hl_type.value}: {n} enemy kills by {pov_name!r} "
                    f"within {settings.multikill_window_ticks} ticks (max gap {settings.max_kill_gap_ticks} ticks) in round {round_num}."
                ),
            )
            candidates.append(candidate)

    return candidates


def _find_maximal_multikill_sequences(
    kills: list[KillEvent],
    window_ticks: int,
    max_kill_gap_ticks: int = 128 * 4,
) -> list[list[KillEvent]]:
    """Find maximal, non-overlapping kill sequences where:
    1. All kills fit in window_ticks.
    2. The gap between consecutive kills does NOT exceed max_kill_gap_ticks (default: 4 seconds).

    Strategy:
      - Greedy from left: extend current window as far as possible.
      - Once the gap to previous kill exceeds max_kill_gap_ticks or the total window
        exceeds window_ticks, emit the current sequence and start a new one from the next kill.
      - This guarantees no dull pauses > 4s between kills in multikill highlights.

    Kills must already be sorted ascending by tick.
    """
    if not kills:
        return []

    sequences: list[list[KillEvent]] = []
    current: list[KillEvent] = [kills[0]]

    for kill in kills[1:]:
        gap_to_prev = kill.tick - current[-1].tick
        total_window = kill.tick - current[0].tick

        if gap_to_prev <= max_kill_gap_ticks and total_window <= window_ticks:
            # Within consecutive gap and total window limit — extend
            current.append(kill)
        else:
            # Gap exceeded or window closed — emit current sequence, start new one
            sequences.append(current)
            current = [kill]

    sequences.append(current)
    return sequences


def _kill_count_to_type(n: int) -> HighlightType:
    if n >= 5:
        return HighlightType.ACE
    if n == 4:
        return HighlightType.MULTIKILL_4K
    if n == 3:
        return HighlightType.MULTIKILL_3K
    if n == 2:
        return HighlightType.MULTIKILL_2K
    return HighlightType.KILL


# ---------------------------------------------------------------------------
# Clutch candidate detection (HEURISTIC)
# ---------------------------------------------------------------------------


def _detect_clutch_candidates(
    round_num: int,
    kills: list[KillEvent],
    bounds: RoundInfo,
    settings: DetectorSettings,
) -> list[HighlightCandidate]:
    """Heuristic clutch detection.

    A clutch candidate is a player who kills ≥ min_clutch_enemies enemies
    while outnumbered (enemies alive > allies alive) at the start of their
    kill sequence.

    This is always is_heuristic=True because:
      - Alive counts are reconstructed from kill sequence, not from game state.
      - Disconnected/kicked players are not tracked.
      - We don't have exact alive counts at every tick from Awpy kills alone.
    """
    # Track alive counts as kills happen, per side
    # Start: both sides at round_team_size alive
    ct_alive = settings.round_team_size
    t_alive = settings.round_team_size

    # Adjust alive counts based on all kills to get approximate starting point
    # We simulate forward through kills; alive counts cannot go below 0.
    # Sort kills by tick
    sorted_kills = sorted(kills, key=lambda k: k.tick)

    # Per-player enemy kill sequences (within round), tracking outnumbered state
    # player_steam_id → list of kills
    player_enemy_kills: dict[str, list[KillEvent]] = defaultdict(list)

    for kill in sorted_kills:
        if kill.is_suicide or kill.is_teamkill:
            # Still reduces alive count for victim's team
            victim_side = kill.victim_team
            if victim_side == "ct":
                ct_alive = max(0, ct_alive - 1)
            elif victim_side == "t":
                t_alive = max(0, t_alive - 1)
            continue

        if kill.attacker_steam_id is None:
            # World/bomb kill — reduce victim side alive count
            victim_side = kill.victim_team
            if victim_side == "ct":
                ct_alive = max(0, ct_alive - 1)
            elif victim_side == "t":
                t_alive = max(0, t_alive - 1)
            continue

        # Track the alive state BEFORE this kill is recorded
        attacker_side = kill.attacker_team
        victim_side = kill.victim_team

        # Determine if attacker is outnumbered at start of this kill
        if attacker_side == "ct":
            attacker_alive = ct_alive
            enemy_alive_before = t_alive
        elif attacker_side == "t":
            attacker_alive = t_alive
            enemy_alive_before = ct_alive
        else:
            # Unknown team — can't determine outnumbered state; still record
            attacker_alive = None
            enemy_alive_before = None

        # Record the kill with snapshot info
        kill._clutch_attacker_alive = attacker_alive      # type: ignore[attr-defined]
        kill._clutch_enemy_alive_before = enemy_alive_before  # type: ignore[attr-defined]

        player_enemy_kills[kill.attacker_steam_id].append(kill)

        # Update alive counts after this kill
        if victim_side == "ct":
            ct_alive = max(0, ct_alive - 1)
        elif victim_side == "t":
            t_alive = max(0, t_alive - 1)

    candidates: list[HighlightCandidate] = []

    for steam_id, player_kills in player_enemy_kills.items():
        if len(player_kills) < settings.min_clutch_enemies:
            continue

        # Check if ANY kill in this sequence happened while outnumbered
        # We define "outnumbered at start": attacker_alive < enemy_alive at
        # the time of the FIRST kill in the sequence.
        first_kill = player_kills[0]
        attacker_alive_at_start = getattr(first_kill, "_clutch_attacker_alive", None)
        enemy_alive_at_start = getattr(first_kill, "_clutch_enemy_alive_before", None)

        # If we can't determine sides, still emit as clutch candidate with caveat
        if attacker_alive_at_start is None or enemy_alive_at_start is None:
            is_outnumbered = False
            reason_extra = " (side unknown — alive count not tracked)"
        else:
            is_outnumbered = attacker_alive_at_start < enemy_alive_at_start
            reason_extra = (
                f" ({attacker_alive_at_start} vs {enemy_alive_at_start} at first kill)"
            )

        if not is_outnumbered:
            continue

        kill_start = player_kills[0].tick
        kill_end = player_kills[-1].tick
        n = len(player_kills)

        clip_start, clip_end = _make_clip_bounds(kill_start, kill_end, bounds, settings)
        tags = _extract_tags(player_kills)
        pov_name = player_kills[0].attacker_name

        candidate = HighlightCandidate(
            id=_make_id(round_num, HighlightType.CLUTCH_CANDIDATE, steam_id, kill_start),
            highlight_type=HighlightType.CLUTCH_CANDIDATE,
            round_num=round_num,
            pov_steam_id=steam_id,
            pov_name=pov_name,
            kill_start_tick=kill_start,
            kill_end_tick=kill_end,
            clip_start_tick=clip_start,
            clip_end_tick=clip_end,
            kill_count=n,
            tags=tags,
            is_heuristic=True,
            detection_reason=(
                f"HEURISTIC clutch_candidate: {pov_name!r} killed {n} enemies "
                f"while outnumbered in round {round_num}.{reason_extra}"
            ),
        )
        candidates.append(candidate)

    return candidates


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _group_kills_by_round(kills: list[KillEvent]) -> dict[int, list[KillEvent]]:
    """Group kills by round_num, skipping kills where round_num is None."""
    groups: dict[int, list[KillEvent]] = defaultdict(list)
    for kill in kills:
        if kill.round_num is not None:
            groups[kill.round_num].append(kill)
    return dict(groups)


def _make_clip_bounds(
    kill_start: int,
    kill_end: int,
    bounds: RoundInfo,
    settings: DetectorSettings,
) -> tuple[int, int]:
    """Compute clip start/end ticks clamped to round boundaries.

    clip_start = max(kill_start - pre_roll_ticks, round.start_tick)
    clip_end   = min(kill_end   + post_roll_ticks, round.official_end_tick or round.end_tick)
    """
    round_upper = (
        bounds.official_end_tick
        if bounds.official_end_tick is not None
        else bounds.end_tick
    )
    clip_start = max(kill_start - settings.pre_roll_ticks, bounds.start_tick)
    clip_end = min(kill_end + settings.post_roll_ticks, round_upper)
    return clip_start, clip_end


def _extract_tags(kills: list[KillEvent]) -> list[str]:
    """Return confirmed highlight tags from a list of kill events.

    Only tags where the relevant field is explicitly True are included.
    None fields are ignored — they never produce a tag.
    """
    tags: set[str] = set()
    for kill in kills:
        if kill.headshot is True:
            tags.add("headshot")
        if kill.wallbang is True:
            tags.add("wallbang")
        if kill.noscope is True:
            tags.add("noscope")
        if kill.thru_smoke is True:
            tags.add("thru_smoke")
        if kill.attacker_blind is True:
            tags.add("blind")
    return sorted(tags)  # sorted for determinism


def _make_id(
    round_num: int,
    hl_type: HighlightType,
    steam_id: str,
    kill_start_tick: int,
) -> str:
    """Deterministic ID for deduplication."""
    return f"{round_num}_{hl_type.value}_{steam_id}_{kill_start_tick}"


def _deduplicate(candidates: list[HighlightCandidate]) -> list[HighlightCandidate]:
    """Remove duplicate IDs, keeping the first occurrence.

    Because _find_maximal_multikill_sequences produces non-overlapping
    sequences, same-round/same-attacker overlaps shouldn't arise from multikill.
    This guard handles edge cases and clutch/multikill ID collisions.

    Type priority for same (round, pov_steam_id, kill_start_tick):
      ACE > 4K > 3K > 2K > KILL > CLUTCH_CANDIDATE
    If two candidates share the same ID, the one with higher priority wins.
    """
    _TYPE_PRIORITY = {
        HighlightType.ACE: 6,
        HighlightType.MULTIKILL_4K: 5,
        HighlightType.MULTIKILL_3K: 4,
        HighlightType.MULTIKILL_2K: 3,
        HighlightType.KILL: 2,
        HighlightType.CLUTCH_CANDIDATE: 1,
    }
    seen: dict[str, HighlightCandidate] = {}
    for c in candidates:
        if c.id not in seen:
            seen[c.id] = c
        else:
            existing = seen[c.id]
            if _TYPE_PRIORITY.get(c.highlight_type, 0) > _TYPE_PRIORITY.get(
                existing.highlight_type, 0
            ):
                seen[c.id] = c
    return list(seen.values())
