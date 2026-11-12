"""Unit tests for Cinematic Scene Analyzer & Dynamics Engine."""

import pytest
from backend.cinematic.scene_analyzer import (
    CinematicSceneAnalyzer,
    CombatTempo,
    DynamicTransitionType,
)


def test_scene_analyzer_anubis_ace():
    analyzer = CinematicSceneAnalyzer(fps=60, tickrate=128)
    report = analyzer.analyze_anubis_ace_production()

    assert report.highlight_id == "anubis_ace_r19"
    assert report.round_number == 19
    assert report.tempo == CombatTempo.RAPID_FIRE
    assert len(report.kill_timings) == 5
    assert len(report.transitions) == 4
    assert len(report.dynamic_effects) >= 5

    # Check Kill 1 engagement vs fatal timing
    k1 = report.kill_timings[0]
    assert k1.kill_num == 1
    assert k1.killer == "pytoshka_"
    assert k1.victim == "Tiger07"
    assert 7.65 <= k1.engagement_time_s <= 7.75
    assert 7.80 <= k1.fatal_time_s <= 7.85
    assert k1.beat_drop_time_s == k1.engagement_time_s
    assert k1.killfeed_frame == 470

    # Check Kill 3 Headshot
    k3 = report.kill_timings[2]
    assert k3.headshot is True
    assert k3.victim == "ProfyfGames"
    assert 12.15 <= k3.fatal_time_s <= 12.25

    # Check HUD suppression policy
    assert report.hud_policy["in_game_hud_suppressed"] is True
    assert "cl_drawhud 0" in report.hud_policy["commands"]
    assert "cl_draw_only_deathnotices 0" in report.hud_policy["commands"]
    assert report.hud_policy["custom_killfeed_enabled"] is True

    # Check Transitions
    trans_types = [t.transition_type for t in report.transitions]
    assert DynamicTransitionType.WHIP_PAN in trans_types
    assert DynamicTransitionType.RADIAL_ZOOM in trans_types
    assert DynamicTransitionType.SNAP_CUT in trans_types
    assert DynamicTransitionType.SMOOTH_GLIDE in trans_types

    # Serialization test
    d = report.to_dict()
    assert d["highlight_id"] == "anubis_ace_r19"
    assert d["tempo"] == "RAPID_FIRE"
    assert len(d["kill_timings"]) == 5
