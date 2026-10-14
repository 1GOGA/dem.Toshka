"""Repository pattern implementation for SQLite storage layer.

Provides transaction-safe operations to save and retrieve parsed demos,
highlights, and render jobs. Handles cache-validation via fingerprint and
schema_version.
"""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from backend.detector.models import HighlightCandidate
from backend.parser.models import ParsedDemo, SCHEMA_VERSION
from backend.storage.models import (
    DemoModel,
    HighlightModel,
    KillEventModel,
    PlayerModel,
    RenderJobModel,
    RoundModel,
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
