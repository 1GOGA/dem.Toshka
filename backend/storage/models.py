"""SQLAlchemy ORM models for CS2 Highlights Studio storage layer.

Uses SQLAlchemy 2.0 style DeclarativeBase.
All tables are tied to a parsed Demo record via foreign keys.
Fingerprint and schema_version ensure cached demo validity.
"""

from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DemoModel(Base):
    __tablename__ = "demos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    map_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tickrate: Mapped[int] = mapped_column(Integer, nullable=False, default=128)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    # Relationships
    players: Mapped[list["PlayerModel"]] = relationship(
        "PlayerModel", back_populates="demo", cascade="all, delete-orphan"
    )
    rounds: Mapped[list["RoundModel"]] = relationship(
        "RoundModel", back_populates="demo", cascade="all, delete-orphan"
    )
    kills: Mapped[list["KillEventModel"]] = relationship(
        "KillEventModel", back_populates="demo", cascade="all, delete-orphan"
    )
    highlights: Mapped[list["HighlightModel"]] = relationship(
        "HighlightModel", back_populates="demo", cascade="all, delete-orphan"
    )
    render_jobs: Mapped[list["RenderJobModel"]] = relationship(
        "RenderJobModel", back_populates="demo", cascade="all, delete-orphan"
    )
    analysis_projects: Mapped[list["AnalysisProjectModel"]] = relationship(
        "AnalysisProjectModel", back_populates="demo", cascade="all, delete-orphan"
    )


class PlayerModel(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    demo_id: Mapped[int] = mapped_column(Integer, ForeignKey("demos.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    steam_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    team: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    demo: Mapped["DemoModel"] = relationship("DemoModel", back_populates="players")


class RoundModel(Base):
    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    demo_id: Mapped[int] = mapped_column(Integer, ForeignKey("demos.id", ondelete="CASCADE"), nullable=False, index=True)
    round_num: Mapped[int] = mapped_column(Integer, nullable=False)
    start_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    freeze_end_tick: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    official_end_tick: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    winner: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    bomb_plant_tick: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bomb_site: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    demo: Mapped["DemoModel"] = relationship("DemoModel", back_populates="rounds")


class KillEventModel(Base):
    __tablename__ = "kill_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    demo_id: Mapped[int] = mapped_column(Integer, ForeignKey("demos.id", ondelete="CASCADE"), nullable=False, index=True)
    tick: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    round_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    attacker_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    attacker_steam_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    attacker_team: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    victim_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    victim_steam_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    victim_team: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    weapon: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    headshot: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    hitgroup: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    noscope: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    thru_smoke: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    attacker_blind: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    wallbang: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    assister_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    assister_steam_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    is_suicide: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_teamkill: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    demo: Mapped["DemoModel"] = relationship("DemoModel", back_populates="kills")


class HighlightModel(Base):
    __tablename__ = "highlights"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # deterministic string id
    demo_id: Mapped[int] = mapped_column(Integer, ForeignKey("demos.id", ondelete="CASCADE"), nullable=False, index=True)
    highlight_type: Mapped[str] = mapped_column(String(64), nullable=False)
    round_num: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    pov_steam_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    pov_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    kill_start_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    kill_end_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    clip_start_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    clip_end_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    kill_count: Mapped[int] = mapped_column(Integer, nullable=False)

    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    is_heuristic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    detection_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")

    demo: Mapped["DemoModel"] = relationship("DemoModel", back_populates="highlights")


class RenderJobModel(Base):
    __tablename__ = "render_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    demo_id: Mapped[int] = mapped_column(Integer, ForeignKey("demos.id", ondelete="CASCADE"), nullable=False, index=True)
    highlight_id: Mapped[Optional[str]] = mapped_column(
        String(128), ForeignKey("highlights.id", ondelete="SET NULL"), nullable=True
    )
    settings_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")  # pending/processing/completed/failed
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    output_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    log_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    demo: Mapped["DemoModel"] = relationship("DemoModel", back_populates="render_jobs")


class AnalysisProjectModel(Base):
    __tablename__ = "analysis_projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID string
    demo_id: Mapped[int] = mapped_column(Integer, ForeignKey("demos.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    demo: Mapped["DemoModel"] = relationship("DemoModel", back_populates="analysis_projects")
    drawings: Mapped[list["TacticalDrawingModel"]] = relationship(
        "TacticalDrawingModel", back_populates="project", cascade="all, delete-orphan"
    )
    bookmarks: Mapped[list["BookmarkModel"]] = relationship(
        "BookmarkModel", back_populates="project", cascade="all, delete-orphan"
    )


class TacticalDrawingModel(Base):
    __tablename__ = "tactical_drawings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID string
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("analysis_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    round_num: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tick: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    layer_type: Mapped[str] = mapped_column(String(32), nullable=False)  # 'pen', 'arrow', 'line', 'circle', 'box', 'text'
    color: Mapped[str] = mapped_column(String(32), nullable=False, default="#00f2fe")
    stroke_width: Mapped[float] = mapped_column(Float, nullable=False, default=3.0)
    geometry_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    text_label: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    project: Mapped["AnalysisProjectModel"] = relationship("AnalysisProjectModel", back_populates="drawings")


class BookmarkModel(Base):
    __tablename__ = "bookmarks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID string
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("analysis_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    round_num: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tick: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    player_steamid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="TACTICAL_MISTAKE")
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    project: Mapped["AnalysisProjectModel"] = relationship("AnalysisProjectModel", back_populates="bookmarks")


# Composite indexes for fast queries
Index("ix_kill_events_demo_round", KillEventModel.demo_id, KillEventModel.round_num)
Index("ix_highlights_demo_pov", HighlightModel.demo_id, HighlightModel.pov_steam_id)
Index("ix_drawings_project_round", TacticalDrawingModel.project_id, TacticalDrawingModel.round_num)
Index("ix_bookmarks_project_round", BookmarkModel.project_id, BookmarkModel.round_num)


# =============================================================================
# Phase 4: Multi-Match Player Analytics & Evidence Insights Models
# =============================================================================


class PlayerProfileModel(Base):
    __tablename__ = "player_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # steam_id or UUID
    steam_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(256), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    primary_role: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    match_stats: Mapped[list["PlayerMatchStatsModel"]] = relationship(
        "PlayerMatchStatsModel", back_populates="profile", cascade="all, delete-orphan"
    )
    insights: Mapped[list["PlayerInsightModel"]] = relationship(
        "PlayerInsightModel", back_populates="profile", cascade="all, delete-orphan"
    )


class PlayerMatchStatsModel(Base):
    __tablename__ = "player_match_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_profile_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    demo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("demos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )
    map_name: Mapped[str] = mapped_column(String(128), nullable=False)
    team_side: Mapped[str] = mapped_column(String(16), nullable=False, default="both")
    kills: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deaths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    headshots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    headshot_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    adr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    kast_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    crosshair_placement_error: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    time_to_damage_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    untradeable_deaths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trade_kill_conversion_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    team_flash_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    opening_duel_win_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    clutch_win_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rounds_played: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    profile: Mapped["PlayerProfileModel"] = relationship("PlayerProfileModel", back_populates="match_stats")
    demo: Mapped["DemoModel"] = relationship("DemoModel")


class PlayerInsightModel(Base):
    __tablename__ = "player_insights"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID
    player_profile_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    demo_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # AIM_DUELS, POSITIONING, DECISION_MAKING...
    severity: Mapped[str] = mapped_column(String(32), nullable=False)  # CRITICAL, WARNING, OPTIMIZATION, STRENGTH
    title: Mapped[str] = mapped_column(String(256), nullable=False)

    # 7-component evidence contract
    pattern_description: Mapped[str] = mapped_column(Text, nullable=False)
    sample_size_str: Mapped[str] = mapped_column(String(128), nullable=False)
    objective_metric_str: Mapped[str] = mapped_column(String(256), nullable=False)
    context_conditions_str: Mapped[str] = mapped_column(Text, nullable=False)
    alternative_strategy_str: Mapped[str] = mapped_column(Text, nullable=False)
    impact_estimate_str: Mapped[str] = mapped_column(String(256), nullable=False)
    jump_demo_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    jump_round_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    jump_tick: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    profile: Mapped["PlayerProfileModel"] = relationship("PlayerProfileModel", back_populates="insights")


Index("ix_match_stats_profile", PlayerMatchStatsModel.player_profile_id, PlayerMatchStatsModel.demo_id)
Index("ix_insights_profile", PlayerInsightModel.player_profile_id, PlayerInsightModel.category)


# =============================================================================
# Phase 5: Strategy Book & Tactical Setups Models
# =============================================================================


class StrategyBookModel(Base):
    __tablename__ = "strategy_books"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    map_name: Mapped[str] = mapped_column(String(128), nullable=False)
    team_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    setups: Mapped[list["TacticalSetupModel"]] = relationship(
        "TacticalSetupModel", back_populates="book", cascade="all, delete-orphan"
    )
    lineups: Mapped[list["UtilityLineupModel"]] = relationship(
        "UtilityLineupModel", back_populates="book", cascade="all, delete-orphan"
    )


class TacticalSetupModel(Base):
    __tablename__ = "tactical_setups"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID
    strategy_book_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("strategy_books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)  # ct / t
    phase: Mapped[str] = mapped_column(String(32), nullable=False, default="default")  # default, execute, post_plant...
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tokens_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    drawings_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    book: Mapped["StrategyBookModel"] = relationship("StrategyBookModel", back_populates="setups")


class UtilityLineupModel(Base):
    __tablename__ = "utility_lineups"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID
    strategy_book_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("strategy_books.id", ondelete="CASCADE"), nullable=True, index=True
    )
    map_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(16), nullable=False)  # ct / t
    utility_type: Mapped[str] = mapped_column(String(32), nullable=False)  # smoke, flash, molotov, he
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    throw_type: Mapped[str] = mapped_column(String(32), nullable=False, default="stand")
    pos_x: Mapped[float] = mapped_column(Float, nullable=False)
    pos_y: Mapped[float] = mapped_column(Float, nullable=False)
    target_x: Mapped[float] = mapped_column(Float, nullable=False)
    target_y: Mapped[float] = mapped_column(Float, nullable=False)
    crosshair_desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    book: Mapped[Optional["StrategyBookModel"]] = relationship("StrategyBookModel", back_populates="lineups")


Index("ix_setups_book_phase", TacticalSetupModel.strategy_book_id, TacticalSetupModel.phase)
Index("ix_lineups_map_type", UtilityLineupModel.map_name, UtilityLineupModel.utility_type)

