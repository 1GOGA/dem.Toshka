"""Unit tests for Cinematic Studio API endpoint functions."""

import pytest

from backend.api.main import (
    create_production_package,
    get_cinematic_highlights,
    get_package_fcpxml,
    get_package_manifests,
    plan_cinematic_shots,
)
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.models import DemoModel, HighlightModel, KillEventModel


@pytest.fixture
def db_session():
    """In-memory SQLite session for testing API endpoints."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    with session_factory() as sess:
        yield sess


def test_cinematic_api_endpoints_direct(db_session):
    # Seed in-memory database with test demo and highlights
    demo = DemoModel(
        id=1,
        file_path="demos/test.dem",
        fingerprint="fp123",
        map_name="de_inferno",
        duration_seconds=120.0,
        tickrate=128,
        schema_version="2.0.0",
    )
    db_session.add(demo)

    hl1 = HighlightModel(
        id="hl_test_01",
        demo_id=1,
        highlight_type="ACE",
        round_num=2,
        clip_start_tick=1000,
        clip_end_tick=1400,
        kill_start_tick=1050,
        kill_end_tick=1350,
        kill_count=5,
        pov_steam_id="76561198000000001",
        pov_name="AceKing",
    )
    db_session.add(hl1)

    for i in range(5):
        k = KillEventModel(
            demo_id=1,
            round_num=2,
            tick=1050 + i * 50,
            attacker_steam_id="76561198000000001",
            attacker_name="AceKing",
            victim_steam_id=f"7656119800000000{i+2}",
            victim_name=f"Bot_{i+1}",
            weapon="ak47",
            headshot=(i % 2 == 0),
            wallbang=(i == 1),
        )
        db_session.add(k)
    db_session.commit()

    # 1. Test get_cinematic_highlights
    highlights = get_cinematic_highlights(demo_id=1, session=db_session)
    assert len(highlights) == 1
    assert highlights[0]["id"] == "hl_test_01"
    assert highlights[0]["score"] > 100.0
    assert highlights[0]["kills_count"] == 5
    assert highlights[0]["has_headshot"] is True
    assert highlights[0]["has_wallbang"] is True

    # 2. Test plan_cinematic_shots
    plan_data = plan_cinematic_shots(
        payload={"demo_id": 1, "highlight_ids": ["hl_test_01"], "fps": 60},
        session=db_session,
    )
    assert "shots" in plan_data
    shots = plan_data["shots"]
    assert len(shots) >= 2
    cam_types = [s["camera_type"] for s in shots]
    assert "FIRST_PERSON" in cam_types
    assert "VICTIM_POV" in cam_types

    # 3. Test create_production_package
    pkg_summary = create_production_package(
        payload={"demo_id": 1, "shots": shots, "project_name": "Test Ace Movie"},
        session=db_session,
    )
    assert "package_id" in pkg_summary
    assert pkg_summary["project_name"] == "Test Ace Movie"
    assert "fcpxml_path" in pkg_summary
    assert "manifests" in pkg_summary
    assert len(pkg_summary["manifests"]) == 7

    package_id = pkg_summary["package_id"]

    # 4. Test get_package_manifests
    manifests = get_package_manifests(package_id=package_id)
    assert "highlight_manifest" in manifests
    assert "shot_plan" in manifests
    assert "camera_paths" in manifests
    assert "render_manifest" in manifests

    # 5. Test get_package_fcpxml
    fcpxml_resp = get_package_fcpxml(package_id=package_id)
    assert fcpxml_resp.media_type == "application/xml"
