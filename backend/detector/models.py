"""Data models for the Highlight Detector.

All time values are in TICKS.  Never mix ticks and seconds.

HighlightType: str-based enum so values serialize cleanly to JSON.
DetectorSettings: configurable knobs with sensible defaults.
HighlightCandidate: one detected highlight moment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class HighlightType(str, Enum):
    """Type of highlight detected.

    Values are plain strings so they JSON-serialize without extra work.
    """

    KILL = "kill"
    MULTIKILL_2K = "multikill_2k"
    MULTIKILL_3K = "multikill_3k"
    MULTIKILL_4K = "multikill_4k"
    ACE = "ace"
    CLUTCH_CANDIDATE = "clutch_candidate"


@dataclass
class DetectorSettings:
    """Configurable thresholds for highlight detection.

    All window/roll values are in ticks (128 ticks ≈ 1 second at 128-tick rate).
    """

    # Multi-kill: all kills by same player must fall within this window
    multikill_window_ticks: int = 128 * 15  # 15 seconds

    # Maximum gap between consecutive kills in a multikill (fragmovie rule: max 4 seconds)
    max_kill_gap_ticks: int = 128 * 4  # 4 seconds

    # Clip pre-roll before the first kill tick
    pre_roll_ticks: int = 128 * 7  # 7 seconds

    # Clip post-roll after the last kill tick
    post_roll_ticks: int = 128 * 4  # 4 seconds

    # Clutch: minimum enemy count alive at start of sequence (heuristic)
    min_clutch_enemies: int = 2

    # Expected team size per side (used for clutch alive-count bootstrap)
    round_team_size: int = 5


@dataclass
class HighlightCandidate:
    """A single detected highlight moment.

    `id` is deterministic and used for deduplication:
        f"{round_num}_{type.value}_{pov_steam_id}_{kill_start_tick}"

    `is_heuristic` must be True for clutch detection (alive counts approximated).

    `clip_start_tick` / `clip_end_tick` are clamped to round boundaries:
        start >= round.start_tick
        end   <= round.official_end_tick  (fallback: round.end_tick)

    `tags` contains only confirmed, non-None attributes from kill events.
    """

    id: str
    highlight_type: HighlightType
    round_num: int
    pov_steam_id: Optional[str]      # main player being highlighted
    pov_name: Optional[str]

    # Ticks of the first/last kill in this sequence
    kill_start_tick: int
    kill_end_tick: int

    # Clamped clip boundaries for renderer
    clip_start_tick: int
    clip_end_tick: int

    kill_count: int

    # Tags derived only from confirmed True values (never from None)
    tags: list[str] = field(default_factory=list)

    # Heuristic flag — must be True for clutch candidates
    is_heuristic: bool = False

    # Human-readable explanation of detection logic / caveats
    detection_reason: str = ""
