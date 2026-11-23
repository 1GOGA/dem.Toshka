"""Repository pattern implementation for SQLite storage layer.

Provides transaction-safe operations to save and retrieve parsed demos,
highlights, and render jobs. Handles cache-validation via fingerprint and
schema_version.
"""

from __future__ import annotations

import json
import uuid
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from backend.detector.models import HighlightCandidate
from backend.parser.models import ParsedDemo, SCHEMA_VERSION
from backend.storage.models import (
    AnalysisProjectModel,
    BookmarkModel,
    DemoModel,
    HighlightModel,
    KillEventModel,
    PlayerInsightModel,
    PlayerMatchStatsModel,
    PlayerModel,
    PlayerProfileModel,
    RenderJobModel,
    RoundModel,
    StrategyBookModel,
    TacticalDrawingModel,
    TacticalSetupModel,
    UtilityLineupModel,
)


class DemoRepository:
    """Handles persistence of parsed demos, highlights, and queries."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_fingerprint(
        self, fingerprint: str, schema_version: Optional[str] = SCHEMA_VERSION
    ) -> Optional[DemoModel]:
        """Retrieve demo by fingerprint.

        If schema_version is specified and differs from the stored version,
        returns None to signal a cache invalidation.
        """
        stmt = (
            select(DemoModel)
            .where(DemoModel.fingerprint == fingerprint)
            .options(
                selectinload(DemoModel.players),
                selectinload(DemoModel.rounds),
                selectinload(DemoModel.highlights),
            )
        )
        demo = self.session.execute(stmt).scalar_one_or_none()

        if demo is None:
            return None

        if schema_version is not None and demo.schema_version != schema_version:
            # Stale schema cache
            return None

        return demo

    def get_by_id(self, demo_id: int) -> Optional[DemoModel]:
        """Retrieve demo by primary key with players, rounds, and highlights loaded."""
        stmt = (
            select(DemoModel)
            .where(DemoModel.id == demo_id)
            .options(
                selectinload(DemoModel.players),
                selectinload(DemoModel.rounds),
                selectinload(DemoModel.highlights),
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_demos(self) -> list[DemoModel]:
        """List all demos sorted by created_at descending."""
        stmt = select(DemoModel).order_by(DemoModel.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def save_demo(
        self,
        parsed_demo: ParsedDemo,
        fingerprint: str,
        highlights: Optional[list[HighlightCandidate]] = None,
    ) -> DemoModel:
        """Persist a ParsedDemo and optional highlights in a single transaction.

        If a demo with the same fingerprint already exists, it is replaced
        cleanly (overwritten).
        """
        # Remove any existing demo with the same fingerprint
        existing = (
            self.session.execute(
                select(DemoModel).where(DemoModel.fingerprint == fingerprint)
            )
            .scalar_one_or_none()
        )
        if existing is not None:
            self.session.delete(existing)
            self.session.flush()

        # Compute match duration in seconds if tickrate > 0 and rounds exist
        duration_seconds: Optional[float] = None
        if parsed_demo.rounds and parsed_demo.tickrate > 0:
            last_round = max(
                parsed_demo.rounds,
                key=lambda r: r.official_end_tick or r.end_tick,
            )
            max_tick = last_round.official_end_tick or last_round.end_tick
            first_round = min(parsed_demo.rounds, key=lambda r: r.start_tick)
            min_tick = first_round.start_tick
            duration_seconds = max(0.0, float(max_tick - min_tick) / parsed_demo.tickrate)

        demo_record = DemoModel(
            file_path=parsed_demo.demo_path,
            fingerprint=fingerprint,
            map_name=parsed_demo.map_name,
            tickrate=parsed_demo.tickrate,
            duration_seconds=duration_seconds,
            schema_version=parsed_demo.schema_version,
        )
        self.session.add(demo_record)
        self.session.flush()  # Populates demo_record.id

        # Add players
        for player in parsed_demo.players:
            p_model = PlayerModel(
                demo_id=demo_record.id,
                name=player.name,
                steam_id=player.steam_id,
                team=player.team,
            )
            self.session.add(p_model)

        # Add rounds
        for r in parsed_demo.rounds:
            r_model = RoundModel(
                demo_id=demo_record.id,
                round_num=r.round_num,
                start_tick=r.start_tick,
                freeze_end_tick=r.freeze_end_tick,
                end_tick=r.end_tick,
                official_end_tick=r.official_end_tick,
                winner=r.winner,
                reason=r.reason,
                bomb_plant_tick=r.bomb_plant_tick,
                bomb_site=r.bomb_site,
            )
            self.session.add(r_model)

        # Add kills
        for k in parsed_demo.kills:
            k_model = KillEventModel(
                demo_id=demo_record.id,
                tick=k.tick,
                round_num=k.round_num,
                attacker_name=k.attacker_name,
                attacker_steam_id=k.attacker_steam_id,
                attacker_team=k.attacker_team,
                victim_name=k.victim_name,
                victim_steam_id=k.victim_steam_id,
                victim_team=k.victim_team,
                weapon=k.weapon,
                headshot=k.headshot,
                hitgroup=k.hitgroup,
                noscope=k.noscope,
                thru_smoke=k.thru_smoke,
                attacker_blind=k.attacker_blind,
                wallbang=k.wallbang,
                assister_name=k.assister_name,
                assister_steam_id=k.assister_steam_id,
                is_suicide=k.is_suicide,
                is_teamkill=k.is_teamkill,
            )
            self.session.add(k_model)

        # Add highlights
        if highlights:
            for h in highlights:
                h_model = HighlightModel(
                    id=h.id,
                    demo_id=demo_record.id,
                    highlight_type=h.highlight_type.value,
                    round_num=h.round_num,
                    pov_steam_id=h.pov_steam_id,
                    pov_name=h.pov_name,
                    kill_start_tick=h.kill_start_tick,
                    kill_end_tick=h.kill_end_tick,
                    clip_start_tick=h.clip_start_tick,
                    clip_end_tick=h.clip_end_tick,
                    kill_count=h.kill_count,
                    tags_json=json.dumps(h.tags),
                    is_heuristic=h.is_heuristic,
                    detection_reason=h.detection_reason,
                )
                self.session.add(h_model)

        self.session.commit()
        return demo_record

    def get_highlights(
        self,
        demo_id: int,
        pov_steam_id: Optional[str] = None,
        highlight_type: Optional[str] = None,
    ) -> list[HighlightModel]:
        """Fetch highlights with optional filters."""
        stmt = select(HighlightModel).where(HighlightModel.demo_id == demo_id)
        if pov_steam_id is not None:
            stmt = stmt.where(HighlightModel.pov_steam_id == pov_steam_id)
        if highlight_type is not None:
            stmt = stmt.where(HighlightModel.highlight_type == highlight_type)
        stmt = stmt.order_by(HighlightModel.round_num, HighlightModel.kill_start_tick)
        return list(self.session.execute(stmt).scalars().all())

    def get_kills(
        self, demo_id: int, round_num: Optional[int] = None
    ) -> list[KillEventModel]:
        """Fetch kill events with optional round filter."""
        stmt = select(KillEventModel).where(KillEventModel.demo_id == demo_id)
        if round_num is not None:
            stmt = stmt.where(KillEventModel.round_num == round_num)
        stmt = stmt.order_by(KillEventModel.tick)
        return list(self.session.execute(stmt).scalars().all())

    def get_players(self, demo_id: int) -> list[PlayerModel]:
        """Fetch players for a demo."""
        stmt = select(PlayerModel).where(PlayerModel.demo_id == demo_id)
        return list(self.session.execute(stmt).scalars().all())

    def get_rounds(self, demo_id: int) -> list[RoundModel]:
        """Fetch rounds for a demo ordered by round number."""
        stmt = select(RoundModel).where(RoundModel.demo_id == demo_id).order_by(RoundModel.round_num)
        return list(self.session.execute(stmt).scalars().all())

    def get_highlight_by_id(self, highlight_id: str) -> Optional[HighlightModel]:
        """Fetch a specific highlight by its unique identifier."""
        stmt = select(HighlightModel).where(HighlightModel.id == highlight_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def create_render_job(
        self,
        job_id: str,
        demo_id: int,
        highlight_id: Optional[str],
        settings_dict: dict,
    ) -> RenderJobModel:
        """Create and persist a new render job in queued/pending state."""
        job = RenderJobModel(
            id=job_id,
            demo_id=demo_id,
            highlight_id=highlight_id,
            settings_json=json.dumps(settings_dict),
            status="pending",
            progress=0.0,
        )
        self.session.add(job)
        self.session.commit()
        return job

    def get_render_job(self, job_id: str) -> Optional[RenderJobModel]:
        """Fetch a render job by its unique ID."""
        stmt = select(RenderJobModel).where(RenderJobModel.id == job_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_render_jobs(self, demo_id: Optional[int] = None) -> list[RenderJobModel]:
        """List render jobs, optionally filtered by demo ID, ordered by created_at desc."""
        stmt = select(RenderJobModel)
        if demo_id is not None:
            stmt = stmt.where(RenderJobModel.demo_id == demo_id)
        stmt = stmt.order_by(RenderJobModel.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def update_render_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        output_path: Optional[str] = None,
        error_summary: Optional[str] = None,
        log_path: Optional[str] = None,
    ) -> Optional[RenderJobModel]:
        """Update the status, progress and outcome of a render job."""
        job = self.get_render_job(job_id)
        if not job:
            return None

        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if output_path is not None:
            job.output_path = output_path
        if error_summary is not None:
            job.error_summary = error_summary
        if log_path is not None:
            job.log_path = log_path

        self.session.commit()
        return job

    def get_active_render_job(
        self, demo_id: int, highlight_id: str
    ) -> Optional[RenderJobModel]:
        """Find an active (pending or running) job for the specified highlight."""
        stmt = (
            select(RenderJobModel)
            .where(
                RenderJobModel.demo_id == demo_id,
                RenderJobModel.highlight_id == highlight_id,
                RenderJobModel.status.in_(["pending", "running"]),
            )
            .order_by(RenderJobModel.created_at.desc())
        )
        return self.session.execute(stmt).scalars().first()

    def get_pending_render_jobs(self) -> list[RenderJobModel]:
        """Fetch all jobs currently in 'pending' status, ordered by created_at asc."""
        stmt = (
            select(RenderJobModel)
            .where(RenderJobModel.status == "pending")
            .order_by(RenderJobModel.created_at.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def reset_stale_running_jobs(self) -> int:
        """Reset any jobs stuck in 'running' to 'failed' on startup so they don't block queues."""
        stmt = (
            select(RenderJobModel)
            .where(RenderJobModel.status == "running")
        )
        running_jobs = list(self.session.execute(stmt).scalars().all())
        for job in running_jobs:
            job.status = "failed"
            job.error_summary = "Server restarted while rendering was in progress"
        if running_jobs:
            self.session.commit()
        return len(running_jobs)

    def cancel_render_job(self, job_id: str) -> Optional[RenderJobModel]:
        """Cancel a pending or running render job."""
        job = self.get_render_job(job_id)
        if not job or job.status in ("completed", "cancelled"):
            return None
        job.status = "cancelled"
        job.error_summary = "Render job was cancelled"
        self.session.commit()
        return job

    def delete_render_job(self, job_id: str) -> bool:
        """Delete a render job record from the database."""
        job = self.get_render_job(job_id)
        if not job:
            return False
        self.session.delete(job)
        self.session.commit()
        return True

    def retry_render_job(self, job_id: str) -> Optional[RenderJobModel]:
        """Reset a failed or cancelled job to pending state for re-execution."""
        job = self.get_render_job(job_id)
        if not job or job.status not in ("failed", "cancelled"):
            return None
        job.status = "pending"
        job.progress = 0.0
        job.error_summary = None
        self.session.commit()
        return job
    def clear_completed_render_jobs(self, demo_id: Optional[int] = None) -> int:
        """Delete finished (completed, failed, cancelled) render jobs from database."""
        stmt = select(RenderJobModel).where(
            RenderJobModel.status.in_(["completed", "failed", "cancelled"])
        )
        if demo_id is not None:
            stmt = stmt.where(RenderJobModel.demo_id == demo_id)
        jobs = list(self.session.execute(stmt).scalars().all())
        for j in jobs:
            self.session.delete(j)
        if jobs:
            self.session.commit()
        return len(jobs)

    # =========================================================================
    # Phase 2: Analysis Projects, Tactical Drawings & Bookmarks
    # =========================================================================

    def create_analysis_project(
        self,
        demo_id: int,
        title: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> AnalysisProjectModel:
        """Create a new analysis project tied to a demo."""
        pid = project_id or str(uuid.uuid4())
        project = AnalysisProjectModel(
            id=pid,
            demo_id=demo_id,
            title=title,
            description=description,
        )
        self.session.add(project)
        self.session.commit()
        return project

    def get_analysis_project(self, project_id: str) -> Optional[AnalysisProjectModel]:
        """Retrieve an analysis project with its drawings and bookmarks eagerly loaded."""
        stmt = (
            select(AnalysisProjectModel)
            .where(AnalysisProjectModel.id == project_id)
            .options(
                selectinload(AnalysisProjectModel.drawings),
                selectinload(AnalysisProjectModel.bookmarks),
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_analysis_projects(self, demo_id: Optional[int] = None) -> list[AnalysisProjectModel]:
        """List all analysis projects, optionally filtered by demo_id."""
        stmt = select(AnalysisProjectModel).order_by(AnalysisProjectModel.updated_at.desc())
        if demo_id is not None:
            stmt = stmt.where(AnalysisProjectModel.demo_id == demo_id)
        return list(self.session.execute(stmt).scalars().all())

    def delete_analysis_project(self, project_id: str) -> bool:
        """Delete an analysis project and all associated drawings/bookmarks."""
        project = self.session.execute(
            select(AnalysisProjectModel).where(AnalysisProjectModel.id == project_id)
        ).scalar_one_or_none()
        if not project:
            return False
        self.session.delete(project)
        self.session.commit()
        return True

    def add_tactical_drawing(
        self,
        project_id: str,
        round_num: int,
        layer_type: str,
        color: str,
        stroke_width: float,
        geometry_json: str,
        tick: Optional[int] = None,
        text_label: Optional[str] = None,
        drawing_id: Optional[str] = None,
    ) -> TacticalDrawingModel:
        """Add a vector drawing shape to an analysis project."""
        did = drawing_id or str(uuid.uuid4())
        drawing = TacticalDrawingModel(
            id=did,
            project_id=project_id,
            round_num=round_num,
            tick=tick,
            layer_type=layer_type,
            color=color,
            stroke_width=stroke_width,
            geometry_json=geometry_json,
            text_label=text_label,
        )
        self.session.add(drawing)
        self.session.commit()
        return drawing

    def delete_tactical_drawing(self, drawing_id: str) -> bool:
        """Delete a single tactical drawing element."""
        drawing = self.session.execute(
            select(TacticalDrawingModel).where(TacticalDrawingModel.id == drawing_id)
        ).scalar_one_or_none()
        if not drawing:
            return False
        self.session.delete(drawing)
        self.session.commit()
        return True

    def get_tactical_drawings(
        self, project_id: str, round_num: Optional[int] = None
    ) -> list[TacticalDrawingModel]:
        """Get all drawings for a project, optionally filtered by round_num."""
        stmt = select(TacticalDrawingModel).where(TacticalDrawingModel.project_id == project_id)
        if round_num is not None:
            stmt = stmt.where(TacticalDrawingModel.round_num == round_num)
        stmt = stmt.order_by(TacticalDrawingModel.created_at.asc())
        return list(self.session.execute(stmt).scalars().all())

    def add_bookmark(
        self,
        project_id: str,
        round_num: int,
        tick: int,
        title: str,
        category: str = "TACTICAL_MISTAKE",
        notes: Optional[str] = None,
        player_steamid: Optional[str] = None,
        bookmark_id: Optional[str] = None,
    ) -> BookmarkModel:
        """Add a tick bookmark to an analysis project."""
        bid = bookmark_id or str(uuid.uuid4())
        bookmark = BookmarkModel(
            id=bid,
            project_id=project_id,
            round_num=round_num,
            tick=tick,
            category=category,
            title=title,
            notes=notes,
            player_steamid=player_steamid,
        )
        self.session.add(bookmark)
        self.session.commit()
        return bookmark

    def delete_bookmark(self, bookmark_id: str) -> bool:
        """Delete a bookmark."""
        bookmark = self.session.execute(
            select(BookmarkModel).where(BookmarkModel.id == bookmark_id)
        ).scalar_one_or_none()
        if not bookmark:
            return False
        self.session.delete(bookmark)
        self.session.commit()
        return True

    def get_bookmarks(
        self, project_id: str, round_num: Optional[int] = None
    ) -> list[BookmarkModel]:
        """Get all bookmarks for a project, optionally filtered by round_num."""
        stmt = select(BookmarkModel).where(BookmarkModel.project_id == project_id)
        if round_num is not None:
            stmt = stmt.where(BookmarkModel.round_num == round_num)
        stmt = stmt.order_by(BookmarkModel.tick.asc())
        return list(self.session.execute(stmt).scalars().all())

    # -------------------------------------------------------------------------
    # Phase 4: Multi-Match Player Analytics & Profiles Repository Methods
    # -------------------------------------------------------------------------

    def get_or_create_player_profile(
        self,
        steam_id: str,
        nickname: str,
        avatar_url: Optional[str] = None,
        primary_role: Optional[str] = None,
    ) -> PlayerProfileModel:
        """Fetch existing player profile by steam_id or create a new profile."""
        stmt = select(PlayerProfileModel).where(PlayerProfileModel.steam_id == steam_id)
        profile = self.session.execute(stmt).scalar_one_or_none()
        if not profile:
            profile = PlayerProfileModel(
                id=f"prof_{steam_id}",
                steam_id=steam_id,
                nickname=nickname,
                avatar_url=avatar_url,
                primary_role=primary_role or "Rifler",
            )
            self.session.add(profile)
            self.session.commit()
            self.session.refresh(profile)
        elif nickname and profile.nickname != nickname:
            profile.nickname = nickname
            if avatar_url:
                profile.avatar_url = avatar_url
            if primary_role:
                profile.primary_role = primary_role
            self.session.commit()
            self.session.refresh(profile)
        return profile

    def get_player_profile(self, steam_id_or_id: str) -> Optional[PlayerProfileModel]:
        """Fetch player profile by profile_id or steam_id."""
        stmt = select(PlayerProfileModel).where(
            (PlayerProfileModel.id == steam_id_or_id) | (PlayerProfileModel.steam_id == steam_id_or_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_player_profiles(self) -> list[PlayerProfileModel]:
        """List all tracked player profiles."""
        stmt = select(PlayerProfileModel).order_by(PlayerProfileModel.updated_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def record_player_match_stats(
        self,
        player_profile_id: str,
        demo_id: int,
        stats: dict,
    ) -> PlayerMatchStatsModel:
        """Record or update match performance statistics for a player profile."""
        stmt = select(PlayerMatchStatsModel).where(
            PlayerMatchStatsModel.player_profile_id == player_profile_id,
            PlayerMatchStatsModel.demo_id == demo_id,
        )
        record = self.session.execute(stmt).scalar_one_or_none()
        if not record:
            record = PlayerMatchStatsModel(
                player_profile_id=player_profile_id,
                demo_id=demo_id,
                map_name=stats.get("map_name", "unknown"),
                team_side=stats.get("team_side", "both"),
                kills=stats.get("kills", 0),
                deaths=stats.get("deaths", 0),
                assists=stats.get("assists", 0),
                headshots=stats.get("headshots", 0),
                headshot_pct=stats.get("headshot_pct", 0.0),
                adr=stats.get("adr", 0.0),
                rating=stats.get("rating", 1.0),
                kast_pct=stats.get("kast_pct", 0.0),
                crosshair_placement_error=stats.get("crosshair_placement_error", 0.0),
                time_to_damage_ms=stats.get("time_to_damage_ms", 0.0),
                untradeable_deaths=stats.get("untradeable_deaths", 0),
                trade_kill_conversion_pct=stats.get("trade_kill_conversion_pct", 0.0),
                team_flash_ratio=stats.get("team_flash_ratio", 0.0),
                opening_duel_win_pct=stats.get("opening_duel_win_pct", 0.0),
                clutch_win_pct=stats.get("clutch_win_pct", 0.0),
                rounds_played=stats.get("rounds_played", 0),
            )
            self.session.add(record)
        else:
            for k, v in stats.items():
                if hasattr(record, k):
                    setattr(record, k, v)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_player_multi_match_stats(self, player_profile_id: str) -> list[PlayerMatchStatsModel]:
        """Fetch all match stats recorded for this player profile."""
        stmt = (
            select(PlayerMatchStatsModel)
            .where(PlayerMatchStatsModel.player_profile_id == player_profile_id)
            .order_by(PlayerMatchStatsModel.match_date.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def add_player_insight(
        self,
        player_profile_id: str,
        insight_data: dict,
    ) -> PlayerInsightModel:
        """Store an evidence-based recommendation insight adhering to the 7-component schema."""
        insight = PlayerInsightModel(
            id=str(uuid.uuid4()),
            player_profile_id=player_profile_id,
            demo_id=insight_data.get("demo_id"),
            category=insight_data["category"],
            severity=insight_data.get("severity", "WARNING"),
            title=insight_data["title"],
            pattern_description=insight_data["pattern_description"],
            sample_size_str=insight_data["sample_size_str"],
            objective_metric_str=insight_data["objective_metric_str"],
            context_conditions_str=insight_data["context_conditions_str"],
            alternative_strategy_str=insight_data["alternative_strategy_str"],
            impact_estimate_str=insight_data["impact_estimate_str"],
            jump_demo_id=insight_data.get("jump_demo_id"),
            jump_round_num=insight_data.get("jump_round_num"),
            jump_tick=insight_data.get("jump_tick"),
        )
        self.session.add(insight)
        self.session.commit()
        self.session.refresh(insight)
        return insight

    def get_player_insights(
        self,
        player_profile_id: str,
        category: Optional[str] = None,
    ) -> list[PlayerInsightModel]:
        """Get generated evidence-based insights for a player profile."""
        stmt = select(PlayerInsightModel).where(PlayerInsightModel.player_profile_id == player_profile_id)
        if category:
            stmt = stmt.where(PlayerInsightModel.category == category)
        stmt = stmt.order_by(PlayerInsightModel.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    # -------------------------------------------------------------------------
    # Phase 5: Strategy Book & Tactical Setups Repository Methods
    # -------------------------------------------------------------------------

    def create_strategy_book(
        self,
        title: str,
        map_name: str,
        team_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> StrategyBookModel:
        """Create a new strategy playbook."""
        book = StrategyBookModel(
            id=str(uuid.uuid4()),
            title=title,
            map_name=map_name,
            team_name=team_name,
            description=description,
        )
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book

    def get_strategy_book(self, book_id: str) -> Optional[StrategyBookModel]:
        """Fetch strategy book with its setups and lineups."""
        stmt = (
            select(StrategyBookModel)
            .where(StrategyBookModel.id == book_id)
            .options(selectinload(StrategyBookModel.setups), selectinload(StrategyBookModel.lineups))
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_strategy_books(self, map_name: Optional[str] = None) -> list[StrategyBookModel]:
        """List all strategy books, optionally filtered by map."""
        stmt = select(StrategyBookModel)
        if map_name:
            stmt = stmt.where(StrategyBookModel.map_name == map_name)
        stmt = stmt.order_by(StrategyBookModel.updated_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def delete_strategy_book(self, book_id: str) -> bool:
        """Delete a strategy book."""
        book = self.session.execute(select(StrategyBookModel).where(StrategyBookModel.id == book_id)).scalar_one_or_none()
        if not book:
            return False
        self.session.delete(book)
        self.session.commit()
        return True

    def add_tactical_setup(
        self,
        strategy_book_id: str,
        title: str,
        side: str,
        phase: str,
        description: Optional[str] = None,
        tokens_json: str = "[]",
        drawings_json: str = "[]",
    ) -> TacticalSetupModel:
        """Add a tactical setup to a strategy book."""
        setup = TacticalSetupModel(
            id=str(uuid.uuid4()),
            strategy_book_id=strategy_book_id,
            title=title,
            side=side,
            phase=phase,
            description=description,
            tokens_json=tokens_json,
            drawings_json=drawings_json,
        )
        self.session.add(setup)
        self.session.commit()
        self.session.refresh(setup)
        return setup

    def delete_tactical_setup(self, setup_id: str) -> bool:
        """Delete a tactical setup."""
        setup = self.session.execute(select(TacticalSetupModel).where(TacticalSetupModel.id == setup_id)).scalar_one_or_none()
        if not setup:
            return False
        self.session.delete(setup)
        self.session.commit()
        return True

    def add_utility_lineup(
        self,
        map_name: str,
        side: str,
        utility_type: str,
        title: str,
        pos_x: float,
        pos_y: float,
        target_x: float,
        target_y: float,
        throw_type: str = "stand",
        crosshair_desc: Optional[str] = None,
        strategy_book_id: Optional[str] = None,
    ) -> UtilityLineupModel:
        """Add a grenade lineup."""
        lineup = UtilityLineupModel(
            id=str(uuid.uuid4()),
            strategy_book_id=strategy_book_id,
            map_name=map_name,
            side=side,
            utility_type=utility_type,
            title=title,
            throw_type=throw_type,
            pos_x=pos_x,
            pos_y=pos_y,
            target_x=target_x,
            target_y=target_y,
            crosshair_desc=crosshair_desc,
        )
        self.session.add(lineup)
        self.session.commit()
        self.session.refresh(lineup)
        return lineup

    def get_utility_lineups(
        self,
        map_name: str,
        utility_type: Optional[str] = None,
        side: Optional[str] = None,
    ) -> list[UtilityLineupModel]:
        """Get grenade lineups for a map."""
        stmt = select(UtilityLineupModel).where(UtilityLineupModel.map_name == map_name)
        if utility_type:
            stmt = stmt.where(UtilityLineupModel.utility_type == utility_type)
        if side:
            stmt = stmt.where(UtilityLineupModel.side == side)
        stmt = stmt.order_by(UtilityLineupModel.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())
