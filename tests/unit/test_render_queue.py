"""Unit tests for RenderQueueManager, sequential execution, and path security."""

from __future__ import annotations

import asyncio
import json
import pathlib
import pytest
from unittest.mock import MagicMock, patch

from backend.parser.errors import InvalidDemoPathError
from backend.render.models import RenderResult, RenderTask
from backend.render.queue import (
    RenderQueueManager,
    parse_render_resolution,
    sanitize_output_path,
    validate_render_demo_path,
)
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.models import DemoModel, HighlightModel, KillEventModel, PlayerModel, RenderJobModel
from backend.storage.repository import DemoRepository


@pytest.fixture
def db_session_factory(tmp_path):
    """Isolated SQLite session factory."""
    db_file = tmp_path / "test_queue.db"
    engine = create_db_engine(f"sqlite:///{db_file}")
    init_db(engine)
    return get_session_factory(engine)


class TestPathSecurity:
    def test_sanitize_output_path_valid(self, tmp_path):
        out = sanitize_output_path("test-job-123", base_dir=tmp_path)
        assert out.name == "clip_test-job-123.mp4"
        assert out.parent == tmp_path.resolve()

    def test_sanitize_output_path_rejects_traversal(self, tmp_path):
        with pytest.raises(ValueError):
            # Attempting traversal inside job_id
            sanitize_output_path("../../../etc/passwd", base_dir=tmp_path)

    def test_sanitize_output_path_collision_prevention(self, tmp_path):
        out1 = sanitize_output_path("job_dup", base_dir=tmp_path, highlight_id="hl1")
        assert out1.name == "clip_job_dup_hl1.mp4"
        out1.touch()

        # Second call with same name must append counter rather than overwriting
        out2 = sanitize_output_path("job_dup", base_dir=tmp_path, highlight_id="hl1")
        assert out2.name == "clip_job_dup_hl1_1.mp4"
        assert out2 != out1

    def test_validate_demo_path_nonexistent(self, tmp_path):
        with pytest.raises(InvalidDemoPathError):
            validate_render_demo_path(str(tmp_path / "missing.dem"))

    def test_validate_demo_path_invalid_extension(self, tmp_path):
        bad_file = tmp_path / "script.exe"
        bad_file.touch()
        with pytest.raises(InvalidDemoPathError):
            validate_render_demo_path(str(bad_file))


class TestRenderQueueManager:
    @pytest.mark.asyncio
    async def test_sequential_processing_success(self, db_session_factory, tmp_path):
        # Setup demo and highlights in DB
        demo_file = tmp_path / "match.dem"
        demo_file.write_bytes(b"PBDEMS2\x00" + b"\x00" * 2000)

        with db_session_factory() as sess:
            demo = DemoModel(
                fingerprint="fp1",
                file_path=str(demo_file),
                map_name="de_dust2",
                tickrate=64,
                duration_seconds=120.0,
                schema_version="1",
            )
            sess.add(demo)
            sess.flush()

            hl = HighlightModel(
                id="hl_1",
                demo_id=demo.id,
                highlight_type="kill",
                round_num=1,
                pov_steam_id="76561198000000001",
                pov_name="Alice",
                kill_start_tick=1000,
                kill_end_tick=1000,
                clip_start_tick=800,
                clip_end_tick=1200,
                kill_count=1,
            )
            sess.add(hl)
            sess.flush()

            job1 = RenderJobModel(
                id="job_seq_1",
                demo_id=demo.id,
                highlight_id="hl_1",
                settings_json=json.dumps({"resolution": "1080p", "fps": 60}),
                status="pending",
                progress=0.0,
            )
            job2 = RenderJobModel(
                id="job_seq_2",
                demo_id=demo.id,
                highlight_id="hl_1",
                settings_json=json.dumps({"resolution": "1080p", "fps": 60}),
                status="pending",
                progress=0.0,
            )
            sess.add_all([job1, job2])
            sess.commit()

        # Mock render engine that tracks execution concurrency
        active_renders = 0
        max_concurrent_renders = 0

        mock_engine = MagicMock()

        def fake_render_clip(task: RenderTask) -> RenderResult:
            nonlocal active_renders, max_concurrent_renders
            active_renders += 1
            max_concurrent_renders = max(max_concurrent_renders, active_renders)

            out_file = task.output_path
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.touch()

            active_renders -= 1
            return RenderResult(
                success=True,
                output_path=out_file,
                duration_seconds=5.0,
            )

        mock_engine.render_clip.side_effect = fake_render_clip

        manager = RenderQueueManager(
            session_factory=db_session_factory,
            render_engine=mock_engine,
            output_dir=tmp_path,
        )
        manager.start()

        # Enqueue two jobs
        await manager.enqueue("job_seq_1")
        await manager.enqueue("job_seq_2")

        # Wait for queue to be drained
        for _ in range(50):
            await asyncio.sleep(0.05)
            with db_session_factory() as sess:
                j1 = sess.get(RenderJobModel, "job_seq_1")
                j2 = sess.get(RenderJobModel, "job_seq_2")
                if j1 and j2 and j1.status == "completed" and j2.status == "completed":
                    break

        await manager.stop()

        with db_session_factory() as sess:
            j1 = sess.get(RenderJobModel, "job_seq_1")
            j2 = sess.get(RenderJobModel, "job_seq_2")
            assert j1.status == "completed"
            assert j1.progress == 1.0
            assert j1.output_path is not None
            assert j2.status == "completed"
            assert j2.progress == 1.0
            assert j2.output_path is not None

        # STRICT SEQUENTIAL GUARANTEE: at no point was there more than 1 concurrent render!
        assert max_concurrent_renders == 1
        assert mock_engine.render_clip.call_count == 2

    @pytest.mark.asyncio
    async def test_render_failure_recorded_in_db(self, db_session_factory, tmp_path):
        demo_file = tmp_path / "match.dem"
        demo_file.write_bytes(b"PBDEMS2\x00" + b"\x00" * 2000)

        with db_session_factory() as sess:
            demo = DemoModel(
                fingerprint="fp_fail",
                file_path=str(demo_file),
                map_name="de_dust2",
                tickrate=64,
                duration_seconds=120.0,
                schema_version="1",
            )
            sess.add(demo)
            sess.flush()

            job = RenderJobModel(
                id="job_fail_1",
                demo_id=demo.id,
                highlight_id=None,
                settings_json=json.dumps({"resolution": "1080p", "fps": 60}),
                status="pending",
                progress=0.0,
            )
            sess.add(job)
            sess.commit()

        mock_engine = MagicMock()
        mock_engine.render_clip.return_value = RenderResult(
            success=False,
            output_path=None,
            duration_seconds=0.0,
            error_message="HLAE crash: timeout waiting for CS2",
        )

        manager = RenderQueueManager(
            session_factory=db_session_factory,
            render_engine=mock_engine,
            output_dir=tmp_path,
        )
        manager.start()

        await manager.enqueue("job_fail_1")

        for _ in range(50):
            await asyncio.sleep(0.05)
            with db_session_factory() as sess:
                j = sess.get(RenderJobModel, "job_fail_1")
                if j and j.status == "failed":
                    break

        await manager.stop()

        with db_session_factory() as sess:
            j = sess.get(RenderJobModel, "job_fail_1")
            assert j.status == "failed"
            assert j.progress == 0.0
            assert "HLAE crash" in (j.error_summary or "")

    @pytest.mark.asyncio
    async def test_queue_victim_pov_and_settings(self, db_session_factory, tmp_path):
        demo_file = tmp_path / "match.dem"
        demo_file.write_bytes(b"PBDEMS2\x00" + b"\x00" * 2000)

        with db_session_factory() as sess:
            demo = DemoModel(
                fingerprint="fp_victim",
                file_path=str(demo_file),
                map_name="de_dust2",
                tickrate=64,
                duration_seconds=120.0,
                schema_version="1",
            )
            sess.add(demo)
            sess.flush()

            hl = HighlightModel(
                id="hl_victim_1",
                demo_id=demo.id,
                highlight_type="kill",
                round_num=2,
                pov_steam_id="76561198000000001",
                pov_name="Attacker",
                kill_start_tick=1000,
                kill_end_tick=1000,
                clip_start_tick=800,
                clip_end_tick=1200,
                kill_count=1,
            )
            sess.add(hl)

            kill = KillEventModel(
                demo_id=demo.id,
                tick=1000,
                round_num=2,
                attacker_name="Attacker",
                attacker_steam_id="76561198000000001",
                attacker_team="ct",
                victim_name="VictimPlayer",
                victim_steam_id="76561198999999999",
                victim_team="t",
                weapon="ak47",
                headshot=True,
                hitgroup="head",
                noscope=False,
                thru_smoke=False,
                attacker_blind=False,
                wallbang=False,
            )
            sess.add(kill)

            job = RenderJobModel(
                id="job_victim_1",
                demo_id=demo.id,
                highlight_id="hl_victim_1",
                settings_json=json.dumps({
                    "resolution": "1080p",
                    "fps": 60,
                    "perspective": "victim",
                    "xray": False,
                    "hud_mode": "killfeed_only",
                }),
                status="pending",
                progress=0.0,
            )
            sess.add(job)
            sess.commit()

        captured_task: RenderTask | None = None

        mock_engine = MagicMock()
        def fake_render(task: RenderTask) -> RenderResult:
            nonlocal captured_task
            captured_task = task
            out_file = task.output_path
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.touch()
            return RenderResult(success=True, output_path=out_file, duration_seconds=4.0)

        mock_engine.render_clip.side_effect = fake_render

        manager = RenderQueueManager(
            session_factory=db_session_factory,
            render_engine=mock_engine,
            output_dir=tmp_path,
        )
        manager.start()
        await manager.enqueue("job_victim_1")

        for _ in range(50):
            await asyncio.sleep(0.05)
            with db_session_factory() as sess:
                j = sess.get(RenderJobModel, "job_victim_1")
                if j and j.status == "completed":
                    break

        await manager.stop()

        assert captured_task is not None
        assert captured_task.pov_steam_id == "76561198999999999"
        assert captured_task.pov_name == "VictimPlayer"
        assert captured_task.xray is False
        assert captured_task.hud_mode == "killfeed_only"
        assert captured_task.perspective == "victim"

    @pytest.mark.asyncio
    async def test_queue_victim_not_found_fails_with_clear_error(self, db_session_factory, tmp_path):
        """When victim POV is requested but no victim exists, job must fail with clear error."""
        demo_file = tmp_path / "match.dem"
        demo_file.write_bytes(b"PBDEMS2\x00" + b"\x00" * 2000)

        with db_session_factory() as sess:
            demo = DemoModel(
                fingerprint="fp_novictim",
                file_path=str(demo_file),
                map_name="de_dust2",
                tickrate=64,
                duration_seconds=120.0,
                schema_version="1",
            )
            sess.add(demo)
            sess.flush()

            hl = HighlightModel(
                id="hl_novictim_1",
                demo_id=demo.id,
                highlight_type="kill",
                round_num=3,
                pov_steam_id="76561198000000001",
                pov_name="Attacker",
                kill_start_tick=1000,
                kill_end_tick=1000,
                clip_start_tick=800,
                clip_end_tick=1200,
                kill_count=1,
            )
            sess.add(hl)

            job = RenderJobModel(
                id="job_novictim_1",
                demo_id=demo.id,
                highlight_id="hl_novictim_1",
                settings_json=json.dumps({"perspective": "victim"}),
                status="pending",
                progress=0.0,
            )
            sess.add(job)
            sess.commit()

        mock_engine = MagicMock()
        manager = RenderQueueManager(
            session_factory=db_session_factory,
            render_engine=mock_engine,
            output_dir=tmp_path,
        )
        manager.start()
        await manager.enqueue("job_novictim_1")

        for _ in range(50):
            await asyncio.sleep(0.05)
            with db_session_factory() as sess:
                j = sess.get(RenderJobModel, "job_novictim_1")
                if j and j.status == "failed":
                    break

        await manager.stop()

        with db_session_factory() as sess:
            j = sess.get(RenderJobModel, "job_novictim_1")
            assert j.status == "failed"
            assert "Victim not found" in (j.error_summary or "")
        assert mock_engine.render_clip.call_count == 0

    @pytest.mark.asyncio
    async def test_queue_specific_player_valid_selection(self, db_session_factory, tmp_path):
        """When specific_player POV is requested with valid player, that player is selected."""
        demo_file = tmp_path / "match.dem"
        demo_file.write_bytes(b"PBDEMS2\x00" + b"\x00" * 2000)

        with db_session_factory() as sess:
            demo = DemoModel(
                fingerprint="fp_spec_valid",
                file_path=str(demo_file),
                map_name="de_dust2",
                tickrate=64,
                duration_seconds=120.0,
                schema_version="1",
            )
            sess.add(demo)
            sess.flush()

            player = PlayerModel(
                demo_id=demo.id,
                steam_id="76561198555555555",
                name="TargetPlayer",
                team="ct",
            )
            sess.add(player)

            hl = HighlightModel(
                id="hl_spec_1",
                demo_id=demo.id,
                highlight_type="kill",
                round_num=1,
                pov_steam_id="76561198000000001",
                pov_name="Attacker",
                kill_start_tick=1000,
                kill_end_tick=1000,
                clip_start_tick=800,
                clip_end_tick=1200,
                kill_count=1,
            )
            sess.add(hl)

            job = RenderJobModel(
                id="job_spec_1",
                demo_id=demo.id,
                highlight_id="hl_spec_1",
                settings_json=json.dumps({
                    "perspective": "specific_player",
                    "perspective_steam_id": "76561198555555555",
                }),
                status="pending",
                progress=0.0,
            )
            sess.add(job)
            sess.commit()

        captured_task: RenderTask | None = None
        mock_engine = MagicMock()
        def fake_render(task: RenderTask) -> RenderResult:
            nonlocal captured_task
            captured_task = task
            out_file = task.output_path
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.touch()
            return RenderResult(success=True, output_path=out_file, duration_seconds=3.0)

        mock_engine.render_clip.side_effect = fake_render

        manager = RenderQueueManager(
            session_factory=db_session_factory,
            render_engine=mock_engine,
            output_dir=tmp_path,
        )
        manager.start()
        await manager.enqueue("job_spec_1")

        for _ in range(50):
            await asyncio.sleep(0.05)
            with db_session_factory() as sess:
                j = sess.get(RenderJobModel, "job_spec_1")
                if j and j.status == "completed":
                    break

        await manager.stop()

        assert captured_task is not None
        assert captured_task.pov_steam_id == "76561198555555555"
        assert captured_task.pov_name == "TargetPlayer"
        assert captured_task.perspective == "specific_player"

    @pytest.mark.asyncio
    async def test_queue_specific_player_not_found_fails_with_clear_error(self, db_session_factory, tmp_path):
        """When specific_player POV is not found in demo players, fail without substituting."""
        demo_file = tmp_path / "match.dem"
        demo_file.write_bytes(b"PBDEMS2\x00" + b"\x00" * 2000)

        with db_session_factory() as sess:
            demo = DemoModel(
                fingerprint="fp_spec_invalid",
                file_path=str(demo_file),
                map_name="de_dust2",
                tickrate=64,
                duration_seconds=120.0,
                schema_version="1",
            )
            sess.add(demo)
            sess.flush()

            hl = HighlightModel(
                id="hl_spec_inv",
                demo_id=demo.id,
                highlight_type="kill",
                round_num=1,
                pov_steam_id="76561198000000001",
                pov_name="Attacker",
                kill_start_tick=1000,
                kill_end_tick=1000,
                clip_start_tick=800,
                clip_end_tick=1200,
                kill_count=1,
            )
            sess.add(hl)

            job = RenderJobModel(
                id="job_spec_inv",
                demo_id=demo.id,
                highlight_id="hl_spec_inv",
                settings_json=json.dumps({
                    "perspective": "specific_player",
                    "perspective_steam_id": "99999999999999999",
                }),
                status="pending",
                progress=0.0,
            )
            sess.add(job)
            sess.commit()

        mock_engine = MagicMock()
        manager = RenderQueueManager(
            session_factory=db_session_factory,
            render_engine=mock_engine,
            output_dir=tmp_path,
        )
        manager.start()
        await manager.enqueue("job_spec_inv")

        for _ in range(50):
            await asyncio.sleep(0.05)
            with db_session_factory() as sess:
                j = sess.get(RenderJobModel, "job_spec_inv")
                if j and j.status == "failed":
                    break

        await manager.stop()

        with db_session_factory() as sess:
            j = sess.get(RenderJobModel, "job_spec_inv")
            assert j.status == "failed"
            assert "Requested specific player" in (j.error_summary or "")
        assert mock_engine.render_clip.call_count == 0

    @pytest.mark.asyncio
    async def test_batch_queue_order_and_execution(self, db_session_factory, tmp_path):
        """Batch of 3 jobs must be executed strictly in order one by one."""
        demo_file = tmp_path / "match.dem"
        demo_file.write_bytes(b"PBDEMS2\x00" + b"\x00" * 2000)

        with db_session_factory() as sess:
            demo = DemoModel(
                fingerprint="fp_batch",
                file_path=str(demo_file),
                map_name="de_dust2",
                tickrate=64,
                duration_seconds=120.0,
                schema_version="1",
            )
            sess.add(demo)
            sess.flush()

            for i in range(1, 4):
                sess.add(
                    RenderJobModel(
                        id=f"batch_job_{i}",
                        demo_id=demo.id,
                        highlight_id=None,
                        settings_json=json.dumps({"resolution": "1080p", "fps": 60}),
                        status="pending",
                        progress=0.0,
                    )
                )
            sess.commit()

        execution_order = []
        concurrency_levels = []
        active = 0

        mock_engine = MagicMock()
        def fake_render(task: RenderTask) -> RenderResult:
            nonlocal active
            active += 1
            concurrency_levels.append(active)
            execution_order.append(task.task_id)
            out_file = task.output_path
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.touch()
            active -= 1
            return RenderResult(success=True, output_path=out_file, duration_seconds=3.0)

        mock_engine.render_clip.side_effect = fake_render

        manager = RenderQueueManager(
            session_factory=db_session_factory,
            render_engine=mock_engine,
            output_dir=tmp_path,
        )
        manager.start()

        # Enqueue all 3 jobs
        await manager.enqueue("batch_job_1")
        await manager.enqueue("batch_job_2")
        await manager.enqueue("batch_job_3")

        for _ in range(60):
            await asyncio.sleep(0.05)
            with db_session_factory() as sess:
                j3 = sess.get(RenderJobModel, "batch_job_3")
                if j3 and j3.status == "completed":
                    break

        await manager.stop()

        # Check exact FIFO order
        assert execution_order == ["batch_job_1", "batch_job_2", "batch_job_3"]
        # Check strict concurrency <= 1
        assert max(concurrency_levels) == 1

        with db_session_factory() as sess:
            for i in range(1, 4):
                j = sess.get(RenderJobModel, f"batch_job_{i}")
                assert j.status == "completed"
                assert j.progress == 1.0

    @pytest.mark.asyncio
    async def test_batch_queue_partial_failure(self, db_session_factory, tmp_path):
        """Failure of one job in a batch does not stop remaining jobs from processing."""
        demo_file = tmp_path / "match.dem"
        demo_file.write_bytes(b"PBDEMS2\x00" + b"\x00" * 2000)

        with db_session_factory() as sess:
            demo = DemoModel(
                fingerprint="fp_part_fail",
                file_path=str(demo_file),
                map_name="de_dust2",
                tickrate=64,
                duration_seconds=120.0,
                schema_version="1",
            )
            sess.add(demo)
            sess.flush()

            sess.add_all([
                RenderJobModel(id="job_ok_1", demo_id=demo.id, status="pending", progress=0.0),
                RenderJobModel(id="job_bad_2", demo_id=demo.id, status="pending", progress=0.0),
                RenderJobModel(id="job_ok_3", demo_id=demo.id, status="pending", progress=0.0),
            ])
            sess.commit()

        mock_engine = MagicMock()
        def fake_render(task: RenderTask) -> RenderResult:
            if task.task_id == "job_bad_2":
                return RenderResult(success=False, output_path=None, duration_seconds=0.0, error_message="Visual verification failed")
            out_file = task.output_path
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.touch()
            return RenderResult(success=True, output_path=out_file, duration_seconds=3.0)

        mock_engine.render_clip.side_effect = fake_render

        manager = RenderQueueManager(
            session_factory=db_session_factory,
            render_engine=mock_engine,
            output_dir=tmp_path,
        )
        manager.start()

        await manager.enqueue("job_ok_1")
        await manager.enqueue("job_bad_2")
        await manager.enqueue("job_ok_3")

        for _ in range(60):
            await asyncio.sleep(0.05)
            with db_session_factory() as sess:
                j3 = sess.get(RenderJobModel, "job_ok_3")
                if j3 and j3.status == "completed":
                    break

        await manager.stop()

        with db_session_factory() as sess:
            j1 = sess.get(RenderJobModel, "job_ok_1")
            j2 = sess.get(RenderJobModel, "job_bad_2")
            j3 = sess.get(RenderJobModel, "job_ok_3")
            assert j1.status == "completed"
            assert j2.status == "failed"
            assert "Visual verification failed" in j2.error_summary
            assert j3.status == "completed"

    @pytest.mark.asyncio
    async def test_queue_retry_failed_job(self, db_session_factory, tmp_path):
        """Failed job can be retried and successfully processed on retry."""
        demo_file = tmp_path / "match.dem"
        demo_file.write_bytes(b"PBDEMS2\x00" + b"\x00" * 2000)

        with db_session_factory() as sess:
            demo = DemoModel(
                fingerprint="fp_retry",
                file_path=str(demo_file),
                map_name="de_dust2",
                tickrate=64,
                duration_seconds=120.0,
                schema_version="1",
            )
            sess.add(demo)
            sess.flush()

            job = RenderJobModel(id="job_to_retry", demo_id=demo.id, status="pending", progress=0.0)
            sess.add(job)
            sess.commit()

        call_count = 0
        mock_engine = MagicMock()
        def fake_render(task: RenderTask) -> RenderResult:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return RenderResult(success=False, output_path=None, duration_seconds=0.0, error_message="Temporary crash")
            out_file = task.output_path
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.touch()
            return RenderResult(success=True, output_path=out_file, duration_seconds=3.0)

        mock_engine.render_clip.side_effect = fake_render

        manager = RenderQueueManager(
            session_factory=db_session_factory,
            render_engine=mock_engine,
            output_dir=tmp_path,
        )
        manager.start()

        # First run fails
        await manager.enqueue("job_to_retry")
        for _ in range(50):
            await asyncio.sleep(0.05)
            with db_session_factory() as sess:
                j = sess.get(RenderJobModel, "job_to_retry")
                if j and j.status == "failed":
                    break

        with db_session_factory() as sess:
            j = sess.get(RenderJobModel, "job_to_retry")
            assert j.status == "failed"

            # Perform retry
            repo = DemoRepository(sess)
            retried = repo.retry_render_job("job_to_retry")
            assert retried is not None
            assert retried.status == "pending"

        # Re-enqueue
        await manager.enqueue("job_to_retry")
        for _ in range(50):
            await asyncio.sleep(0.05)
            with db_session_factory() as sess:
                j = sess.get(RenderJobModel, "job_to_retry")
                if j and j.status == "completed":
                    break

        await manager.stop()

        with db_session_factory() as sess:
            j = sess.get(RenderJobModel, "job_to_retry")
            assert j.status == "completed"
            assert j.progress == 1.0
            assert j.error_summary is None


class TestParseRenderResolution:
    def test_default_16_9(self):
        assert parse_render_resolution({}) == (1920, 1080)
        assert parse_render_resolution({"resolution": "1080p"}) == (1920, 1080)
        assert parse_render_resolution({"resolution": "720p"}) == (1280, 720)

    def test_4_3_default_is_1280x960(self):
        # When aspect_ratio is 4:3 and resolution is not set or default, defaults to 1280x960 (pro standard)
        assert parse_render_resolution({"aspect_ratio": "4:3"}) == (1280, 960)
        assert parse_render_resolution({"aspect_ratio": "4:3", "resolution": "4:3"}) == (1280, 960)
        assert parse_render_resolution({"aspect_ratio": "4:3", "resolution": "1280x960"}) == (1280, 960)

    def test_4_3_custom_resolutions(self):
        assert parse_render_resolution({"aspect_ratio": "4:3", "resolution": "1440x1080"}) == (1440, 1080)
        assert parse_render_resolution({"aspect_ratio": "4:3", "resolution": "1024x768"}) == (1024, 768)

    def test_parse_arbitrary_wxh(self):
        assert parse_render_resolution({"resolution": "1280x1024"}) == (1280, 1024)
        assert parse_render_resolution({"resolution": "2560x1440"}) == (2560, 1440)

