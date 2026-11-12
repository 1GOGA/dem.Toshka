"""Unit tests for Phase 3 Cinematic Studio AI Production Pipeline."""

import pathlib
import pytest
from unittest.mock import MagicMock, patch

from backend.cinematic.camera_library import generate_shoulder_cam_path
from backend.cinematic.models import (
    CameraType,
    CinematicProductionPackage,
    CinematicShot,
    OverlayKillEvent,
    ShotPurpose,
    Vector3,
)
from backend.cinematic.music_sync import MusicBeatGrid, align_shots_to_beats, generate_placeholder_music_track
from backend.cinematic.overlay_generator import (
    generate_multikill_badge,
    generate_svg_killfeed_badge,
    render_killfeed_png_badge,
)
from backend.cinematic.production_coordinator import AutomatedQCVerifier, JobState, ProductionCoordinator
from backend.cinematic.resolve_export import generate_davinci_resolve_python_script
from backend.cinematic.shot_director import CameraQualityScorer, CinematicDirectorV2


class TestCameraQualityScorer:
    def test_first_person_quality_score(self):
        scorer = CameraQualityScorer()
        shot = CinematicShot(
            shot_id="shot_hero",
            highlight_id="hl_01",
            round_number=19,
            camera_type=CameraType.FIRST_PERSON,
            purpose=ShotPurpose.PRIMARY_ACTION,
            start_tick=1000,
            end_tick=2000,
            start_time=10.0,
            end_time=20.0,
            duration_seconds=10.0,
            fov=90.0,
        )
        report = scorer.score_shot(shot)
        assert report.score >= 90.0
        assert report.clipping_risk is False
        assert report.status == "VERIFIED"

    def test_shoulder_cam_experimental_and_fallback(self):
        scorer = CameraQualityScorer()
        shot = CinematicShot(
            shot_id="shot_shoulder",
            highlight_id="hl_01",
            round_number=19,
            camera_type=CameraType.SHOULDER_CAM,
            purpose=ShotPurpose.APPROACH,
            start_tick=1000,
            end_tick=1500,
            start_time=10.0,
            end_time=15.0,
            duration_seconds=5.0,
            fov=95.0,
        )
        # Normal open space
        report_open = scorer.score_shot(shot, corridor_narrow=False)
        assert report_open.status == "EXPERIMENTAL"
        assert report_open.clipping_risk is False

        # Narrow corridor -> clipping risk flagged and fallback recommended
        report_narrow = scorer.score_shot(shot, corridor_narrow=True)
        assert report_narrow.clipping_risk is True
        assert any("fallback" in r.lower() for r in report_narrow.recommendations)

    def test_freecam_review_in_tight_spaces(self):
        scorer = CameraQualityScorer()
        shot = CinematicShot(
            shot_id="shot_flyby",
            highlight_id="hl_01",
            round_number=19,
            camera_type=CameraType.FREECAM_FLYBY,
            purpose=ShotPurpose.APPROACH,
            start_tick=1000,
            end_tick=1500,
            start_time=10.0,
            end_time=15.0,
            duration_seconds=5.0,
            fov=85.0,
        )
        report_tight = scorer.score_shot(shot, corridor_narrow=True)
        assert report_tight.status == "NEEDS_PREVIEW_REVIEW"
        assert report_tight.clipping_risk is True


class TestCinematicDirectorV2:
    def test_narrative_pacing_and_shot_budget(self):
        director = CinematicDirectorV2()
        kills = [
            {"tick": 120927, "attacker_name": "pytoshka_", "victim_name": "Tiger07", "weapon": "m4a1", "headshot": False},
            {"tick": 121263, "attacker_name": "pytoshka_", "victim_name": "zuuuuuhhhhn", "weapon": "m4a1", "headshot": False},
            {"tick": 121491, "attacker_name": "pytoshka_", "victim_name": "ProfyfGames", "weapon": "m4a1", "headshot": True},
            {"tick": 121595, "attacker_name": "pytoshka_", "victim_name": "freekjkeee", "weapon": "m4a1", "headshot": False},
            {"tick": 121920, "attacker_name": "pytoshka_", "victim_name": "axuenchik002", "weapon": "m4a1", "headshot": False},
        ]
        decision = director.plan_cinematic_production(
            highlight_id="ace_r19",
            round_number=19,
            start_tick=120000,
            end_tick=122500,
            hero_steam_id="76561199036405932",
            hero_name="pytoshka_",
            kills=kills,
            highlight_type="ace",
        )

        # Objective: never render all 8 cameras by default; select 2-4 purposeful shots
        assert 2 <= len(decision.selected_shots) <= 4
        # Verify discarded camera explanations exist
        assert len(decision.discarded_cameras) >= 2
        # Check rapid multikill detected (kills 3 & 4 occur in <1.2s: ticks 121491 to 121595 is 104 ticks = 0.81s)
        assert decision.rapid_multikill is True
        # Check headshot slowmo segment generated
        assert len(decision.slow_motion_segments) >= 1
        assert any(s["timescale"] == 0.40 for s in decision.slow_motion_segments)


class TestOverlayGenerator:
    def test_multikill_badge_variants(self):
        b2 = generate_multikill_badge(2)
        assert "DOUBLE KILL" in b2
        b3 = generate_multikill_badge(3)
        assert "TRIPLE KILL" in b3
        b4 = generate_multikill_badge(4)
        assert "QUAD KILL" in b4
        b_ace = generate_multikill_badge(5, is_ace=True)
        assert "ACE" in b_ace
        assert "ROUND DOMINATION" in b_ace

    def test_visual_styles(self):
        ev = OverlayKillEvent(
            tick=1000,
            time_seconds=10.0,
            round_number=1,
            killer_name="pytoshka_",
            killer_steam_id="76561199036405932",
            victim_name="ram1x1",
            victim_steam_id="76561199886338966",
            weapon="usp_silencer",
            headshot=True,
            wallbang=False,
            noscope=False,
            thrusmoke=False,
            attackerblind=False,
            kill_number_in_round=1,
        )
        svg_cinematic = generate_svg_killfeed_badge(ev, style="cinematic")
        assert "url(#bgGrad)" in svg_cinematic

        svg_dark = generate_svg_killfeed_badge(ev, style="dark")
        assert "#f43f5e" in svg_dark

        svg_broadcast = generate_svg_killfeed_badge(ev, style="broadcast")
        assert "#3b82f6" in svg_broadcast

    def test_png_badge_render(self, tmp_path):
        ev = OverlayKillEvent(
            tick=1000,
            time_seconds=10.0,
            round_number=1,
            killer_name="pytoshka_",
            killer_steam_id="76561199036405932",
            victim_name="ram1x1",
            victim_steam_id="76561199886338966",
            weapon="m4a1",
            headshot=True,
            wallbang=True,
            noscope=False,
            thrusmoke=False,
            attackerblind=False,
            kill_number_in_round=3,
        )
        png_out = tmp_path / "badge.png"
        res = render_killfeed_png_badge(ev, png_out)
        assert res.exists()
        assert res.stat().st_size > 1000


class TestMusicSync:
    def test_beat_grid_and_snapping(self):
        grid = MusicBeatGrid.create(bpm=128.0, duration_seconds=10.0)
        assert grid.bpm == 128.0
        assert round(grid.beat_duration, 3) == 0.469
        # Test snapping to beat
        snapped = grid.snap_to_nearest_beat(1.0)
        assert abs(snapped - 0.9375) < 0.1 or abs(snapped - 1.4062) < 0.1

    def test_generate_music_track(self, tmp_path):
        wav_path = tmp_path / "test_music.wav"
        res = generate_placeholder_music_track(wav_path, duration_seconds=2.0, bpm=128.0)
        assert res.exists()
        assert res.stat().st_size > 50000


class TestProductionCoordinatorAndResolve:
    def test_state_checkpoint_saving_and_loading(self, tmp_path):
        coord = ProductionCoordinator(
            output_dir=tmp_path,
            demo_path=tmp_path / "dummy.dem",
        )
        coord.state = JobState.PLANNED
        coord.shot_statuses = {"shot_01": {"status": "QC_PASSED"}}
        coord.save_checkpoint()

        # New coordinator instance on same dir should load checkpoint
        coord2 = ProductionCoordinator(
            output_dir=tmp_path,
            demo_path=tmp_path / "dummy.dem",
        )
        loaded = coord2.load_checkpoint()
        assert loaded is True
        assert coord2.state == JobState.PLANNED
        assert "shot_01" in coord2.shot_statuses

    def test_davinci_resolve_python_script_generation(self, tmp_path):
        package = CinematicProductionPackage(
            package_id="pkg_test",
            demo_id="demo_01",
            demo_name="anubis_ace",
            map_name="de_anubis",
            created_at="2026-11-12T12:00:00Z",
            shots=[
                CinematicShot(
                    shot_id="shot_01",
                    highlight_id="hl_01",
                    round_number=19,
                    camera_type=CameraType.FIRST_PERSON,
                    purpose=ShotPurpose.PRIMARY_ACTION,
                    start_tick=1000,
                    end_tick=2000,
                    start_time=10.0,
                    end_time=20.0,
                    duration_seconds=10.0,
                    output_filename="shot_01.mp4",
                )
            ],
            overlay_events=[
                OverlayKillEvent(
                    tick=1500,
                    time_seconds=15.0,
                    round_number=19,
                    killer_name="pytoshka_",
                    killer_steam_id="76561199036405932",
                    victim_name="Tiger07",
                    victim_steam_id="",
                    weapon="m4a1",
                    headshot=True,
                    wallbang=False,
                    noscope=False,
                    thrusmoke=False,
                    attackerblind=False,
                    kill_number_in_round=1,
                    is_ace=True,
                )
            ],
            resolve_project_name="CS2_Test_Project",
        )
        script_file = tmp_path / "setup_resolve.py"
        content = generate_davinci_resolve_python_script(package, output_script_path=script_file)
        assert script_file.exists()
        assert "DaVinciResolveScript" in content
        assert "Hero POV (Master)" in content
        assert "Cinematic B-Roll" in content
        assert "Victim Reaction" in content
        assert "Overlays & Killfeed" in content
        assert "AddMarker" in content
