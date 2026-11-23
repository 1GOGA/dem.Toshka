"""
tests/unit/test_multi_match_analytics.py — Tests for Phase 4 Multi-Match Analytics & Evidence Insights.
"""

from __future__ import annotations

import datetime
import os
import pytest
from backend.analytics.multi_match import (
    calculate_competency_radar,
    build_player_analytics_summary,
    generate_and_persist_insights,
)
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.models import DemoModel, PlayerMatchStatsModel, PlayerModel, PlayerProfileModel
from backend.storage.repository import DemoRepository
from backend.api.main import list_player_profiles, get_player_multi_match_analytics


def test_competency_radar_calculation():
    """Verify 6-pillar radar score calculations."""
    # Match with high headshots and opening duels
    m1 = PlayerMatchStatsModel(
        player_profile_id="p1",
        demo_id=1,
        map_name="de_mirage",
        team_side="both",
        kills=25,
        deaths=12,
        assists=4,
        headshots=16,
        headshot_pct=64.0,
        adr=105.0,
        rating=1.45,
        kast_pct=78.0,
        crosshair_placement_error=4.2,
        time_to_damage_ms=210.0,
        untradeable_deaths=2,
        trade_kill_conversion_pct=48.0,
        team_flash_ratio=0.10,
        opening_duel_win_pct=70.0,
        clutch_win_pct=50.0,
        rounds_played=24,
    )
    radar = calculate_competency_radar([m1])
    assert radar.aim_duels >= 80.0
    assert radar.positioning >= 70.0
    assert radar.decision_making >= 70.0
    assert radar.trading >= 70.0
    assert radar.clutch >= 70.0


def test_multi_match_aggregation_and_maps():
    """Verify multi-match summary aggregations and per-map breakdown."""
    profile = PlayerProfileModel(
        id="prof_123",
        steam_id="76561198000000001",
        nickname="ZywOo",
        primary_role="AWPer",
    )
    m1 = PlayerMatchStatsModel(
        player_profile_id=profile.id,
        demo_id=1,
        map_name="de_dust2",
        kills=20,
        deaths=10,
        assists=3,
        headshots=8,
        headshot_pct=40.0,
        adr=85.0,
        rating=1.30,
        kast_pct=75.0,
        untradeable_deaths=2,
        trade_kill_conversion_pct=40.0,
        team_flash_ratio=0.12,
        opening_duel_win_pct=60.0,
        clutch_win_pct=33.3,
        rounds_played=20,
    )
    m2 = PlayerMatchStatsModel(
        player_profile_id=profile.id,
        demo_id=2,
        map_name="de_inferno",
        kills=15,
        deaths=15,
        assists=5,
        headshots=6,
        headshot_pct=40.0,
        adr=72.0,
        rating=1.05,
        kast_pct=68.0,
        untradeable_deaths=5,
        trade_kill_conversion_pct=30.0,
        team_flash_ratio=0.15,
        opening_duel_win_pct=45.0,
        clutch_win_pct=25.0,
        rounds_played=22,
    )

    summary = build_player_analytics_summary(profile, [m1, m2])
    assert summary["matches_count"] == 2
    assert summary["total_rounds"] == 42
    assert summary["overview"]["kills"] == 35
    assert summary["overview"]["deaths"] == 25
    assert summary["overview"]["kd_ratio"] == 1.40
    assert len(summary["maps"]) == 2


def test_evidence_based_insights_contract():
    """Verify generation of 7-component evidence recommendations with Demo Vision anchors."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()
    repo = DemoRepository(session)

    try:
        # Seed demo
        demo = DemoModel(
            file_path="C:/dummy/test.dem",
            fingerprint="dummy_fp_1",
            map_name="de_anubis",
            schema_version="2.0.0",
        )
        session.add(demo)
        session.flush()

        profile = repo.get_or_create_player_profile(
            steam_id="76561198000000002",
            nickname="TestPlayer",
        )
        # Create match with high untradeable death rate (5 untradeables out of 10 deaths = 50%)
        m = repo.record_player_match_stats(
            player_profile_id=profile.id,
            demo_id=demo.id,
            stats={
                "map_name": "de_anubis",
                "team_side": "ct",
                "kills": 12,
                "deaths": 10,
                "assists": 2,
                "headshots": 5,
                "headshot_pct": 41.7,
                "adr": 68.0,
                "rating": 0.95,
                "kast_pct": 62.0,
                "untradeable_deaths": 5,
                "trade_kill_conversion_pct": 20.0,
                "team_flash_ratio": 0.20,
                "opening_duel_win_pct": 55.0,
                "clutch_win_pct": 25.0,
                "rounds_played": 18,
            },
        )

        insights = generate_and_persist_insights(profile, [m], repo)
        assert len(insights) >= 2

        # Check 7-component evidence schema for Positioning insight
        pos_insight = next(i for i in insights if i.category == "POSITIONING")
        assert pos_insight.severity == "CRITICAL"
        assert len(pos_insight.pattern_description) > 10
        assert "Выборка:" in pos_insight.sample_size_str
        assert "смертей" in pos_insight.objective_metric_str
        assert len(pos_insight.context_conditions_str) > 5
        assert len(pos_insight.alternative_strategy_str) > 10
        assert len(pos_insight.impact_estimate_str) > 10
        # Check Demo Vision anchor coordinates
        assert pos_insight.jump_demo_id == demo.id
        assert pos_insight.jump_round_num is not None
        assert pos_insight.jump_tick is not None
    finally:
        session.close()


def test_multi_match_api_endpoints():
    """Verify FastAPI list_player_profiles and get_player_multi_match_analytics endpoints."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()
    repo = DemoRepository(session)

    try:
        demo = DemoModel(
            file_path="C:/dummy/test2.dem",
            fingerprint="dummy_fp_2",
            map_name="de_dust2",
            schema_version="2.0.0",
        )
        session.add(demo)
        session.flush()

        p = repo.get_or_create_player_profile(
            steam_id="76561198000000003",
            nickname="s1mple",
            primary_role="Sniper",
        )
        repo.record_player_match_stats(
            player_profile_id=p.id,
            demo_id=demo.id,
            stats={"kills": 30, "deaths": 10, "rating": 1.75, "rounds_played": 22},
        )

        # 1. List profiles
        profiles = list_player_profiles(db=session)
        assert len(profiles) >= 1
        assert any(prof.nickname == "s1mple" for prof in profiles)

        # 2. Get analytics
        analytics = get_player_multi_match_analytics(steam_id_or_id="76561198000000003", db=session)
        assert analytics.steam_id == "76561198000000003"
        assert analytics.nickname == "s1mple"
        assert analytics.matches_count == 1
        assert analytics.radar.aim_duels > 0
        assert len(analytics.insights) > 0
    finally:
        session.close()
