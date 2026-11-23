"""Unit and integration tests for Demo Vision 2D Radar, telemetry, and replay extraction."""

import pathlib
import pytest
from backend.parser.replay import (
    get_map_calibration,
    normalize_map_name,
    world_to_radar_percent,
    radar_percent_to_world,
    extract_round_replay_data,
    MAP_CALIBRATIONS,
)
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.repository import DemoRepository
from backend.storage.models import DemoModel
from backend.api.main import (
    create_project,
    list_projects,
    get_project,
    delete_project,
    add_drawing,
    list_drawings,
    delete_drawing,
    add_bookmark,
    list_bookmarks,
    delete_bookmark,
)
from backend.api.schemas import (
    CreateAnalysisProjectRequest,
    CreateTacticalDrawingRequest,
    CreateBookmarkRequest,
)

FIXTURE_DEMO = pathlib.Path("tests/integration/fixtures/test.dem")


class TestDemoVisionCalibrations:
    def test_normalize_map_names(self):
        assert normalize_map_name("de_dust2") == "de_dust2"
        assert normalize_map_name("workshop/12345/de_mirage.vpk") == "de_mirage"
        assert normalize_map_name("maps/de_nuke.vpk") == "de_nuke"
        assert normalize_map_name(None) == "de_mirage"

    def test_calibrations_cover_competitive_pool(self):
        pool = ["de_mirage", "de_inferno", "de_dust2", "de_nuke", "de_ancient", "de_anubis", "de_vertigo", "de_train"]
        for map_name in pool:
            cal = get_map_calibration(map_name)
            assert "pos_x" in cal
            assert "pos_y" in cal
            assert "scale" in cal
            assert cal["scale"] > 0

    def test_multi_level_split_z(self):
        nuke_cal = get_map_calibration("de_nuke")
        assert nuke_cal.get("split_z") is not None
        assert "upper" in nuke_cal["levels"]
        assert "lower" in nuke_cal["levels"]

        vertigo_cal = get_map_calibration("de_vertigo")
        assert vertigo_cal.get("split_z") is not None

    def test_world_to_radar_transforms(self):
        # Mirage center coordinates transform within 0..100%
        cal = get_map_calibration("de_mirage")
        center_x = cal["pos_x"] + (cal["scale"] * 512.0)
        center_y = cal["pos_y"] - (cal["scale"] * 512.0)
        pct_x, pct_y = world_to_radar_percent(center_x, center_y, "de_mirage")
        assert 45.0 <= pct_x <= 55.0
        assert 45.0 <= pct_y <= 55.0

        # Back and forth precision
        wx, wy, _ = radar_percent_to_world(pct_x, pct_y, "de_mirage")
        assert abs(wx - center_x) < 20.0
        assert abs(wy - center_y) < 20.0


class TestDemoVisionReplayExtraction:
    @pytest.mark.skipif(not FIXTURE_DEMO.is_file(), reason="Fixture demo test.dem not found")
    def test_extract_round_replay_telemetry(self):
        data = extract_round_replay_data(FIXTURE_DEMO, round_num=1, step_ticks=16)

        assert data["round_num"] == 1
        assert data["map_name"] == "de_nuke"
        assert data["tickrate"] in (64, 128)
        assert len(data["frames"]) > 0
        assert len(data["players"]) == 10

        first_frame = data["frames"][0]
        assert "tick" in first_frame
        assert "players" in first_frame
        assert len(first_frame["players"]) > 0

        p = first_frame["players"][0]
        # Verify mandatory Demo Vision telemetry fields
        assert "steam_id" in p
        assert "side" in p
        assert p["side"] in ("ct", "t")
        assert "health" in p
        assert "x" in p
        assert "y" in p
        assert "level" in p
        assert p["level"] in ("upper", "lower")

        # Verify Phase 1 extended fields
        assert "yaw" in p
        assert isinstance(p["yaw"], float)
        assert "pitch" in p
        assert isinstance(p["pitch"], float)
        assert "armor" in p
        assert isinstance(p["armor"], int)
        assert "has_helmet" in p
        assert isinstance(p["has_helmet"], bool)
        assert "has_defuser" in p
        assert isinstance(p["has_defuser"], bool)
        assert "weapon" in p
        assert isinstance(p["weapon"], str)
        assert "is_flashed" in p
        assert isinstance(p["is_flashed"], bool)

    @pytest.mark.skipif(not FIXTURE_DEMO.is_file(), reason="Fixture demo test.dem not found")
    def test_extract_grenades_and_duration(self):
        data = extract_round_replay_data(FIXTURE_DEMO, round_num=1, step_ticks=16)
        assert "grenades" in data
        grenades = data["grenades"]
        assert len(grenades) > 0

        for g in grenades:
            assert "id" in g
            assert "type" in g
            assert g["type"] in ("smoke", "molotov", "flash", "he", "decoy")
            assert "start_tick" in g
            assert "detonate_tick" in g
            assert "end_tick" in g
            assert g["end_tick"] >= g["detonate_tick"]
            assert g["duration_seconds"] > 0
            assert "trajectory" in g


class TestAnalysisProjectsAndTacticalDrawings:
    @pytest.fixture
    def test_repo(self):
        engine = create_db_engine("sqlite:///:memory:")
        init_db(engine)
        SessionFactory = get_session_factory(engine)
        with SessionFactory() as session:
            # Create a mock demo
            demo = DemoModel(
                file_path="mock/test.dem",
                fingerprint="test_fp_123",
                map_name="de_mirage",
                tickrate=128,
                schema_version="2.0.0",
            )
            session.add(demo)
            session.commit()
            demo_id = demo.id

        session = SessionFactory()
        repo = DemoRepository(session)
        yield repo, demo_id, session
        session.close()

    def test_project_crud(self, test_repo):
        repo, demo_id, _ = test_repo
        proj = repo.create_analysis_project(
            demo_id=demo_id,
            title="Mirage A Execute Breakdown",
            description="Analysis of round 4 smokes and trades",
        )
        assert proj.id is not None
        assert proj.title == "Mirage A Execute Breakdown"
        assert proj.demo_id == demo_id

        # Retrieve
        fetched = repo.get_analysis_project(proj.id)
        assert fetched is not None
        assert fetched.id == proj.id

        # List
        projects = repo.list_analysis_projects(demo_id=demo_id)
        assert len(projects) == 1

        # Delete
        success = repo.delete_analysis_project(proj.id)
        assert success is True
        assert repo.get_analysis_project(proj.id) is None

    def test_tactical_drawing_crud(self, test_repo):
        repo, demo_id, _ = test_repo
        proj = repo.create_analysis_project(demo_id=demo_id, title="Test Project")

        # Add arrow drawing
        geom = '{"x1": 45.2, "y1": 50.1, "x2": 52.3, "y2": 58.4}'
        drawing = repo.add_tactical_drawing(
            project_id=proj.id,
            round_num=4,
            layer_type="arrow",
            color="#00f2fe",
            stroke_width=3.0,
            geometry_json=geom,
            text_label="A Ramp Push",
        )
        assert drawing.id is not None
        assert drawing.layer_type == "arrow"
        assert drawing.round_num == 4

        # List drawings
        drawings = repo.get_tactical_drawings(proj.id, round_num=4)
        assert len(drawings) == 1
        assert drawings[0].text_label == "A Ramp Push"

        # Delete drawing
        deleted = repo.delete_tactical_drawing(drawing.id)
        assert deleted is True
        assert len(repo.get_tactical_drawings(proj.id, round_num=4)) == 0

    def test_bookmarks_crud(self, test_repo):
        repo, demo_id, _ = test_repo
        proj = repo.create_analysis_project(demo_id=demo_id, title="Test Project")

        # Add bookmark
        bm = repo.add_bookmark(
            project_id=proj.id,
            round_num=4,
            tick=12400,
            title="Late rotation from B",
            category="TACTICAL_MISTAKE",
            notes="Anchor rotated too early leaving site open",
            player_steamid="76561198000000001",
        )
        assert bm.id is not None
        assert bm.tick == 12400
        assert bm.category == "TACTICAL_MISTAKE"

        # List bookmarks
        bookmarks = repo.get_bookmarks(proj.id, round_num=4)
        assert len(bookmarks) == 1
        assert bookmarks[0].title == "Late rotation from B"

        # Delete bookmark
        deleted = repo.delete_bookmark(bm.id)
        assert deleted is True
        assert len(repo.get_bookmarks(proj.id, round_num=4)) == 0


class TestAnalysisProjectsAPI:
    @pytest.fixture
    def api_session(self):
        engine = create_db_engine("sqlite:///:memory:")
        init_db(engine)
        SessionFactory = get_session_factory(engine)

        with SessionFactory() as session:
            demo = DemoModel(
                file_path="mock/test_api.dem",
                fingerprint="api_fp_123",
                map_name="de_nuke",
                tickrate=128,
                schema_version="2.0.0",
            )
            session.add(demo)
            session.commit()
            demo_id = demo.id

        session = SessionFactory()
        yield session, demo_id
        session.close()

    def test_api_project_lifecycle(self, api_session):
        session, demo_id = api_session

        # 1. Create project via endpoint
        proj_req = CreateAnalysisProjectRequest(demo_id=demo_id, title="API Test Project")
        proj_dto = create_project(req=proj_req, db=session)
        assert proj_dto.id is not None
        assert proj_dto.title == "API Test Project"
        project_id = proj_dto.id

        # 2. Add drawing via endpoint
        draw_req = CreateTacticalDrawingRequest(
            round_num=1,
            layer_type="pen",
            color="#facc15",
            stroke_width=4.0,
            geometry_json='{"points": [[10, 10], [20, 20]]}',
        )
        draw_dto = add_drawing(project_id=project_id, req=draw_req, db=session)
        assert draw_dto.id is not None
        assert draw_dto.layer_type == "pen"
        drawing_id = draw_dto.id

        # 3. Add bookmark via endpoint
        bm_req = CreateBookmarkRequest(
            round_num=1,
            tick=4500,
            title="First Kill Contact",
            category="GREAT_PLAY",
        )
        bm_dto = add_bookmark(project_id=project_id, req=bm_req, db=session)
        assert bm_dto.id is not None
        assert bm_dto.tick == 4500
        bm_id = bm_dto.id

        # 4. Get project details with drawings and bookmarks
        detail = get_project(project_id=project_id, db=session)
        assert len(detail.drawings) == 1
        assert len(detail.bookmarks) == 1

        # 5. List endpoints
        projects_list = list_projects(demo_id=demo_id, db=session)
        assert len(projects_list) == 1

        drawings_list = list_drawings(project_id=project_id, round_num=1, db=session)
        assert len(drawings_list) == 1

        bookmarks_list = list_bookmarks(project_id=project_id, round_num=1, db=session)
        assert len(bookmarks_list) == 1

        # 6. Delete drawing & bookmark
        del_draw = delete_drawing(project_id=project_id, drawing_id=drawing_id, db=session)
        assert del_draw["status"] == "deleted"

        del_bm = delete_bookmark(project_id=project_id, bookmark_id=bm_id, db=session)
        assert del_bm["status"] == "deleted"

        # 7. Delete project
        del_proj = delete_project(project_id=project_id, db=session)
        assert del_proj["status"] == "deleted"

