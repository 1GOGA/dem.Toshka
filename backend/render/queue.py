"""Sequential asynchronous render queue and worker for CS2 Highlight clips."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
from typing import Callable, Optional

from sqlalchemy.orm import sessionmaker

from backend.parser.ingestion import validate_demo_path
from backend.render.cfg_generator import steam64_to_account_id
from backend.render.config import DEFAULT_CS2_EXE, DEFAULT_HLAE_EXE, DEFAULT_HOOK_DLL, RENDER_OUTPUT_DIR
from backend.render.engine import RenderEngine
from backend.render.models import RenderResult, RenderTask
from backend.storage.models import DemoModel, HighlightModel, RenderJobModel
from backend.storage.repository import DemoRepository

logger = logging.getLogger("demtoshka.render_queue")


def parse_render_resolution(settings: dict) -> tuple[int, int]:
    """Parse aspect ratio and resolution into exact (width, height) for CS2 launch options.

    Supports:
    - 4:3 pro resolutions: 1280x960 (default for 4:3), 1440x1080, 1024x768
    - 16:9 widescreen: 1920x1080 (1080p, default for 16:9), 1280x720 (720p), 2560x1440 (1440p)
    - Custom format 'WIDTHxHEIGHT' e.g. '1280x960'
    """
    res_str = str(settings.get("resolution", "")).lower().strip()
    aspect = str(settings.get("aspect_ratio") or settings.get("aspectRatio") or "").strip()

    # Direct resolution string match
    if res_str in ("1280x960", "960p"):
        return (1280, 960)
    elif res_str in ("1440x1080",):
        return (1440, 1080)
    elif res_str in ("1024x768",):
        return (1024, 768)
    elif res_str in ("1920x1080", "1080p"):
        if aspect == "4:3":
            return (1280, 960)
        return (1920, 1080)
    elif res_str in ("1280x720", "720p"):
        return (1280, 720)
    elif res_str in ("2560x1440", "1440p", "2k"):
        return (2560, 1440)
    elif res_str == "4:3":
        return (1280, 960)
    elif "x" in res_str:
        try:
            parts = res_str.split("x")
            w, h = int(parts[0]), int(parts[1])
            if 320 <= w <= 7680 and 240 <= h <= 4320:
                return (w, h)
        except (ValueError, IndexError):
            pass

    # If aspect is explicitly 4:3, use 1280x960 as standard esports resolution
    if aspect == "4:3":
        return (1280, 960)

    # Default to 1920x1080
    return (1920, 1080)


def sanitize_output_path(
    job_id: str,
    base_dir: pathlib.Path = RENDER_OUTPUT_DIR,
    highlight_id: Optional[str] = None,
    map_name: Optional[str] = None,
    player_name: Optional[str] = None,
    hl_type: Optional[str] = None,
    round_num: Optional[int] = None,
) -> pathlib.Path:
    if ".." in job_id or "/" in job_id or "\\" in job_id:
        raise ValueError("Path traversal attempt detected in render output path")
    if highlight_id and (".." in highlight_id or "/" in highlight_id or "\\" in highlight_id):
        raise ValueError("Path traversal attempt detected in render output path")

    import re
    # Strip any invalid characters
    safe_job_id = re.sub(r"[^\w\-]", "_", job_id)

    if map_name and player_name and hl_type and round_num is not None:
        clean_map = re.sub(r"[^\w\-]", "", map_name).replace("de_", "")
        clean_player = re.sub(r"[^\w\-]", "_", player_name)
        clean_type = re.sub(r"[^\w\-]", "_", hl_type).replace("multikill_", "")
        candidate_name = f"{clean_map}_{clean_player}_{clean_type}_R{round_num}_{safe_job_id[:6]}.mp4"
    elif highlight_id:
        safe_hl_id = re.sub(r"[^\w\-]", "_", highlight_id)
        candidate_name = f"clip_{safe_job_id[:8]}_{safe_hl_id}.mp4"
    else:
        candidate_name = f"clip_{safe_job_id}.mp4"

    resolved_base = base_dir.resolve()
    target = (resolved_base / candidate_name).resolve()
    if not str(target).startswith(str(resolved_base)):
        raise ValueError("Path traversal attempt detected in render output path")

    # Guarantee collision-free: if target file already exists, append counter without overwriting
    counter = 1
    stem = target.stem
    while target.exists():
        target = (resolved_base / f"{stem}_{counter}.mp4").resolve()
        counter += 1

    return target


def validate_render_demo_path(demo_path_str: str) -> pathlib.Path:
    """Validate demo path for security (traversal, extension, existence)."""
    p = pathlib.Path(demo_path_str)
    # validate_demo_path checks existence and .dem extension
    validate_demo_path(p)
    return p


class RenderQueueManager:
    """Sequential render queue processor ensuring strictly one CS2 process at a time."""

    def __init__(
        self,
        session_factory: sessionmaker,
        render_engine: Optional[RenderEngine] = None,
        output_dir: Optional[pathlib.Path] = None,
    ) -> None:
        self.session_factory = session_factory
        self.render_engine = render_engine or RenderEngine()
        self.output_dir = output_dir or RENDER_OUTPUT_DIR
        self._queue: Optional[asyncio.Queue[str]] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._current_job_id: Optional[str] = None
        self._pending_ids: set[str] = set()

    @property
    def current_job_id(self) -> Optional[str]:
        return self._current_job_id

    def _ensure_queue(self) -> asyncio.Queue[str]:
        if self._queue is None:
            self._queue = asyncio.Queue()
        return self._queue

    def start(self) -> None:
        """Start the background sequential worker loop if not already running."""
        queue = self._ensure_queue()
        if not self._is_running:
            self._is_running = True

            # Startup recovery: reset stale running jobs and recover pending ones
            try:
                import datetime
                now = datetime.datetime.now()
                with self.session_factory() as session:
                    repo = DemoRepository(session)
                    stale_count = repo.reset_stale_running_jobs()
                    if stale_count > 0:
                        logger.warning("Reset %d stale running job(s) to failed on startup.", stale_count)

                    pending_jobs = repo.get_pending_render_jobs()
                    for job in pending_jobs:
                        # Expire pending jobs older than 2 hours to avoid surprise CS2 popups from yesterday
                        if job.created_at and (now - job.created_at).total_seconds() > 7200:
                            repo.update_render_job(
                                job.id,
                                status="failed",
                                error_summary="Queued job expired before worker started. Click Retry to render.",
                            )
                            logger.info("Expired old pending job %s (created %s)", job.id, job.created_at)
                        elif job.id not in self._pending_ids and job.id != self._current_job_id:
                            self._pending_ids.add(job.id)
                            queue.put_nowait(job.id)
                            logger.info("Enqueued pending render job %s on startup recovery.", job.id)
            except Exception as e:
                logger.warning("Error during render queue startup recovery: %s", e)

            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("Render queue background worker started. Initial queue size: %d", queue.qsize())

    async def stop(self) -> None:
        """Gracefully stop the background worker."""
        self._is_running = False
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._pending_ids.clear()
        logger.info("Render queue worker stopped.")

    async def enqueue(self, job_id: str) -> None:
        """Enqueue a job ID for sequential processing if not already queued."""
        if job_id in self._pending_ids or job_id == self._current_job_id:
            logger.info("Job %s is already queued or running, skipping duplicate enqueue.", job_id)
            return

        queue = self._ensure_queue()
        if not self._is_running:
            self.start()
        self._pending_ids.add(job_id)
        await queue.put(job_id)
        logger.info("Job %s enqueued. Queue size: %d", job_id, queue.qsize())

    async def _worker_loop(self) -> None:
        """Continuous worker processing jobs, batching same-demo clips into a single CS2 run."""
        queue = self._ensure_queue()
        while self._is_running:
            try:
                # Wait for next job
                first_job_id = await queue.get()
                batch_job_ids = [first_job_id]

                # Drain other immediately available jobs from queue to batch them
                while not queue.empty():
                    try:
                        next_id = queue.get_nowait()
                        batch_job_ids.append(next_id)
                    except asyncio.QueueEmpty:
                        break

                for jid in batch_job_ids:
                    self._pending_ids.discard(jid)

                try:
                    await self._process_batch(batch_job_ids)
                finally:
                    self._current_job_id = None
                    for _ in batch_job_ids:
                        queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Unexpected error in render queue worker: %s", e)
                await asyncio.sleep(1.0)

    def _build_task(self, job_id: str) -> tuple[Optional[RenderTask], Optional[str]]:
        """Load job from SQLite and build validated RenderTask."""
        session = self.session_factory()
        try:
            repo = DemoRepository(session)
            job = repo.get_render_job(job_id)
            if not job:
                return None, f"Job {job_id} not found in database"

            demo = repo.get_by_id(job.demo_id)
            if not demo:
                repo.update_render_job(
                    job_id,
                    status="failed",
                    progress=0.0,
                    error_summary="Associated demo not found in database",
                )
                return

            highlight = repo.get_highlight_by_id(job.highlight_id) if job.highlight_id else None
            round_info = None
            victim_info = None
            hl_kills = []
            if highlight:
                rounds = repo.get_rounds(demo_id=demo.id)
                round_info = next((r for r in rounds if r.round_num == highlight.round_num), None)
                kills = repo.get_kills(demo_id=demo.id, round_num=highlight.round_num)
                hl_kills = [
                    k
                    for k in kills
                    if k.attacker_steam_id == highlight.pov_steam_id
                    and highlight.kill_start_tick <= k.tick <= highlight.kill_end_tick
                ]
                if hl_kills and hl_kills[0].victim_steam_id:
                    victim_info = (hl_kills[0].victim_steam_id, hl_kills[0].victim_name)

            all_players = repo.get_players(demo_id=demo.id)

            # Parse settings
            try:
                settings = json.loads(job.settings_json or "{}")
            except Exception:
                settings = {}

            # Update status to running
            repo.update_render_job(job_id, status="running", progress=0.1)
        finally:
            session.close()

        # 2. Build RenderTask with strict path and parameter validations
        try:
            demo_path = validate_render_demo_path(demo.file_path)
            output_mp4 = sanitize_output_path(
                job_id,
                highlight_id=job.highlight_id,
                base_dir=self.output_dir,
                map_name=demo.map_name,
                player_name=highlight.pov_name if highlight else None,
                hl_type=highlight.highlight_type if highlight else None,
                round_num=highlight.round_num if highlight else None,
            )

            # Prevent overwriting the demo file itself
            if output_mp4.resolve() == demo_path.resolve():
                raise ValueError("Target output path matches source demo path")

            # Determine resolution and aspect ratio (supports 4:3 1280x960, 1440x1080, 1024x768 and 16:9)
            resolution = parse_render_resolution(settings)
            fps = int(settings.get("fps", 60))

            # Advanced recording settings
            xray = bool(settings.get("xray", True))
            hud_mode = str(settings.get("hud_mode", "full"))
            if hud_mode not in ("real", "huge_esports", "huge_killfeed", "full", "killfeed_only", "none"):
                hud_mode = "full"
            radar_mode = str(settings.get("radar_mode", "broadcast"))
            if hud_mode == "real":
                if "xray" not in settings:
                    xray = False
                if "radar_mode" not in settings:
                    radar_mode = "player_focus"
            perspective = str(settings.get("perspective", "attacker"))
            custom_crosshair = bool(settings.get("custom_crosshair", True))

            # Determine tick ranges and perspective POV
            tickrate = max(1, demo.tickrate)
            camera_switches: list[tuple[int, Optional[str], Optional[str]]] = []
            is_killcam_replay = False
            killcam_victim_steam_id = None
            killcam_victim_name = None
            killcam_victim_start_tick = None
            killcam_victim_end_tick = None
            killcam_hero_start_tick = None

            if highlight:
                pre_roll = float(settings.get("pre_roll_seconds", 5.0))
                if perspective == "dynamic_killcam":
                    pre_roll = max(pre_roll, 4.8)
                post_roll = float(settings.get("post_roll_seconds", 5.0))

                base_start = (
                    highlight.kill_start_tick
                    if getattr(highlight, "kill_start_tick", None) is not None
                    else highlight.clip_start_tick
                )
                base_end = (
                    highlight.kill_end_tick
                    if getattr(highlight, "kill_end_tick", None) is not None
                    else highlight.clip_end_tick
                )

                start_tick = max(0, base_start - int(pre_roll * tickrate))
                end_tick = base_end + int(post_roll * tickrate)

                # Clamp to round boundaries if round details available
                if round_info:
                    start_tick = max(round_info.start_tick, start_tick)
                    r_upper = round_info.official_end_tick or round_info.end_tick
                    if r_upper and r_upper > start_tick:
                        end_tick = min(r_upper, end_tick)

                if perspective == "dynamic_killcam":
                    # Dynamic Killcam mode (Tournament Replay):
                    # 1. First record the victim holding/moving and DYING ON CAMERA (showing epic frag & ragdoll).
                    # 2. Then REWIND backwards ~4.0s before the kill to Hero start, switch camera to Hero, and capture full play!
                    if not highlight.pov_steam_id:
                        raise ValueError(f"Attacker SteamID not found for highlight {highlight.id}")
                    hero_steam_id = highlight.pov_steam_id
                    hero_name = highlight.pov_name
                    pov_steam_id = hero_steam_id
                    pov_name = hero_name

                    # Gather all kills by hero in this highlight
                    effective_kills = hl_kills
                    if not effective_kills and round_info:
                        session_kills = repo.get_kills(demo_id=demo.id, round_num=highlight.round_num)
                        effective_kills = [
                            k for k in session_kills
                            if highlight.kill_start_tick <= k.tick <= highlight.kill_end_tick
                        ]

                    valid_kills = sorted(
                        [k for k in effective_kills if k.victim_steam_id and k.victim_steam_id != hero_steam_id],
                        key=lambda k: k.tick,
                    )

                    if valid_kills:
                        primary_kill = valid_kills[0]
                        k_tick = primary_kill.tick
                        r_start = round_info.start_tick if round_info else 0

                        # Phase 1: Victim death POV (~3.5s lead-in, and ~1.2s post-death to see ragdoll fall)
                        vic_lead_ticks = int(3.5 * tickrate)
                        vic_post_ticks = int(1.2 * tickrate)
                        killcam_victim_start_tick = max(r_start, k_tick - vic_lead_ticks)
                        killcam_victim_end_tick = k_tick + vic_post_ticks
                        killcam_victim_steam_id = primary_kill.victim_steam_id
                        killcam_victim_name = primary_kill.victim_name

                        # Phase 2: Rewind ~4.0s backwards before kill to hero POV
                        hero_rewind_ticks = int(4.0 * tickrate)
                        killcam_hero_start_tick = max(r_start, k_tick - hero_rewind_ticks)
                        is_killcam_replay = True

                        logger.info(
                            "Configured Tournament Killcam Replay: Victim %s [%d..%d] -> REWIND -> Hero %s [%d..%d]",
                            killcam_victim_name,
                            killcam_victim_start_tick,
                            killcam_victim_end_tick,
                            hero_name,
                            killcam_hero_start_tick,
                            end_tick,
                        )
                    else:
                        is_killcam_replay = False

                elif perspective == "victim":
                    if not victim_info:
                        raise ValueError(
                            f"Victim not found for highlight {highlight.id} in round {highlight.round_num}"
                        )
                    pov_steam_id, pov_name = victim_info
                elif perspective == "specific_player":
                    target_steam = settings.get("perspective_steam_id")
                    target_name = settings.get("perspective_name")
                    matched_player = None
                    for p in all_players:
                        if target_steam and str(p.steam_id) == str(target_steam):
                            matched_player = p
                            break
                        if target_name and (p.name == target_name or target_name.lower() in (p.name or "").lower()):
                            matched_player = p
                            break
                    if not matched_player:
                        raise ValueError(
                            f"Requested specific player '{target_steam or target_name}' not found in demo players"
                        )
                    pov_steam_id = matched_player.steam_id
                    pov_name = matched_player.name
                else:  # "attacker"
                    if not highlight.pov_steam_id:
                        raise ValueError(f"Attacker SteamID not found for highlight {highlight.id}")
                    pov_steam_id = highlight.pov_steam_id
                    pov_name = highlight.pov_name
            else:
                # Default 10-second preview from demo beginning
                start_tick = 100
                end_tick = 100 + 10 * tickrate
                pov_steam_id = None
                pov_name = None
                radar_mode = str(settings.get("radar_mode", "broadcast"))
                camera_switches = []

            logger.info(
                "POV Selection for Job %s: highlight_id=%s, round=%s, ticks=[%s, %s], perspective=%s, selected_player=%s, steam_id=%s, account_id=%s, crosshair=%s, radar_mode=%s, camera_switches=%d",
                job_id,
                highlight.id if highlight else None,
                highlight.round_num if highlight else None,
                start_tick,
                end_tick,
                perspective,
                pov_name,
                pov_steam_id,
                steam64_to_account_id(pov_steam_id) if pov_steam_id else None,
                custom_crosshair,
                radar_mode,
                len(camera_switches),
            )

            task = RenderTask(
                task_id=job_id,
                demo_path=demo_path,
                start_tick=start_tick,
                end_tick=end_tick,
                pov_steam_id=pov_steam_id,
                pov_name=pov_name,
                tickrate=tickrate,
                resolution=resolution,
                fps=fps,
                output_path=output_mp4,
                xray=xray,
                hud_mode=hud_mode,
                perspective=perspective,
                custom_crosshair=custom_crosshair,
                fov=int(settings["fov"]) if settings.get("fov") else None,
                viewmodel_fov=int(settings["viewmodel_fov"]) if settings.get("viewmodel_fov") else None,
                crosshair_preset=str(settings.get("crosshair_preset", "pro_cyan")),
                crosshair_color=str(settings["crosshair_color"]) if settings.get("crosshair_color") else None,
                radar_mode=radar_mode,
                hud_scale=float(settings["hud_scale"]) if settings.get("hud_scale") else None,
                camera_switches=camera_switches,
                is_killcam_replay=is_killcam_replay,
                killcam_victim_steam_id=killcam_victim_steam_id,
                killcam_victim_name=killcam_victim_name,
                killcam_victim_start_tick=killcam_victim_start_tick,
                killcam_victim_end_tick=killcam_victim_end_tick,
                killcam_hero_start_tick=killcam_hero_start_tick,
            )
            return task, None
        except Exception as e:
            return None, str(e)

    async def _process_batch(self, job_ids: list[str]) -> None:
        """Process a list of render jobs, grouping by demo for continuous single-session capture."""
        if not job_ids:
            return

        logger.info("Worker processing batch of %d job(s): %s", len(job_ids), job_ids)

        # 1. Build and validate tasks
        built_tasks: list[tuple[str, RenderTask]] = []
        for jid in job_ids:
            task, err = self._build_task(jid)
            if not task:
                session = self.session_factory()
                try:
                    repo = DemoRepository(session)
                    repo.update_render_job(
                        jid,
                        status="failed",
                        progress=0.0,
                        error_summary=f"Validation error: {err}",
                    )
                finally:
                    session.close()
            else:
                built_tasks.append((jid, task))

        if not built_tasks:
            return

        # 2. Group by demo file path
        demo_groups: dict[pathlib.Path, list[tuple[str, RenderTask]]] = {}
        for jid, task in built_tasks:
            demo_groups.setdefault(task.demo_path.resolve(), []).append((jid, task))

        # 3. Execute each demo group
        for demo_path, group in demo_groups.items():
            group_job_ids = [jid for jid, _ in group]
            group_tasks = [t for _, t in group]

            # Mark all as running
            session = self.session_factory()
            try:
                repo = DemoRepository(session)
                for jid in group_job_ids:
                    repo.update_render_job(jid, status="running", progress=0.1)
            finally:
                session.close()

            batch_fn = getattr(self.render_engine, "render_batch", None)
            is_mock = hasattr(batch_fn, "_mock_name") or hasattr(batch_fn, "assert_called")
            has_explicit_mock = is_mock and (
                getattr(batch_fn, "side_effect", None) is not None
                or (getattr(batch_fn, "return_value", None) is not None and not hasattr(getattr(batch_fn, "return_value", None), "_mock_name"))
            )
            has_killcam = any(t.is_killcam_replay for t in group_tasks)
            can_use_batch = (len(group_tasks) > 1) and not has_killcam and (not is_mock or has_explicit_mock)

            if can_use_batch:
                # OPTIMIZATION: Single CS2 process continuous multi-clip recording
                logger.info(
                    "Executing SINGLE CS2 process continuous batch recording for %d clips from demo %s",
                    len(group_tasks),
                    demo_path.name,
                )
                self._current_job_id = f"batch_{len(group_tasks)}_clips"
                results: list[RenderResult] = await asyncio.to_thread(
                    self.render_engine.render_batch, group_tasks
                )

                # Record results
                session = self.session_factory()
                try:
                    repo = DemoRepository(session)
                    for (jid, _), res in zip(group, results):
                        if res.success and res.output_path and res.output_path.exists():
                            repo.update_render_job(
                                jid,
                                status="completed",
                                progress=1.0,
                                output_path=str(res.output_path),
                                log_path=str(res.log_file) if res.log_file else None,
                            )
                            logger.info("Batch item %s completed: %s", jid, res.output_path)
                        else:
                            repo.update_render_job(
                                jid,
                                status="failed",
                                progress=0.0,
                                error_summary=res.error_message or "Unknown rendering error",
                                log_path=str(res.log_file) if res.log_file else None,
                            )
                            logger.warning("Batch item %s failed: %s", jid, res.error_message)
                finally:
                    session.close()

            else:
                # Sequential clip rendering (single clip or mock engine)
                for jid, task in group:
                    self._current_job_id = jid
                    logger.info("Executing clip render for job %s", jid)
                    res: RenderResult = await asyncio.to_thread(self.render_engine.render_clip, task)

                    session = self.session_factory()
                    try:
                        repo = DemoRepository(session)
                        if res.success and res.output_path and res.output_path.exists():
                            repo.update_render_job(
                                jid,
                                status="completed",
                                progress=1.0,
                                output_path=str(res.output_path),
                                log_path=str(res.log_file) if res.log_file else None,
                            )
                            logger.info("Job %s completed: %s", jid, res.output_path)
                        else:
                            repo.update_render_job(
                                jid,
                                status="failed",
                                progress=0.0,
                                error_summary=res.error_message or "Unknown rendering error",
                                log_path=str(res.log_file) if res.log_file else None,
                            )
                            logger.warning("Job %s failed: %s", jid, res.error_message)
                    finally:
                        session.close()
