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


# Composite indexes for fast queries
Index("ix_kill_events_demo_round", KillEventModel.demo_id, KillEventModel.round_num)
Index("ix_highlights_demo_pov", HighlightModel.demo_id, HighlightModel.pov_steam_id)
