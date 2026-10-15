"""Unit tests for FastAPI endpoints (Stage F).

Tests health check, demo listing, demo retrieval, highlights filtering,
scoreboard retrieval, and render jobs queue creation using an isolated
in-memory SQLite database.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend.api.main import (
    create_render_jobs,
    create_montage_endpoint,
    get_demo,
    get_highlights,
    get_job_video,
    get_kills,
    get_match_stats,
    get_montage_video,
    get_player_analytics,
    get_players,
    get_render_by_filename,
    get_render_job,
    get_rounds,
    health_check,
    list_demos,
    list_render_jobs,
    parse_demo_endpoint,
    retry_failed_jobs_endpoint,
    retry_render_job_endpoint,
)
from backend.api.schemas import MontageCreateRequest, ParseDemoRequest, RenderJobCreateRequest
from backend.detector.models import HighlightCandidate, HighlightType
from backend.parser.models import KillEvent, ParsedDemo, PlayerInfo, RoundInfo, SCHEMA_VERSION
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.repository import DemoRepository


@pytest.fixture
def db_session():
    """In-memory SQLite session for testing API endpoints."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    with session_factory() as sess:
        yield sess


def seed_demo(session) -> int:
    repo = DemoRepository(session)
    p1 = PlayerInfo(name="Alice", steam_id="STEAM_1", team="ct")
    p2 = PlayerInfo(name="Bob", steam_id="STEAM_2", team="t")

    r1 = RoundInfo(
        round_num=1,
        start_tick=1000,
        freeze_end_tick=1200,
        end_tick=5000,
        official_end_tick=5200,
        winner="ct",
        reason="ct_killed",
        bomb_plant_tick=None,
        bomb_site=None,
    )

    k1 = KillEvent(
        tick=2500,
        round_num=1,
        attacker_name="Alice",
        attacker_steam_id="STEAM_1",
        attacker_team="ct",
        victim_name="Bob",
        victim_steam_id="STEAM_2",
        victim_team="t",
        weapon="ak47",
        headshot=True,
        hitgroup="head",
        noscope=False,
        thru_smoke=False,
        attacker_blind=False,
        wallbang=False,
        assister_name=None,
        assister_steam_id=None,
    )

    h1 = HighlightCandidate(
        id="1_kill_STEAM_1_2500",
        highlight_type=HighlightType.KILL,
        round_num=1,
        pov_steam_id="STEAM_1",
        pov_name="Alice",
        kill_start_tick=2500,
        kill_end_tick=2500,
        clip_start_tick=2000,
        clip_end_tick=3000,
        kill_count=1,
        tags=["headshot"],
        is_heuristic=False,
        detection_reason="Single kill",
    )

    parsed = ParsedDemo(
        schema_version=SCHEMA_VERSION,
        demo_path="seeded.dem",
        map_name="de_dust2",
        tickrate=128,
        rounds=[r1],
        players=[p1, p2],
        kills=[k1],
    )

    saved = repo.save_demo(parsed, fingerprint="seeded_fp", highlights=[h1])
    return saved.id


class TestApiEndpoints:
    def test_health_check(self):
        res = health_check()
        assert res["status"] == "ok"
        assert res["schema_version"] == SCHEMA_VERSION

    def test_list_and_get_demo(self, db_session):
        demo_id = seed_demo(db_session)

        # List demos
        demos = list_demos(db=db_session)
        assert len(demos) == 1
        assert demos[0].id == demo_id
        assert demos[0].map_name == "de_dust2"
        assert demos[0].players_count == 2
        assert demos[0].rounds_count == 1
        assert demos[0].highlights_count == 1

        # Get single demo
        d = get_demo(demo_id=demo_id, db=db_session)
        assert d.id == demo_id
        assert d.fingerprint == "seeded_fp"

    def test_get_demo_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc:
            get_demo(demo_id=9999, db=db_session)
        assert exc.value.status_code == 404

    def test_get_highlights_and_filtering(self, db_session):
        demo_id = seed_demo(db_session)

        # All highlights
        all_hl = get_highlights(demo_id=demo_id, db=db_session)
        assert len(all_hl) == 1
        assert all_hl[0].pov_name == "Alice"
        assert all_hl[0].tags == ["headshot"]

        # Filter by POV
        alice_hl = get_highlights(demo_id=demo_id, pov_steam_id="STEAM_1", db=db_session)
        assert len(alice_hl) == 1

        bob_hl = get_highlights(demo_id=demo_id, pov_steam_id="STEAM_2", db=db_session)
        assert len(bob_hl) == 0

        # Filter by type
        kill_hl = get_highlights(demo_id=demo_id, highlight_type="kill", db=db_session)
        assert len(kill_hl) == 1

        ace_hl = get_highlights(demo_id=demo_id, highlight_type="ace", db=db_session)
        assert len(ace_hl) == 0

    def test_get_match_stats(self, db_session):
        demo_id = seed_demo(db_session)

        stats = get_match_stats(demo_id=demo_id, db=db_session)
        assert stats.total_rounds == 1
        assert stats.score == {"ct": 1}
        assert len(stats.players) == 2
        assert stats.players[0].name == "Alice"
        assert stats.players[0].kills == 1
        assert stats.players[0].headshot_pct == 100.0

    def test_get_players_and_rounds(self, db_session):
        demo_id = seed_demo(db_session)

        players = get_players(demo_id=demo_id, db=db_session)
        assert len(players) == 2
        assert {p.name for p in players} == {"Alice", "Bob"}

        rounds = get_rounds(demo_id=demo_id, db=db_session)
        assert len(rounds) == 1
        assert rounds[0].round_num == 1
        assert rounds[0].winner == "ct"

        kills = get_kills(demo_id=demo_id, db=db_session)
        assert len(kills) == 1
        assert kills[0].attacker_name == "Alice"
        assert kills[0].victim_name == "Bob"

    def test_get_player_analytics_success(self, db_session):
        demo_id = seed_demo(db_session)
        analytics = get_player_analytics(demo_id=demo_id, player_identifier="STEAM_1", db=db_session)
        assert analytics.name == "Alice"
        assert analytics.steam_id == "STEAM_1"
        assert analytics.kills == 1
        assert analytics.deaths == 0
        assert analytics.performance_rating >= 0.40
        assert isinstance(analytics.strengths, list)
        assert isinstance(analytics.advice, list)

    def test_get_player_analytics_not_found(self, db_session):
        demo_id = seed_demo(db_session)
        with pytest.raises(HTTPException) as exc:
            get_player_analytics(demo_id=demo_id, player_identifier="UNKNOWN_PLAYER", db=db_session)
        assert exc.value.status_code == 404


    @pytest.mark.asyncio
    async def test_create_render_jobs(self, db_session):
        demo_id = seed_demo(db_session)

        req = RenderJobCreateRequest(
            demo_id=demo_id,
            highlight_ids=["1_kill_STEAM_1_2500"],
            resolution="1080p",
            fps=60,
        )

        jobs = await create_render_jobs(req, db=db_session)
        assert len(jobs) == 1
        assert jobs[0].demo_id == demo_id
        assert jobs[0].highlight_id == "1_kill_STEAM_1_2500"
        assert jobs[0].status == "pending"
        assert jobs[0].progress == 0.0

        # Retrieve by ID
        fetched = get_render_job(jobs[0].id, db=db_session)
        assert fetched.id == jobs[0].id
        assert fetched.status == "pending"

        # List jobs
        job_list = list_render_jobs(demo_id=demo_id, db=db_session)
        assert len(job_list) == 1
        assert job_list[0].id == jobs[0].id

    @pytest.mark.asyncio
    async def test_create_render_jobs_custom_settings(self, db_session):
        import json
        demo_id = seed_demo(db_session)

        req = RenderJobCreateRequest(
            demo_id=demo_id,
            highlight_ids=["1_kill_STEAM_1_2500"],
            resolution="720p",
            fps=30,
            perspective="victim",
            xray=False,
            hud_mode="killfeed_only",
        )

        jobs = await create_render_jobs(req, db=db_session)
        assert len(jobs) == 1
        assert jobs[0].settings_json is not None
        settings = json.loads(jobs[0].settings_json)
        assert settings["perspective"] == "victim"
        assert settings["xray"] is False
        assert settings["hud_mode"] == "killfeed_only"
        assert settings["resolution"] == "720p"

    def test_get_render_job_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc:
            get_render_job("nonexistent_job_id", db=db_session)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_render_jobs_invalid_highlight(self, db_session):
        demo_id = seed_demo(db_session)
        req = RenderJobCreateRequest(
            demo_id=demo_id,
            highlight_ids=["nonexistent_hl_id"],
        )
        with pytest.raises(HTTPException) as exc:
            await create_render_jobs(req, db=db_session)
        assert exc.value.status_code == 400

    def test_parse_demo_invalid_path(self, db_session):
        req = ParseDemoRequest(demo_path="nonexistent_file.dem")
        with pytest.raises(HTTPException) as exc:
            parse_demo_endpoint(req, db=db_session)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_double_click_duplicate_prevention(self, db_session):
        """Second submission while first is still pending must return existing active job instead of duplicate."""
        demo_id = seed_demo(db_session)
        req = RenderJobCreateRequest(
            demo_id=demo_id,
            highlight_ids=["1_kill_STEAM_1_2500"],
        )

        jobs1 = await create_render_jobs(req, db=db_session)
        assert len(jobs1) == 1
        job_id_1 = jobs1[0].id

        # Immediate second click
        jobs2 = await create_render_jobs(req, db=db_session)
        assert len(jobs2) == 1
        assert jobs2[0].id == job_id_1, "Expected second call to return identical active job ID"

        # Verify only 1 job in database
        repo = DemoRepository(db_session)
        all_jobs = repo.list_render_jobs(demo_id=demo_id)
        assert len(all_jobs) == 1

    @pytest.mark.asyncio
    async def test_deduplicate_highlight_ids_in_single_request(self, db_session):
        """Passing duplicate IDs in highlight_ids array must deduplicate cleanly."""
        demo_id = seed_demo(db_session)
        req = RenderJobCreateRequest(
            demo_id=demo_id,
            highlight_ids=["1_kill_STEAM_1_2500", "1_kill_STEAM_1_2500"],
        )

        jobs = await create_render_jobs(req, db=db_session)
        assert len(jobs) == 1

    @pytest.mark.asyncio
    async def test_retry_render_job_endpoint(self, db_session):
        """Failed job can be retried via POST /api/render-jobs/{job_id}/retry."""
        demo_id = seed_demo(db_session)
        repo = DemoRepository(db_session)
        job = repo.create_render_job(
            job_id="test_retry_api_1",
            demo_id=demo_id,
            highlight_id="1_kill_STEAM_1_2500",
            settings_dict={"resolution": "1080p"},
        )
        repo.update_render_job(job.id, status="failed", error_summary="Engine crash")

        # Retry endpoint
        retried = await retry_render_job_endpoint(job.id, db=db_session)
        assert retried.id == job.id
        assert retried.status == "pending"
        assert retried.progress == 0.0
        assert retried.error_summary is None

    @pytest.mark.asyncio
    async def test_retry_non_failed_job_rejected(self, db_session):
        """Retrying a job that is already pending or running raises HTTP 400."""
        demo_id = seed_demo(db_session)
        repo = DemoRepository(db_session)
        job = repo.create_render_job(
            job_id="test_pending_job",
            demo_id=demo_id,
            highlight_id="1_kill_STEAM_1_2500",
            settings_dict={},
        )

        with pytest.raises(HTTPException) as exc:
            await retry_render_job_endpoint(job.id, db=db_session)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_retry_failed_jobs_endpoint(self, db_session):
        """POST /api/render-jobs/retry-failed retries all failed jobs for a demo."""
        demo_id = seed_demo(db_session)
        repo = DemoRepository(db_session)
        j1 = repo.create_render_job("fail_1", demo_id, "1_kill_STEAM_1_2500", {})
        j2 = repo.create_render_job("fail_2", demo_id, "1_kill_STEAM_1_2500", {})
        repo.update_render_job("fail_1", status="failed", error_summary="err1")
        repo.update_render_job("fail_2", status="failed", error_summary="err2")

        retried_list = await retry_failed_jobs_endpoint(demo_id=demo_id, db=db_session)
        assert len(retried_list) == 2
        assert {j.id for j in retried_list} == {"fail_1", "fail_2"}
        assert all(j.status == "pending" for j in retried_list)

    def test_get_job_video_missing_job_returns_404(self, db_session):
        with pytest.raises(HTTPException) as exc:
            get_job_video("nonexistent_job", db=db_session)
        assert exc.value.status_code == 404

    def test_get_job_video_missing_file_returns_404(self, db_session):
        demo_id = seed_demo(db_session)
        repo = DemoRepository(db_session)
        job = repo.create_render_job("missing_vid_job", demo_id, "1_kill_STEAM_1_2500", {})
        repo.update_render_job(job.id, status="completed", output_path="renders/nonexistent.mp4")

        with pytest.raises(HTTPException) as exc:
            get_job_video(job.id, db=db_session)
        assert exc.value.status_code == 404

    def test_get_render_by_filename_path_traversal_rejected(self):
        with pytest.raises(HTTPException) as exc:
            get_render_by_filename("../../../secret.mp4")
        assert exc.value.status_code == 400

    def test_get_render_by_filename_missing_file_returns_404(self):
        with pytest.raises(HTTPException) as exc:
            get_render_by_filename("nonexistent_clip.mp4")
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_montage_no_jobs_found(self, db_session):
        demo_id = seed_demo(db_session)
        req = MontageCreateRequest(demo_id=demo_id)
        with pytest.raises(HTTPException) as exc:
            await create_montage_endpoint(req, db=db_session)
        assert exc.value.status_code == 400
        assert "No completed clip video files found" in exc.value.detail

    def test_get_montage_video_path_traversal_rejected(self):
        with pytest.raises(HTTPException) as exc:
            get_montage_video("../../../etc/passwd.mp4")
        assert exc.value.status_code == 400

    def test_get_montage_video_missing_returns_404(self):
        with pytest.raises(HTTPException) as exc:
            get_montage_video("nonexistent_montage.mp4")
        assert exc.value.status_code == 404

    def test_parse_demo_with_filename_fallback(self, db_session, monkeypatch):
        # Bare filename should resolve from fixtures
        req = ParseDemoRequest(demo_path="test.dem")
        # In this unit test environment, test.dem might be parsed or cached
        from pathlib import Path
        fixture_path = Path("tests/integration/fixtures/test.dem")
        if fixture_path.exists():
            summary = parse_demo_endpoint(req, db=db_session)
            assert summary.file_path.endswith("test.dem")
            assert summary.id > 0


