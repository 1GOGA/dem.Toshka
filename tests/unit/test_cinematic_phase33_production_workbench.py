"""
Unit tests for dem.Toshka Cinematic Studio Phase 3.3.

Covers:
- Phase A & D: Real Sonniss GDC 2026 Sound Library extraction, indexing and audition
- Phase B: Strict Event-First Production Architecture & Timeline Lock State Machine
- Phase C: CS2 HUD & Capture Profiles with convar reality check
- Phase E: AI Scene Director & 9 narrative storyboard scene cards
- Phase F: Dynamic Editing & Fusion Transitions Catalog
- Phase G: Production Workbench API endpoints
"""

import json
import os
import pathlib
import pytest

from backend.cinematic.production_models import (
    EventTimelineMapping,
    HudCaptureProfile,
    HudElementToggles,
    SceneCategory,
    StoryboardSceneCard,
    TimelineLockState,
    TransitionDefinition,
    TransitionFamily,
    TRANSITION_REGISTRY,
)
from backend.cinematic.overlay_generator import (
    check_timeline_lock_status,
    generate_event_mapped_killfeed,
)
from backend.cinematic.scene_analyzer import CinematicSceneAnalyzer
from backend.cinematic.sound_library_manager import SoundLibraryManager


class TestSoundLibraryManager:
    """Validates real Sonniss sound library acquisition, catalog and audio auditioning."""

    def test_catalog_exists_and_verified(self):
        catalog_path = pathlib.Path("assets/sound_library/sound_library_catalog.json")
        assert catalog_path.exists(), "sound_library_catalog.json must exist on disk"

        data = json.loads(catalog_path.read_text(encoding="utf-8"))
        assert data["total_assets"] >= 100, f"Expected at least 100 sound assets, found {data['total_assets']}"
        assert "Sonniss" in data["library_name"]
        assert "Royalty-Free" in data["license_type"]

    def test_manager_lists_and_filters_categories(self):
        mgr = SoundLibraryManager()
        overview = mgr.get_overview()
        assert overview["is_loaded"] is True
        assert overview["total_assets"] >= 100

        categories = mgr.list_categories()
        expected_cats = [
            "impacts", "cinematic_hits", "whooshes", "whip_transitions",
            "risers", "reverse_fx", "glitch", "atmosphere", "gameplay_accents", "ui"
        ]
        for cat in expected_cats:
            assert cat in categories, f"Missing expected sound category: {cat}"

        # Test filtering
        impacts = mgr.list_assets(category="impacts")
        assert len(impacts) > 0
        for asset in impacts:
            assert asset.category == "impacts"
            assert asset.duration_seconds > 0.0
            assert asset.sample_rate in [44100, 48000, 96000, 192000]

    def test_manager_audition_path_resolution(self):
        mgr = SoundLibraryManager()
        impacts = mgr.list_assets(category="impacts")
        assert len(impacts) > 0
        first = impacts[0]
        resolved = mgr.get_audio_file_path(first.category, first.filename)
        assert resolved is not None
        assert os.path.exists(resolved)
        assert resolved.endswith(".wav")


class TestTimelineLockStateMachine:
    """Validates Phase B: strict production ordering and event-to-timeline frame lock."""

    def test_timeline_lock_blocks_premature_killfeed(self):
        # When timeline is PENDING_TIMELINE_LOCK, generation must be BLOCKED
        can_generate, msg = check_timeline_lock_status(TimelineLockState.PENDING_TIMELINE_LOCK)
        assert can_generate is False
        assert "BLOCKED" in msg

        # When timeline is INVALIDATED, generation must be BLOCKED
        can_generate_inv, msg_inv = check_timeline_lock_status(TimelineLockState.INVALIDATED)
        assert can_generate_inv is False
        assert "INVALIDATED" in msg_inv

        # When timeline is LOCKED, generation is PERMITTED
        can_generate_locked, msg_locked = check_timeline_lock_status(TimelineLockState.LOCKED)
        assert can_generate_locked is True
        assert "Timeline locked" in msg_locked

    def test_generate_event_mapped_killfeed_with_lock(self, tmp_path):
        analyzer = CinematicSceneAnalyzer()
        report = analyzer.analyze_anubis_ace_production()
        mappings = report.event_mappings

        # Generation fails when unlocked
        res_fail = generate_event_mapped_killfeed(
            mappings, TimelineLockState.PENDING_TIMELINE_LOCK, tmp_path / "fail"
        )
        assert res_fail["success"] is False
        assert res_fail["status"] == "PENDING_TIMELINE_LOCK"

        # Generation succeeds when locked
        res_succ = generate_event_mapped_killfeed(
            mappings, TimelineLockState.LOCKED, tmp_path / "succ"
        )
        assert res_succ["success"] is True
        assert res_succ["status"] == "GENERATED"
        assert len(res_succ["generated_badges"]) == len(mappings)

        # Check that generated badges have accurate frame mappings
        for badge_info in res_succ["generated_badges"]:
            assert badge_info["timeline_frame"] in [470, 627, 732, 780, 932]
            assert os.path.exists(badge_info["badge_path"])


class TestHudAndCaptureProfiles:
    """Validates Phase C: capture profiles and CS2 Source 2 convar generation."""

    def test_custom_killfeed_profile_convars(self):
        toggles = HudElementToggles(
            native_killfeed=False,
            custom_killfeed=True,
            crosshair=True,
            radar=False,
            player_hud=False,
            weapon_viewmodel=True,
            xray=False,
        )
        convars = toggles.to_convars(HudCaptureProfile.CUSTOM_KILLFEED)
        assert convars["sv_cheats"] == "1"
        assert convars["cl_drawhud"] == "0"
        assert convars["cl_draw_only_deathnotices"] == "0"
        assert convars["crosshair"] == "1"
        assert convars["r_drawviewmodel"] == "1"

    def test_clean_cinematic_profile_convars(self):
        toggles = HudElementToggles()
        convars = toggles.to_convars(HudCaptureProfile.CLEAN_CINEMATIC)
        assert convars["cl_drawhud"] == "0"
        assert convars["crosshair"] == "0"
        assert convars["spec_show_xray"] == "0"

    def test_minimal_hud_profile_convars(self):
        toggles = HudElementToggles(crosshair=True)
        convars = toggles.to_convars(HudCaptureProfile.MINIMAL_HUD)
        assert convars["cl_drawhud"] == "1"
        assert convars["cl_draw_only_deathnotices"] == "1"
        assert convars["crosshair"] == "1"


class TestSceneDirectorStoryboard:
    """Validates Phase E: AI Scene Director recognizing 9 narrative scene types."""

    def test_9_scene_storyboard_manifest(self):
        analyzer = CinematicSceneAnalyzer()
        report = analyzer.analyze_anubis_ace_production()

        storyboard = report.storyboard
        assert len(storyboard) == 9, f"Expected exactly 9 scene cards, got {len(storyboard)}"

        # Validate sequence of categories
        expected_categories = [
            SceneCategory.ESTABLISHING,
            SceneCategory.APPROACH,
            SceneCategory.TENSION,
            SceneCategory.ENGAGEMENT,
            SceneCategory.SPRAY_TRANSFER,
            SceneCategory.MULTIKILL,
            SceneCategory.CLUTCH,
            SceneCategory.ACE_CLIMAX,
            SceneCategory.AFTERMATH,
        ]

        for idx, expected_cat in enumerate(expected_categories):
            scene = storyboard[idx]
            assert scene.category == expected_cat
            assert scene.scene_number == idx + 1
            assert scene.duration_seconds > 0.0
            assert len(scene.suggested_camera_type) > 0
            assert len(scene.suggested_transition) > 0
            assert len(scene.suggested_sound_treatment) > 0


class TestDynamicEditingEngine:
    """Validates Phase F: dynamic transitions library and presets."""

    def test_transitions_registry(self):
        assert len(TRANSITION_REGISTRY) >= 10
        families = {t.family for t in TRANSITION_REGISTRY}
        assert TransitionFamily.CAMERA in families
        assert TransitionFamily.ZOOM in families
        assert TransitionFamily.IMPACT in families
        assert TransitionFamily.MASK in families
        assert TransitionFamily.MOTION in families
        assert TransitionFamily.DIGITAL in families

        for t in TRANSITION_REGISTRY:
            assert t.duration_frames > 0
            assert t.shutter_angle >= 0.0
            assert len(t.description) > 0
            assert len(t.best_used_for) > 0
