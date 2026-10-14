"""Unit tests for Video Render module (Stage G & Stage H)."""

from __future__ import annotations

import pathlib
import pytest

from backend.render.cfg_generator import generate_render_cfg, steam64_to_account_id
from backend.render.engine import RenderEngine
from backend.render.models import RenderTask
from backend.render.verifier import (
    verify_media_integrity,
    verify_mp4,
    verify_mp4_visual_content,
)


class TestRenderModels:
    def test_render_task_duration_calculation(self):
        task = RenderTask(
            task_id="t1",
            demo_path=pathlib.Path("match.dem"),
            start_tick=1280,
            end_tick=2560,
            pov_steam_id="76561198000000001",
            pov_name="Alice",
            tickrate=128,
        )
        assert task.duration_seconds == 10.0

    def test_render_task_duration_minimum_one_second(self):
        task = RenderTask(
            task_id="t2",
            demo_path=pathlib.Path("match.dem"),
            start_tick=100,
            end_tick=110,
            pov_steam_id=None,
            pov_name=None,
            tickrate=128,
        )
        assert task.duration_seconds == 1.0


class TestCfgGenerator:
    def test_steam64_conversion(self):
        # 76561197960265728 + 12345 = 76561197960278073
        steam64 = "76561197960278073"
        account_id = steam64_to_account_id(steam64)
        assert account_id == 12345

    def test_steam64_invalid_returns_none(self):
        assert steam64_to_account_id("not_a_number") is None
        assert steam64_to_account_id(None) is None

    def test_generate_cfg_content(self, tmp_path):
        cfg_path = tmp_path / "test.cfg"
        content = generate_render_cfg(
            start_tick=5000,
            pov_steam_id="76561197960278073",
            pov_name="Alice",
            output_cfg_path=cfg_path,
        )

        assert "demo_gototick 5000" in content
        assert "spec_autodirector 0" in content
        assert "spec_mode 4" in content
        assert "spec_player Alice" in content
        assert "spec_lock_to_accountid 12345" in content
        assert cfg_path.exists()

    def test_generate_cfg_content_with_hlae_recording(self, tmp_path):
        cfg_path = tmp_path / "test_hlae.cfg"
        out_dir = tmp_path / "output_record"
        content = generate_render_cfg(
            start_tick=5000,
            end_tick=5300,
            pov_steam_id="76561197960278073",
            pov_name="Alice",
            output_dir=out_dir,
            fps=60,
            output_cfg_path=cfg_path,
        )

        assert "mirv_streams record name" in content
        assert "mirv_streams record fps 60" in content
        assert "mirv_streams record screen enabled 1" in content
        assert "mirv_streams record screen settings afxFfmpegYuv420p" in content
        assert "spec_lock_to_accountid 12345" in content
        assert 'mirv_cmd addAtTick 5000 "spec_autodirector 0; spec_mode 4; spec_lock_to_accountid 12345; spec_player Alice; cl_trueview_show_status 0; demo_ui_mode 0; cl_spec_show_bindings 0; mirv_streams record start"' in content
        assert 'mirv_cmd addAtTick 5300 "mirv_streams record end; quit"' in content
        assert "r_show_build_info 0" in content
        assert "spec_show_xray 1" in content
        assert "cl_draw_only_deathnotices 0" in content
        assert "cl_trueview_show_status 0" in content
        assert "demo_ui_mode 0" in content
        assert "cl_spec_show_bindings 0" in content
        assert "cl_crosshairstyle 4" in content
        assert cfg_path.exists()

    def test_generate_cfg_xray_disabled(self, tmp_path):
        cfg_path = tmp_path / "test_no_xray.cfg"
        content = generate_render_cfg(
            start_tick=5000,
            xray=False,
            output_cfg_path=cfg_path,
        )
        assert "spec_show_xray 0" in content
        assert "mirv_fix selectedPlayerGlow 0" in content

    def test_generate_cfg_hud_killfeed_only(self, tmp_path):
        cfg_path = tmp_path / "test_killfeed.cfg"
        content = generate_render_cfg(
            start_tick=5000,
            hud_mode="killfeed_only",
            output_cfg_path=cfg_path,
        )
        assert "cl_drawhud 1" in content
        assert "cl_draw_only_deathnotices 1" in content

    def test_generate_cfg_hud_none(self, tmp_path):
        cfg_path = tmp_path / "test_no_hud.cfg"
        content = generate_render_cfg(
            start_tick=5000,
            hud_mode="none",
            output_cfg_path=cfg_path,
        )
        assert "cl_drawhud 0" in content

    def test_generate_cfg_hud_huge_modes(self):
        content_huge = generate_render_cfg(start_tick=5000, hud_mode="huge_esports")
        assert "hud_scaling 1.15" in content_huge
        assert "cl_drawhud 1" in content_huge
        assert "cl_draw_only_deathnotices 0" in content_huge

        content_kf = generate_render_cfg(start_tick=5000, hud_mode="huge_killfeed")
        assert "hud_scaling 1.15" in content_kf
        assert "cl_drawhud 1" in content_kf
        assert "cl_draw_only_deathnotices 1" in content_kf

    def test_generate_cfg_radar_modes(self, tmp_path):
        cfg_path = tmp_path / "test_radar.cfg"
        content_bc = generate_render_cfg(
            start_tick=5000,
            radar_mode="broadcast",
            output_cfg_path=cfg_path,
        )
        assert "cl_radar_always_centered 0" in content_bc
        assert "cl_radar_scale 0.55" in content_bc
        assert "cl_radar_rotate 0" in content_bc

        content_pf = generate_render_cfg(start_tick=5000, radar_mode="player_focus")
        assert "cl_radar_always_centered 1" in content_pf
        assert "cl_radar_rotate 1" in content_pf

        content_dl = generate_render_cfg(start_tick=5000, radar_mode="dynamic_large")
        assert "cl_hud_radar_scale 1.30" in content_dl
        assert "cl_radar_always_centered 1" in content_dl
        assert "cl_radar_rotate 1" in content_dl
        assert "cl_radar_scale 0.70" in content_dl

        content_bg = generate_render_cfg(start_tick=5000, radar_mode="broadcast_giant")
        assert "cl_hud_radar_scale 1.30" in content_bg
        assert "cl_radar_always_centered 0" in content_bg
        assert "cl_radar_rotate 0" in content_bg

    def test_generate_cfg_camera_switches(self, tmp_path):
        cfg_path = tmp_path / "test_switches.cfg"
        switches = [
            (5100, "76561197960278073", "Victim1"),
            (5200, "76561197960278074", "Hero"),
        ]
        content = generate_render_cfg(
            start_tick=5000,
            end_tick=5300,
            output_dir=tmp_path / "out",
            camera_switches=switches,
            output_cfg_path=cfg_path,
        )
        assert 'mirv_cmd addAtTick 5100 "spec_autodirector 0; spec_mode 4; spec_lock_to_accountid 12345; spec_player Victim1"' in content
        assert 'mirv_cmd addAtTick 5200 "spec_autodirector 0; spec_mode 4; spec_lock_to_accountid 12346; spec_player Hero"' in content

    def test_dynamic_killcam_switches_timing(self, tmp_path):
        tickrate = 64
        kill_tick = 5000
        hero_lead = int(2.0 * tickrate)
        vic_duration = int(2.2 * tickrate)
        hero_switch = kill_tick - hero_lead
        vic_switch = hero_switch - vic_duration

        switches = [
            (vic_switch, "76561197960278073", "VictimPlayer"),
            (hero_switch, "76561197960278074", "HeroPlayer"),
        ]
        content = generate_render_cfg(
            start_tick=4500,
            end_tick=5200,
            output_dir=tmp_path / "out",
            camera_switches=switches,
        )
        assert f"mirv_cmd addAtTick {vic_switch}" in content
        assert f"mirv_cmd addAtTick {hero_switch}" in content
        assert "spec_player VictimPlayer" in content
        assert "spec_player HeroPlayer" in content
        assert kill_tick - hero_switch >= int(2.0 * tickrate)

    def test_generate_cfg_linear_recording_pass(self, tmp_path):
        """Verify linear CFG generation: seek forward, record start, record end & quit without backward loops."""
        out_dir = tmp_path / "clip_out"
        cfg_path = tmp_path / "clip.cfg"
        content = generate_render_cfg(
            start_tick=4800,
            end_tick=5080,
            output_dir=out_dir,
            output_cfg_path=cfg_path,
            fps=60,
            pov_steam_id="76561197960278073",
            pov_name="VictimPlayer",
        )

        assert "demo_gototick 4780" in content
        assert "spec_player VictimPlayer" in content
        assert 'mirv_cmd addAtTick 4800 "spec_autodirector 0; spec_mode 4; spec_lock_to_accountid 12345; spec_player VictimPlayer; cl_trueview_show_status 0; demo_ui_mode 0; cl_spec_show_bindings 0; mirv_streams record start"' in content
        assert 'mirv_cmd addAtTick 5080 "mirv_streams record end; quit"' in content
        assert cfg_path.exists()

    def test_generate_batch_render_cfg(self, tmp_path):
        from backend.render.cfg_generator import BatchClipItem, generate_batch_render_cfg

        cfg_path = tmp_path / "batch.cfg"
        out_dir = tmp_path / "batch_out"
        clips = [
            BatchClipItem(
                clip_id="clip_1",
                start_tick=1000,
                end_tick=1500,
                pov_steam_id="76561197960278073",
                pov_name="Alice",
            ),
            BatchClipItem(
                clip_id="clip_2",
                start_tick=3000,
                end_tick=3500,
                pov_steam_id="76561197960278074",
                pov_name="Bob",
            ),
        ]
        content = generate_batch_render_cfg(
            clips=clips,
            output_dir=out_dir,
            output_cfg_path=cfg_path,
            fps=60,
        )
        assert "demo_gototick 980" in content
        assert "cl_trueview_show_status 0" in content
        assert "demo_ui_mode 0" in content
        assert "demo_gototick 2980" in content
        assert 'mirv_cmd addAtTick 1500 "mirv_streams record end; demo_gototick 2980; demo_resume"' in content
        assert 'mirv_cmd addAtTick 3500 "mirv_streams record end; quit"' in content
        assert " 0 0" not in content
        # Ensure every single command line fits safely within Source 2 console buffer (< 200 chars)
        assert all(len(line) < 200 for line in content.splitlines())
        assert cfg_path.exists()


class TestVerifier:
    def test_missing_file_returns_false(self, tmp_path):
        missing = tmp_path / "nonexistent.mp4"
        is_valid, duration, err = verify_mp4(missing)
        assert not is_valid
        assert "does not exist" in (err or "")

    def test_empty_file_returns_false(self, tmp_path):
        empty = tmp_path / "empty.mp4"
        empty.touch()
        is_valid, duration, err = verify_mp4(empty)
        assert not is_valid
        assert "empty" in (err or "")

    def test_visual_verification_missing_file(self, tmp_path):
        missing = tmp_path / "missing.mp4"
        is_vis, err = verify_mp4_visual_content(missing)
        assert not is_vis
        assert "does not exist" in (err or "").lower()

    def test_visual_verification_on_poc_video(self):
        poc_video = pathlib.Path("renders/hlae_poc/take0000/video.mp4")
        if not poc_video.exists():
            pytest.skip("PoC video not present on disk")
        is_vis, err = verify_mp4_visual_content(poc_video, sample_seconds=[1.0, 2.0])
        assert is_vis
        assert err is None

    def test_media_integrity_missing_file_returns_false(self, tmp_path):
        missing = tmp_path / "nonexistent.mp4"
        is_intact, err = verify_media_integrity(missing)
        assert not is_intact
        assert "does not exist" in (err or "").lower()

    def test_verify_mp4_codec_validation(self):
        poc_video = pathlib.Path("renders/hlae_poc/take0000/video.mp4")
        if not poc_video.exists():
            pytest.skip("PoC video not present on disk")
        # Passing correct codec
        valid, dur, err = verify_mp4(poc_video, expected_video_codec="h264")
        assert valid
        assert err is None

        # Rejecting mismatched video codec
        invalid, _, err = verify_mp4(poc_video, expected_video_codec="vp9")
        assert not invalid
        assert "expected 'vp9'" in (err or "").lower()

    def test_verify_media_integrity_on_real_fixture(self):
        poc_video = pathlib.Path("renders/hlae_poc/take0000/video.mp4")
        if not poc_video.exists():
            pytest.skip("PoC video not present on disk")
        is_intact, err = verify_media_integrity(poc_video)
        assert is_intact
        assert err is None


class TestRenderEngineValidation:
    def test_missing_cs2_returns_error(self, tmp_path):
        engine = RenderEngine(
            cs2_exe=tmp_path / "nonexistent_cs2.exe",
            hlae_exe=tmp_path / "HLAE.exe",
            hook_dll=tmp_path / "AfxHookSource2.dll",
        )
        task = RenderTask(
            task_id="test_missing_cs2",
            demo_path=tmp_path / "dummy.dem",
            start_tick=100,
            end_tick=200,
            pov_steam_id=None,
            pov_name=None,
        )
        res = engine.render_clip(task)
        assert not res.success
        assert "cs2 executable not found" in (res.error_message or "").lower()

    def test_missing_hlae_returns_error(self, tmp_path):
        cs2_dummy = tmp_path / "cs2.exe"
        cs2_dummy.touch()
        engine = RenderEngine(
            cs2_exe=cs2_dummy,
            hlae_exe=tmp_path / "nonexistent_hlae.exe",
            hook_dll=tmp_path / "AfxHookSource2.dll",
        )
        task = RenderTask(
            task_id="test_missing_hlae",
            demo_path=tmp_path / "dummy.dem",
            start_tick=100,
            end_tick=200,
            pov_steam_id=None,
            pov_name=None,
        )
        res = engine.render_clip(task)
        assert not res.success
        assert "hlae executable not found" in (res.error_message or "").lower()

    def test_missing_hook_dll_returns_error(self, tmp_path):
        cs2_dummy = tmp_path / "cs2.exe"
        cs2_dummy.touch()
        hlae_dummy = tmp_path / "HLAE.exe"
        hlae_dummy.touch()
        engine = RenderEngine(
            cs2_exe=cs2_dummy,
            hlae_exe=hlae_dummy,
            hook_dll=tmp_path / "nonexistent_hook.dll",
        )
        task = RenderTask(
            task_id="test_missing_dll",
            demo_path=tmp_path / "dummy.dem",
            start_tick=100,
            end_tick=200,
            pov_steam_id=None,
            pov_name=None,
        )
        res = engine.render_clip(task)
        assert not res.success
        assert "afxhooksource2.dll not found" in (res.error_message or "").lower()

    def test_missing_demo_returns_error(self, tmp_path):
        cs2_dummy = tmp_path / "cs2.exe"
        cs2_dummy.touch()
        hlae_dummy = tmp_path / "HLAE.exe"
        hlae_dummy.touch()
        hook_dummy = tmp_path / "AfxHookSource2.dll"
        hook_dummy.touch()

        engine = RenderEngine(
            cs2_exe=cs2_dummy,
            hlae_exe=hlae_dummy,
            hook_dll=hook_dummy,
        )
        task = RenderTask(
            task_id="test_missing_demo",
            demo_path=tmp_path / "missing.dem",
            start_tick=100,
            end_tick=200,
            pov_steam_id=None,
            pov_name=None,
        )
        res = engine.render_clip(task)
        assert not res.success
        assert "not found" in (res.error_message or "").lower()

    def test_render_batch_empty(self, tmp_path):
        engine = RenderEngine()
        assert engine.render_batch([]) == []

    def test_render_batch_missing_executables(self, tmp_path):
        engine = RenderEngine(
            cs2_exe=tmp_path / "missing_cs2.exe",
            hlae_exe=tmp_path / "missing_hlae.exe",
            hook_dll=tmp_path / "missing_hook.dll",
        )
        task1 = RenderTask(
            task_id="t1",
            demo_path=tmp_path / "demo.dem",
            start_tick=100,
            end_tick=200,
            pov_steam_id=None,
            pov_name=None,
        )
        task2 = RenderTask(
            task_id="t2",
            demo_path=tmp_path / "demo.dem",
            start_tick=300,
            end_tick=400,
            pov_steam_id=None,
            pov_name=None,
        )
        results = engine.render_batch([task1, task2])
        assert len(results) == 2
        assert not results[0].success
        assert not results[1].success
        assert "not found" in (results[0].error_message or "").lower()

    def test_profiles_configuration(self):
        from backend.render.profiles import RenderProfileType, get_profile
        comp = get_profile(RenderProfileType.CLEAN_COMPETITIVE)
        assert comp.deathnotices_only is True
        assert comp.draw_hud is True
        assert comp.trueview_suppressed is True

        cine = get_profile(RenderProfileType.CINEMATIC)
        assert cine.draw_hud is False
        assert cine.custom_crosshair is False
        assert cine.trueview_suppressed is True

    def test_render_clip_tournament_killcam_two_pass_staging(self, tmp_path, monkeypatch):
        """Verify that tournament killcam triggers two sequential passes (Victim then Hero) and concatenates via create_montage."""
        from unittest.mock import MagicMock
        from backend.render.montage import MontageResult

        dummy_cs2 = tmp_path / "cs2.exe"
        dummy_cs2.write_text("cs2")
        dummy_hlae = tmp_path / "hlae.exe"
        dummy_hlae.write_text("hlae")
        dummy_hook = tmp_path / "hook.dll"
        dummy_hook.write_text("hook")
        dummy_demo = tmp_path / "match.dem"
        dummy_demo.write_text("demo")

        engine = RenderEngine(
            cs2_exe=dummy_cs2,
            hlae_exe=dummy_hlae,
            hook_dll=dummy_hook,
        )

        out_mp4 = tmp_path / "final_killcam.mp4"
        task = RenderTask(
            task_id="kc_task_123",
            demo_path=dummy_demo,
            start_tick=5000,
            end_tick=5800,
            pov_steam_id="76561197960278074",
            pov_name="HeroAttacker",
            output_path=out_mp4,
            is_killcam_replay=True,
            killcam_victim_steam_id="76561197960278073",
            killcam_victim_name="VictimPlayer",
            killcam_victim_start_tick=4800,
            killcam_victim_end_tick=5080,
            killcam_hero_start_tick=4750,
        )

        # Track calls to _execute_cs2_pass
        executed_passes = []

        def mock_execute_pass(task, subtask_id, start_tick, end_tick, pov_steam_id, pov_name, output_mp4, camera_switches=None, log_file=None):
            executed_passes.append({
                "subtask_id": subtask_id,
                "start_tick": start_tick,
                "end_tick": end_tick,
                "pov_name": pov_name,
                "pov_steam_id": pov_steam_id,
                "output_mp4": output_mp4,
            })
            output_mp4.parent.mkdir(parents=True, exist_ok=True)
            output_mp4.write_text(f"dummy video for {subtask_id}")
            return True, None, True, None

        monkeypatch.setattr(engine, "_execute_cs2_pass", mock_execute_pass)

        mock_montage = MagicMock()
        def mock_montage_call(clip_paths, output_path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("stitched final killcam")
            return MontageResult(success=True, output_path=output_path, duration_seconds=10.0, clip_count=len(clip_paths))

        monkeypatch.setattr("backend.render.engine.create_montage", mock_montage_call)
        monkeypatch.setattr("backend.render.engine.verify_mp4", lambda *args, **kwargs: (True, 10.0, None))
        monkeypatch.setattr("backend.render.engine.verify_media_integrity", lambda *args, **kwargs: (True, None))
        monkeypatch.setattr("backend.render.engine.verify_mp4_visual_content", lambda *args, **kwargs: (True, None))
        monkeypatch.setattr("backend.render.engine.verify_mp4_audio_signal", lambda *args, **kwargs: (True, 0.0, -14.0, None))

        result = engine.render_clip(task)

        assert result.success is True
        assert len(executed_passes) == 2

        # Pass 1: Victim view
        assert executed_passes[0]["subtask_id"] == "kc_task_123_vic"
        assert executed_passes[0]["start_tick"] == 4800
        assert executed_passes[0]["end_tick"] == 5080
        assert executed_passes[0]["pov_name"] == "VictimPlayer"
        assert executed_passes[0]["pov_steam_id"] == "76561197960278073"

        # Pass 2: Hero view
        assert executed_passes[1]["subtask_id"] == "kc_task_123_hero"
        assert executed_passes[1]["start_tick"] == 4750
        assert executed_passes[1]["end_tick"] == 5800
        assert executed_passes[1]["pov_name"] == "HeroAttacker"
        assert executed_passes[1]["pov_steam_id"] == "76561197960278074"

