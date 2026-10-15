"""Data structures for Video Rendering tasks and results."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RenderTask:
    """Specification for rendering a single highlight moment into an MP4 clip."""

    task_id: str
    demo_path: pathlib.Path
    start_tick: int
    end_tick: int
    pov_steam_id: Optional[str]
    pov_name: Optional[str]
    tickrate: int = 128
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 60
    output_path: pathlib.Path = field(
        default_factory=lambda: pathlib.Path("renders") / "clip.mp4"
    )
    xray: bool = True
    hud_mode: str = "full"  # "real" | "huge_esports" | "huge_killfeed" | "full" | "killfeed_only" | "none"
    perspective: str = "attacker"  # "attacker" | "victim" | "specific_player"
    custom_crosshair: bool = True
    fov: Optional[int] = None  # e.g. 68, 90, 95, 100, 105
    viewmodel_fov: Optional[int] = None  # e.g. 60, 68 (tournament movie viewmodel)
    crosshair_preset: str = "pro_cyan"  # "pro_cyan" | "green_clean" | "dot" | "minimal_white" | "hidden" | "default"
    crosshair_color: Optional[str] = None  # "cyan" | "green" | "yellow" | "white" | "pink" | "red" | "blue"
    radar_mode: str = "broadcast"  # "dynamic_large" | "broadcast_giant" | "broadcast" | "player_focus" | "compact" | "hidden"
    hud_scale: Optional[float] = None  # e.g. 0.95, 1.0, 1.15, 1.25
    overhead_mode: Optional[bool] = None
    killfeed_only: Optional[bool] = None
    teamcounter_mode: Optional[bool] = None
    camera_switches: list[tuple[int, Optional[str], Optional[str]]] = field(default_factory=list)
    # Tournament Killcam Replay (Victim death POV -> Rewind -> Hero POV)
    is_killcam_replay: bool = False
    killcam_victim_steam_id: Optional[str] = None
    killcam_victim_name: Optional[str] = None
    killcam_victim_start_tick: Optional[int] = None
    killcam_victim_end_tick: Optional[int] = None
    killcam_hero_start_tick: Optional[int] = None

    @property
    def duration_seconds(self) -> float:
        """Expected clip duration based on tickrange."""
        return max(1.0, float(self.end_tick - self.start_tick) / max(1, self.tickrate))


@dataclass
class RenderResult:
    """Outcome of a video render job."""

    success: bool
    output_path: Optional[pathlib.Path]
    duration_seconds: float
    error_message: Optional[str] = None
    log_file: Optional[pathlib.Path] = None
    has_audio: bool = False
    warning_message: Optional[str] = None


