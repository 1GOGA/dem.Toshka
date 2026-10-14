"""Pydantic schemas for the CS2 Highlights Studio REST API."""

from __future__ import annotations

import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class PlayerDTO(BaseModel):
    id: int
    demo_id: int
    name: str
    steam_id: Optional[str] = None
    team: Optional[str] = None


class RoundDTO(BaseModel):
    id: int
    round_num: int
    start_tick: int
    freeze_end_tick: Optional[int] = None
    end_tick: int
    official_end_tick: Optional[int] = None
    winner: Optional[str] = None
    reason: Optional[str] = None
    bomb_plant_tick: Optional[int] = None
    bomb_site: Optional[str] = None


class KillDTO(BaseModel):
    id: int
    demo_id: int
    tick: int
    round_num: Optional[int] = None
    attacker_name: Optional[str] = None
    attacker_steam_id: Optional[str] = None
    attacker_team: Optional[str] = None
    victim_name: Optional[str] = None
    victim_steam_id: Optional[str] = None
    victim_team: Optional[str] = None
    weapon: Optional[str] = None
    headshot: Optional[bool] = None
    noscope: Optional[bool] = None
    thru_smoke: Optional[bool] = None
    wallbang: Optional[bool] = None
    is_suicide: bool = False
    is_teamkill: bool = False


class HighlightDTO(BaseModel):
    id: str
    demo_id: int
    highlight_type: str
    round_num: int
    pov_steam_id: Optional[str] = None
    pov_name: Optional[str] = None
    kill_start_tick: int
    kill_end_tick: int
    clip_start_tick: int
    clip_end_tick: int
    kill_count: int
    tags: list[str] = Field(default_factory=list)
    is_heuristic: bool = False
    detection_reason: str = ""
    radar_x: Optional[float] = None
    radar_y: Optional[float] = None
    victim_radar_x: Optional[float] = None
    victim_radar_y: Optional[float] = None
    radar_level: Optional[str] = "upper"


class DemoSummary(BaseModel):
    id: int
    file_path: str
    fingerprint: str
    map_name: Optional[str] = None
    tickrate: int
    duration_seconds: Optional[float] = None
    schema_version: str
    created_at: datetime.datetime
    rounds_count: int = 0
    players_count: int = 0
    highlights_count: int = 0


class ParseDemoRequest(BaseModel):
    demo_path: str


class PlayerStatsDTO(BaseModel):
    name: str
    steam_id: Optional[str] = None
    team: Optional[str] = None
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    suicides: int = 0
    teamkills: int = 0
    headshots: int = 0
    headshot_pct: float = 0.0
    kd_ratio: float = 0.0
    kpr: float = 0.0
    dpr: float = 0.0
    differential: int = 0
    performance_rating: float = 1.0
    faceit_level: int = 5
    kast_pct: float = 0.0
    opening_kills: int = 0
    opening_deaths: int = 0
    multikills: dict[str, int] = Field(default_factory=dict)
    clutches_won: int = 0
    adr: Optional[float] = None
    weapon_kills: dict[str, int] = Field(default_factory=dict)
    kills_by_round: dict[int, int] = Field(default_factory=dict)


class MatchScoreboardDTO(BaseModel):
    total_rounds: int
    score: dict[str, int]
    players: list[PlayerStatsDTO]
    weapon_summary: dict[str, int]


class RenderJobCreateRequest(BaseModel):
    demo_id: int
    highlight_ids: list[str]
    resolution: str = "1080p"  # "1080p" | "720p" | "1280x960" | "1440x1080" | "1024x768" | "4:3"
    aspect_ratio: str = "16:9"  # "16:9" | "4:3"
    stretch_4_3: bool = False
    fps: int = 60              # 60 | 30
    pre_roll_seconds: float = 4.0
    post_roll_seconds: float = 2.5
    perspective: str = "attacker"  # "attacker" | "victim" | "specific_player" | "dynamic_killcam"
    perspective_steam_id: Optional[str] = None
    xray: bool = True
    hud_mode: str = "full"     # "real" | "huge_esports" | "huge_killfeed" | "full" | "killfeed_only" | "none"
    hud_scale: Optional[float] = None # 0.95 | 1.05 | 1.15 | 1.25
    custom_crosshair: bool = True
    fov: Optional[int] = None  # 68 | 90 | 95 | 100 | 105
    viewmodel_fov: Optional[int] = None  # 60 | 68
    crosshair_preset: str = "pro_cyan"  # "pro_cyan" | "green_clean" | "dot" | "minimal_white" | "hidden" | "default"
    crosshair_color: Optional[str] = None  # "cyan" | "green" | "yellow" | "white" | "pink" | "red" | "blue"
    radar_mode: str = "broadcast"  # "dynamic_large" | "broadcast_giant" | "broadcast" | "player_focus" | "compact" | "hidden"


class RenderJobDTO(BaseModel):
    id: str
    demo_id: int
    highlight_id: Optional[str] = None
    status: str
    progress: float
    output_path: Optional[str] = None
    error_summary: Optional[str] = None
    log_path: Optional[str] = None
    settings_json: Optional[str] = None
    created_at: datetime.datetime


class MontageCreateRequest(BaseModel):
    job_ids: Optional[list[str]] = None
    demo_id: Optional[int] = None
    filenames: Optional[list[str]] = None


class MontageDTO(BaseModel):
    success: bool
    montage_path: str
    filename: str
    duration_seconds: float
    clip_count: int


class PlayerErrorDTO(BaseModel):
    round_num: int
    tick: int
    error_type: str
    title: str
    description: str
    severity: str


class PlayerAnalyticsDTO(BaseModel):
    name: str
    steam_id: Optional[str] = None
    team: Optional[str] = None
    total_rounds: int
    performance_rating: float
    kills: int
    deaths: int
    assists: int
    kd_ratio: float
    kpr: float
    dpr: float
    headshot_pct: float
    kast_pct: float
    swing_winrate_pct: float
    crosshair_placement_score: float
    first_bullet_accuracy_pct: float
    spray_control_pct: float
    opening_duels_won: int
    opening_duels_lost: int
    opening_winrate_pct: float
    trade_kills: int
    trade_kill_pct: float
    traded_deaths: int
    traded_death_pct: float
    clutches_won: int
    clutches_attempted: int
    clutch_winrate_pct: float
    multikill_rounds: dict[str, int] = Field(default_factory=dict)
    errors: list[PlayerErrorDTO] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    advice: list[str] = Field(default_factory=list)
    map_impact_score: float = 1.0
    fun_badges: list[dict[str, str]] = Field(default_factory=list)



