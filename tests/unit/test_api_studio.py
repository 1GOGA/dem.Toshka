"""Unit tests for the Studio Bridge and Social Drafts API endpoint functions."""

from __future__ import annotations

import pathlib
import pytest
from sqlalchemy.orm import Session

from backend.api.main import (
    create_social_draft,
    create_studio_job,
    get_studio_job_status,
    get_studio_status,
)
from backend.api.schemas import CreateStudioJobRequest, SocialDraftRequest
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.models import DemoModel, HighlightModel


@pytest.fixture
def db_session(tmp_path: pathlib.Path) -> Session:
    db_path = tmp_path / "test_api_direct.db"
    engine = create_db_engine(f"sqlite:///{db_path}")
    init_db(engine)
    SessionFactory = get_session_factory(engine)
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


class TestStudioAPI:
    def test_get_studio_status_endpoint(self):
        res = get_studio_status()
        assert hasattr(res, "available")
        assert res.manifest_schema == "1.0.0"
        assert isinstance(res.supported_profiles, list)

    def test_create_social_draft_endpoint(self):
        req = SocialDraftRequest(
            player_name="pytoshka_",
            map_name="de_mirage",
            highlight_type="ace",
            primary_weapon="awp",
            round_num=10,
            kill_count=5,
            score=96.0,
            duration_sec=8.5,
            platform="telegram",
        )
        res = create_social_draft(req)
        assert res.platform == "telegram"
        assert "pytoshka_" in res.text
        assert "Mirage" in res.text
        assert "AWP" in res.text

    def test_create_studio_job_flow_endpoint(self, db_session: Session):
        # Seed test demo and highlight
        demo = DemoModel(
            file_path="C:\\CS2\\test.dem",
            fingerprint="test_sha_unique_12345",
            map_name="de_dust2",
            tickrate=128,
            duration_seconds=120.0,
            schema_version="1",
        )
        db_session.add(demo)
        db_session.commit()

        hl = HighlightModel(
            id="hl_test_direct_01",
            demo_id=demo.id,
            highlight_type="ace",
            round_num=3,
            pov_steam_id="76561198000000001",
            pov_name="pytoshka_",
            kill_start_tick=5000,
            kill_end_tick=5800,
            clip_start_tick=4800,
            clip_end_tick=6000,
            kill_count=5,
            tags_json='["ace", "dust2"]',
            is_heuristic=False,
            detection_reason="5K ACE in round 3",
        )
        db_session.add(hl)
        db_session.commit()

        # Call create_studio_job
        req = CreateStudioJobRequest(
            demo_id=demo.id,
            highlight_id=hl.id,
            profile="clean_cinematic",
            resolution="1920x1080",
            fps=60,
            hud_mode="killfeed_only",
            user_notes="Direct endpoint test",
        )
        resp = create_studio_job(req, db=db_session)
        assert resp.status == "pending"
        assert resp.job_id.startswith("job_")
        assert pathlib.Path(resp.manifest_path).exists()

        # Query job status
        st_res = get_studio_job_status(resp.job_id)
        assert st_res["job_id"] == resp.job_id
        assert st_res["status"] == "pending"
