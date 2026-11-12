"""
Unit tests for Phase 3.5: AI VFX Intelligence & Decision Engine.
Verifies catalog completeness, Fusion preset integrity, decision engine logic,
validation test renders, and API endpoints.
"""

import json
import pathlib
import pytest

from backend.api.main import (
    get_vfx_catalog,
    decide_vfx,
    compare_vfx_tiers,
    list_vfx_presets,
    get_vfx_validation_tests,
    submit_vfx_feedback,
    get_vfx_plugin_research,
)
from backend.cinematic.vfx_decision_engine import (
    VfxDecisionEngine,
    VfxSceneContext,
    VfxDecision,
)


@pytest.fixture
def vfx_engine():
    return VfxDecisionEngine()


class DummyRequest:
    def __init__(self, data):
        self._data = data

    async def json(self):
        return self._data


def test_vfx_catalog_completeness(vfx_engine):
    """Catalog must contain all 7 categories and at least 21 actionable recipes."""
    catalog = vfx_engine.catalog
    assert len(catalog) >= 21

    expected_categories = {
        "TIME_MANIPULATION",
        "SUBJECT_HIGHLIGHT",
        "WEAPON_AND_HANDS",
        "ENVIRONMENT",
        "COMPOSITING",
        "CAMERA_AND_MOTION",
        "COLOR",
    }
    catalog_categories = {item["category"] for item in catalog.values()}
    assert expected_categories.issubset(catalog_categories)

    for item in catalog.values():
        assert "effect_id" in item
        assert "name" in item
        assert "fusion_node_structure" in item
        assert "resolve_implementation_instructions" in item
        assert "confidence" in item
        assert item["confidence"] in ("OBSERVED", "INFERRED", "VERIFIED")


def test_fusion_presets_integrity():
    """All 11 production Fusion .setting presets must exist and have valid structure."""
    preset_dir = pathlib.Path("assets/fusion_presets")
    assert preset_dir.is_dir()

    expected_presets = [
        "Player_Outline_Subtle.setting",
        "Player_Outline_Cyan.setting",
        "Player_Outline_Gold.setting",
        "Weapon_RimLight.setting",
        "Hands_AccentGlow.setting",
        "Sky_Cinematic_Grade.setting",
        "Headshot_Impact.setting",
        "ACE_Climax.setting",
        "Motion_WhipPan.setting",
        "Radial_Zoom_Impact.setting",
        "SpeedRamp_Accent.setting",
    ]

    for p_name in expected_presets:
        preset_file = preset_dir / p_name
        assert preset_file.is_file(), f"Missing preset: {p_name}"
        assert preset_file.stat().st_size > 100
        content = preset_file.read_text(encoding="utf-8")
        assert "GroupOperator" in content or "MacroOperator" in content
        assert "Tools" in content


def test_plugin_research_document():
    """Plugin Lab research document must exist and detail plugins and hardware limits."""
    res_file = pathlib.Path("reference_library/effect_intelligence/PLUGIN_RESEARCH.md")
    assert res_file.is_file()
    content = res_file.read_text(encoding="utf-8")
    assert "Reactor 3" in content
    assert "Glow Expo" in content
    assert "Boris FX Sapphire" in content
    assert "Maxon Universe" in content
    assert "AMD Radeon RX 5700 XT" in content
    assert "DaVinci Resolve Free 21.0" in content


def test_decision_engine_headshot_slowmo(vfx_engine):
    """Lethal headshot should trigger optical flow slow motion deceleration."""
    ctx = VfxSceneContext(
        scene_id="headshot_scene",
        scene_category="ENGAGEMENT",
        camera_type="FIRST_PERSON",
        fps=60.0,
        time_seconds=10.08,
        duration_seconds=1.5,
        is_kill_event=True,
        is_headshot=True,
    )
    decision = vfx_engine.decide_vfx(ctx, "SUBTLE")
    selected_ids = [e.effect_id for e in decision.selected_effects]
    assert "EFF_TIME_OPTICAL_FLOW_SLOWMO" in selected_ids
    assert decision.treatment_tier == "SUBTLE"
    assert decision.fairlight_audio_ducking_db < 0.0


def test_decision_engine_rapid_multikill_rejects_slowmo(vfx_engine):
    """Rapid multikill (<0.85s) must reject slow motion with clear 'less is better' rationale."""
    ctx = VfxSceneContext(
        scene_id="rapid_kill_scene",
        scene_category="MULTIKILL",
        camera_type="FIRST_PERSON",
        fps=60.0,
        time_seconds=10.89,
        duration_seconds=0.81,
        is_kill_event=True,
        is_headshot=False,
        rapid_kill_interval=0.81,  # < 0.85s
    )
    decision = vfx_engine.decide_vfx(ctx, "SUBTLE")
    selected_ids = [e.effect_id for e in decision.selected_effects]
    assert "EFF_TIME_OPTICAL_FLOW_SLOWMO" not in selected_ids

    rejected_reasons = {r.effect_id: r.rejection_reason for r in decision.rejected_effects}
    assert "EFF_TIME_OPTICAL_FLOW_SLOWMO" in rejected_reasons
    assert "Rapid multikill interval" in rejected_reasons["EFF_TIME_OPTICAL_FLOW_SLOWMO"]


def test_decision_engine_ace_climax_gold_outline(vfx_engine):
    """Ace climax orbit camera triggers player outline gold climax effect."""
    ctx = VfxSceneContext(
        scene_id="ace_orbit_climax",
        scene_category="ACE_CLIMAX",
        camera_type="ORBIT_CAMERA",
        fps=60.0,
        time_seconds=15.46,
        duration_seconds=3.0,
        is_kill_event=True,
        is_ace_kill=True,
        is_outdoor_sky_visible=True,
    )
    decision = vfx_engine.decide_vfx(ctx, "SUBTLE")
    selected_ids = [e.effect_id for e in decision.selected_effects]
    assert "EFF_SUBJ_OUTLINE_GOLD_CLIMAX" in selected_ids
    assert "EFF_ENV_SKY_CINEMATIC_GRADE" in selected_ids


def test_decision_engine_clean_tier_pass_through(vfx_engine):
    """Clean tier must strictly apply 0 effects and pass-through macro."""
    ctx = VfxSceneContext(
        scene_id="clean_test_scene",
        scene_category="ACE_CLIMAX",
        camera_type="ORBIT_CAMERA",
        fps=60.0,
        time_seconds=15.46,
        duration_seconds=3.0,
        is_kill_event=True,
        is_ace_kill=True,
    )
    decision = vfx_engine.decide_vfx(ctx, "CLEAN")
    assert decision.treatment_tier == "CLEAN"
    assert len(decision.selected_effects) == 0
    assert "Pass-through" in decision.fusion_macro_recipe


def test_decision_engine_three_tier_comparison(vfx_engine):
    """Comparison generator must yield clean, subtle, and strong proposals."""
    ctx = VfxSceneContext(
        scene_id="compare_scene",
        scene_category="ACE_CLIMAX",
        camera_type="ORBIT_CAMERA",
        fps=60.0,
        time_seconds=15.46,
        duration_seconds=3.0,
        is_kill_event=True,
        is_ace_kill=True,
        is_outdoor_sky_visible=True,
    )
    tiers = vfx_engine.compare_scene_tiers(ctx)
    assert "clean" in tiers
    assert "subtle" in tiers
    assert "strong" in tiers

    assert len(tiers["clean"].selected_effects) == 0
    assert len(tiers["subtle"].selected_effects) > 0
    assert len(tiers["strong"].selected_effects) >= len(tiers["subtle"].selected_effects)


def test_real_validation_renders_exist():
    """All 6 real validation tests and their PNG thumbnails must exist on disk."""
    out_dir = pathlib.Path("renders/vfx_validation_tests")
    assert out_dir.is_dir()

    expected_files = [
        "test_01_slowmo_matrix.mp4",
        "test_01_slowmo_matrix.png",
        "test_02_player_outline_climax.mp4",
        "test_02_player_outline_climax.png",
        "test_03_weapon_hands_accent.mp4",
        "test_03_weapon_hands_accent.png",
        "test_04_sky_sandstone_grade.mp4",
        "test_04_sky_sandstone_grade.png",
        "test_05_whip_pan_transition.mp4",
        "test_05_whip_pan_transition.png",
        "test_06_three_tier_comparison.mp4",
        "test_06_three_tier_comparison.png",
    ]

    for f_name in expected_files:
        f_path = out_dir / f_name
        assert f_path.is_file(), f"Missing validation test file: {f_name}"
        assert f_path.stat().st_size > 0


@pytest.mark.asyncio
async def test_vfx_api_endpoints():
    """Test all FastAPI VFX intelligence endpoints directly."""
    # 1. Catalog
    catalog_data = get_vfx_catalog()
    assert catalog_data["count"] >= 21

    # 2. Decide
    decide_req = DummyRequest({
        "scene_id": "test_shot_01",
        "scene_category": "ENGAGEMENT",
        "camera_type": "FIRST_PERSON",
        "fps": 60.0,
        "time_seconds": 10.0,
        "duration_seconds": 2.0,
        "is_kill_event": True,
        "is_headshot": True,
        "requested_tier": "SUBTLE",
    })
    decision = await decide_vfx(decide_req)
    assert decision["treatment_tier"] == "SUBTLE"
    assert len(decision["selected_effects"]) > 0

    # 3. Compare
    compare_req = DummyRequest({
        "scene_id": "test_shot_02",
        "scene_category": "ACE_CLIMAX",
        "camera_type": "ORBIT_CAMERA",
        "fps": 60.0,
        "time_seconds": 15.0,
        "duration_seconds": 3.0,
        "is_kill_event": True,
        "is_ace_kill": True,
    })
    compare_data = await compare_vfx_tiers(compare_req)
    assert "clean" in compare_data
    assert "subtle" in compare_data
    assert "strong" in compare_data

    # 4. Presets
    presets_data = list_vfx_presets()
    assert presets_data["count"] == 11

    # 5. Tests
    tests_data = get_vfx_validation_tests()
    assert tests_data["count"] == 6

    # 6. Feedback
    fb_req = DummyRequest({
        "effect_id": "EFF_TIME_OPTICAL_FLOW_SLOWMO",
        "vote": "like",
        "note": "Loved the deceleration on kill 3",
    })
    fb_res = await submit_vfx_feedback(fb_req)
    assert fb_res["status"] == "success"

    # 7. Plugin research
    res_data = get_vfx_plugin_research()
    assert "Reactor 3" in res_data["content"]
