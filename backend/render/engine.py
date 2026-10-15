"""Orchestrator for CS2 demo playback and video capture via HLAE."""

from __future__ import annotations

import logging
import os
import pathlib
import shutil
import subprocess
import time
import uuid
from typing import Optional

logger = logging.getLogger("demtoshka.render_engine")

from backend.render.cfg_backup import ConfigBackupManager
from backend.render.cfg_generator import (
    BatchClipItem,
    generate_batch_render_cfg,
    generate_render_cfg,
)
from backend.render.config import (
    DEFAULT_CFG_DIR,
    DEFAULT_CS2_EXE,
    DEFAULT_CSGO_DIR,
    DEFAULT_HOOK_DLL,
    DEFAULT_HLAE_EXE,
    RENDER_OUTPUT_DIR,
)
from backend.render.models import RenderResult, RenderTask
from backend.render.montage import create_montage
from backend.render.muxer import mux_video_and_audio
from backend.render.verifier import (
    verify_media_integrity,
    verify_mp4,
    verify_mp4_audio_signal,
    verify_mp4_visual_content,
)


class RenderEngine:
    def __init__(
        self,
        cs2_exe: pathlib.Path = DEFAULT_CS2_EXE,
        csgo_dir: pathlib.Path = DEFAULT_CSGO_DIR,
        cfg_dir: pathlib.Path = DEFAULT_CFG_DIR,
        hlae_exe: pathlib.Path = DEFAULT_HLAE_EXE,
        hook_dll: pathlib.Path = DEFAULT_HOOK_DLL,
    ) -> None:
        self.cs2_exe = cs2_exe
        self.csgo_dir = csgo_dir
        self.cfg_dir = cfg_dir
        self.hlae_exe = hlae_exe
        self.hook_dll = hook_dll

    def _execute_cs2_pass(
        self,
        task: RenderTask,
        subtask_id: str,
        start_tick: int,
        end_tick: int,
        pov_steam_id: Optional[str],
        pov_name: Optional[str],
        output_mp4: pathlib.Path,
        camera_switches: Optional[list[tuple[int, Optional[str], Optional[str]]]] = None,
        log_file: Optional[pathlib.Path] = None,
    ) -> tuple[bool, Optional[str], bool, Optional[str]]:
        """Execute a single linear CS2/HLAE recording pass.

        Returns (success, error_message, has_audio, warning_message).
        """
        job_render_dir = RENDER_OUTPUT_DIR / f"job_{subtask_id}"
        if job_render_dir.exists():
            shutil.rmtree(job_render_dir, ignore_errors=True)
        job_render_dir.mkdir(parents=True, exist_ok=True)

        staged_demo = self.csgo_dir / f"temp_{subtask_id}.dem"
        cfg_path = self.cfg_dir / f"render_{subtask_id}.cfg"

        try:
            with ConfigBackupManager(csgo_cfg_dir=self.cfg_dir):
                shutil.copy2(task.demo_path, staged_demo)

                logger.info(
                    "Configuring linear render CFG for pass %s: ticks=[%s, %s], pov_name=%s, pov_steam_id=%s",
                    subtask_id,
                    start_tick,
                    end_tick,
                    pov_name,
                    pov_steam_id,
                )
                generate_render_cfg(
                    start_tick=start_tick,
                    end_tick=end_tick,
                    output_dir=job_render_dir,
                    fps=task.fps,
                    pov_steam_id=pov_steam_id,
                    pov_name=pov_name,
                    output_cfg_path=cfg_path,
                    xray=task.xray,
                    hud_mode=task.hud_mode,
                    hud_scale=getattr(task, "hud_scale", None),
                    overhead_mode=getattr(task, "overhead_mode", None),
                    killfeed_only=getattr(task, "killfeed_only", None),
                    teamcounter_mode=getattr(task, "teamcounter_mode", None),
                    custom_crosshair=task.custom_crosshair,
                    fov=task.fov,
                    viewmodel_fov=task.viewmodel_fov,
                    crosshair_preset=task.crosshair_preset,
                    crosshair_color=task.crosshair_color,
                    radar_mode=task.radar_mode,
                    camera_switches=camera_switches,
                    is_killcam_replay=False,
                )

                demo_rel_name = f"temp_{subtask_id}"
                w, h = task.resolution

                cs2_args = (
                    f"-steam -insecure +sv_lan 1 -console -condebug -novid -nojoy -high "
                    f"+fps_max 0 +mat_powersavingsmode 0 -sw -w {w} -h {h} -afxDisableSteamStorage "
                    f"+exec render_{subtask_id}.cfg +playdemo {demo_rel_name}"
                )

                hlae_cmd = [
                    str(self.hlae_exe.resolve()),
                    "-customLoader",
                    "-noGui",
                    "-autoStart",
                    "-hookDllPath",
                    str(self.hook_dll.resolve()),
                    "-programPath",
                    str(self.cs2_exe.resolve()),
                    "-cmdLine",
                    cs2_args,
                ]

                hlae_proc = subprocess.Popen(
                    hlae_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                tickrate = max(1, task.tickrate)
                pass_duration = max(1.0, (end_tick - start_tick) / tickrate)
                max_timeout = max(240.0, pass_duration * 6.0 + 180.0)
                start_time = time.time()
                cs2_seen = False

                while time.time() - start_time < max_timeout:
                    res = subprocess.run(
                        ["tasklist", "/FI", "IMAGENAME eq cs2.exe", "/FO", "CSV", "/NH"],
                        capture_output=True,
                        text=True,
                    )
                    cs2_running = "cs2.exe" in res.stdout

                    if cs2_running:
                        cs2_seen = True
                    elif cs2_seen:
                        break

                    time.sleep(2.0)

                # If timed out, kill CS2
                res = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq cs2.exe", "/FO", "CSV", "/NH"],
                    capture_output=True,
                    text=True,
                )
                if "cs2.exe" in res.stdout:
                    logger.warning("CS2 exceeded timeout (%.0fs), killing process...", max_timeout)
                    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], capture_output=True)

                hlae_out, hlae_err = "", ""
                try:
                    hlae_out, hlae_err = hlae_proc.communicate(timeout=5.0)
                except subprocess.TimeoutExpired:
                    hlae_proc.terminate()
                    hlae_out, hlae_err = hlae_proc.communicate()

                if log_file:
                    log_content = (
                        f"--- Pass {subtask_id} Render Log ---\n"
                        f"HLAE Command: {' '.join(hlae_cmd)}\n"
                        f"CS2 Args: {cs2_args}\n"
                        f"CS2 seen running: {cs2_seen}\n"
                        f"HLAE exit code: {hlae_proc.returncode}\n"
                        f"--- HLAE STDOUT ---\n{hlae_out}\n"
                        f"--- HLAE STDERR ---\n{hlae_err}\n"
                    )
                    try:
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(log_content + "\n")
                    except Exception as log_ex:
                        logger.warning("Could not append to task log file %s: %s", log_file, log_ex)

                # Ensure CS2 is terminated if it hung
                res = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq cs2.exe", "/FO", "CSV", "/NH"],
                    capture_output=True,
                    text=True,
                )
                if "cs2.exe" in res.stdout:
                    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], capture_output=True)
                    return False, f"CS2 process did not finish within timeout ({max_timeout:.0f}s)", False, None

                # Locate recorded video and audio files
                take_dirs = sorted(
                    [d for d in job_render_dir.iterdir() if d.is_dir() and d.name.lower().startswith("take")],
                    key=lambda d: d.name,
                )
                if not take_dirs:
                    take_dirs = sorted([d for d in job_render_dir.iterdir() if d.is_dir()], key=lambda d: d.name)

                mp4_candidates = list(job_render_dir.rglob("*.mp4"))
                if not mp4_candidates:
                    return False, "HLAE completed but no .mp4 video file was generated in output directory", False, None

                recorded_video = mp4_candidates[0]
                wav_candidates = list(job_render_dir.rglob("*.wav"))
                recorded_audio = wav_candidates[0] if wav_candidates else None

                output_mp4.parent.mkdir(parents=True, exist_ok=True)
                mux_res = mux_video_and_audio(
                    video_path=recorded_video,
                    audio_path=recorded_audio,
                    output_path=output_mp4,
                    watermark=getattr(task, "watermark", True),
                )
                if not mux_res.success:
                    return False, mux_res.error_message or "Multiplexing video and audio failed", False, None

                return True, None, mux_res.has_audio, mux_res.warning_message

        except Exception as ex:
            return False, f"Recording pass failed: {ex}", False, None
        finally:
            if staged_demo.exists():
                try:
                    staged_demo.unlink()
                except Exception:
                    pass
            if cfg_path.exists():
                try:
                    cfg_path.unlink()
                except Exception:
                    pass
            if job_render_dir.exists():
                try:
                    shutil.rmtree(job_render_dir, ignore_errors=True)
                except Exception:
                    pass

    def render_clip(self, task: RenderTask) -> RenderResult:
        """Execute end-to-end rendering for a single highlight clip using HLAE."""
        log_file = RENDER_OUTPUT_DIR / f"{task.task_id}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Validation
        if not self.cs2_exe.exists():
            return RenderResult(
                success=False,
                output_path=None,
                duration_seconds=0.0,
                error_message=f"CS2 executable not found at: {self.cs2_exe}",
                log_file=log_file,
            )

        if not self.hlae_exe.exists():
            return RenderResult(
                success=False,
                output_path=None,
                duration_seconds=0.0,
                error_message=f"HLAE executable not found at: {self.hlae_exe}. Please install HLAE to tools/hlae",
                log_file=log_file,
            )

        if not self.hook_dll.exists():
            return RenderResult(
                success=False,
                output_path=None,
                duration_seconds=0.0,
                error_message=f"AfxHookSource2.dll not found at: {self.hook_dll}",
                log_file=log_file,
            )

        if not task.demo_path.exists():
            return RenderResult(
                success=False,
                output_path=None,
                duration_seconds=0.0,
                error_message=f"Demo file not found at: {task.demo_path}",
                log_file=log_file,
            )

        # 2. Execution (Two-Pass Staging for Tournament Killcam vs Linear Pass for Standard)
        if task.is_killcam_replay:
            # TOURNAMENT KILLCAM REPLAY: Two-Pass Staging
            # Pass 1: Victim view (shows victim moving/holding and falling on camera)
            vic_subtask_id = f"{task.task_id}_vic"
            vic_out = RENDER_OUTPUT_DIR / f"temp_{task.task_id}_victim.mp4"
            v_start = task.killcam_victim_start_tick if task.killcam_victim_start_tick is not None else task.start_tick
            v_end = task.killcam_victim_end_tick if task.killcam_victim_end_tick is not None else task.end_tick

            logger.info(
                "Executing Pass 1 of Tournament Killcam (Victim POV: %s, ticks=[%s, %s])",
                task.killcam_victim_name,
                v_start,
                v_end,
            )
            ok1, err1, has_audio1, warn1 = self._execute_cs2_pass(
                task=task,
                subtask_id=vic_subtask_id,
                start_tick=v_start,
                end_tick=v_end,
                pov_steam_id=task.killcam_victim_steam_id,
                pov_name=task.killcam_victim_name,
                output_mp4=vic_out,
                camera_switches=None,
                log_file=log_file,
            )
            if not ok1:
                return RenderResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    error_message=f"Tournament killcam Pass 1 (Victim) failed: {err1}",
                    log_file=log_file,
                )

            # Pass 2: Hero view (rewind ~4.0s before kill to hero POV, plays until highlight end)
            hero_subtask_id = f"{task.task_id}_hero"
            hero_out = RENDER_OUTPUT_DIR / f"temp_{task.task_id}_hero.mp4"
            h_start = task.killcam_hero_start_tick if task.killcam_hero_start_tick is not None else task.start_tick

            logger.info(
                "Executing Pass 2 of Tournament Killcam (Hero POV: %s, ticks=[%s, %s])",
                task.pov_name,
                h_start,
                task.end_tick,
            )
            ok2, err2, has_audio2, warn2 = self._execute_cs2_pass(
                task=task,
                subtask_id=hero_subtask_id,
                start_tick=h_start,
                end_tick=task.end_tick,
                pov_steam_id=task.pov_steam_id,
                pov_name=task.pov_name,
                output_mp4=hero_out,
                camera_switches=task.camera_switches,
                log_file=log_file,
            )
            if not ok2:
                if vic_out.exists():
                    try:
                        vic_out.unlink()
                    except Exception:
                        pass
                return RenderResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    error_message=f"Tournament killcam Pass 2 (Hero) failed: {err2}",
                    log_file=log_file,
                )

            # Combine Pass 1 (Victim death) and Pass 2 (Hero play) into final output
            montage_res = create_montage(clip_paths=[vic_out, hero_out], output_path=task.output_path)
            if vic_out.exists():
                try:
                    vic_out.unlink()
                except Exception:
                    pass
            if hero_out.exists():
                try:
                    hero_out.unlink()
                except Exception:
                    pass

            if not montage_res.success:
                return RenderResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    error_message=montage_res.error_message or "Montage concat failed for killcam replay",
                    log_file=log_file,
                )

            mux_has_audio = has_audio1 or has_audio2
            warning_note = warn2 or warn1
        else:
            # Standard single-pass clip
            ok, err, mux_has_audio, warning_note = self._execute_cs2_pass(
                task=task,
                subtask_id=task.task_id,
                start_tick=task.start_tick,
                end_tick=task.end_tick,
                pov_steam_id=task.pov_steam_id,
                pov_name=task.pov_name,
                output_mp4=task.output_path,
                camera_switches=task.camera_switches,
                log_file=log_file,
            )
            if not ok:
                return RenderResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    error_message=err or "Single pass rendering failed",
                    log_file=log_file,
                )

        # 3. Verification: streams, duration, resolution, fps, codecs, integrity, visual brightness and audio signal
        is_valid, duration, err = verify_mp4(
            task.output_path,
            require_audio=mux_has_audio,
            expected_resolution=task.resolution,
            expected_fps=task.fps,
            expected_video_codec="h264",
            expected_audio_codec="aac" if mux_has_audio else "",
        )
        if not is_valid:
            return RenderResult(
                success=False,
                output_path=task.output_path,
                duration_seconds=duration or 0.0,
                error_message=f"Output verification failed: {err}",
                log_file=log_file,
                has_audio=mux_has_audio,
            )

        is_intact, int_err = verify_media_integrity(task.output_path)
        if not is_intact:
            return RenderResult(
                success=False,
                output_path=task.output_path,
                duration_seconds=duration or 0.0,
                error_message=f"Bitstream integrity check failed: {int_err}",
                log_file=log_file,
                has_audio=mux_has_audio,
            )

        is_visible, vis_err = verify_mp4_visual_content(task.output_path)
        if not is_visible:
            return RenderResult(
                success=False,
                output_path=task.output_path,
                duration_seconds=duration or 0.0,
                error_message=f"Visual verification failed: {vis_err}",
                log_file=log_file,
                has_audio=mux_has_audio,
            )

        if mux_has_audio:
            has_sig, max_db, mean_db, sig_msg = verify_mp4_audio_signal(task.output_path)
            if not has_sig and sig_msg:
                warning_note = (
                    f"{warning_note}; {sig_msg}" if warning_note else sig_msg
                )

        return RenderResult(
            success=True,
            output_path=task.output_path,
            duration_seconds=duration or task.duration_seconds,
            error_message=None,
            log_file=log_file,
            has_audio=mux_has_audio,
            warning_message=warning_note,
        )

    def render_batch(self, tasks: list[RenderTask]) -> list[RenderResult]:
        """Execute batch rendering for multiple highlight clips in ONE continuous CS2/HLAE process.

        Eliminates repeated game/map reloads, saving minutes per batch.
        Guarantees that CS2 runs under a single PID for the entire batch.
        """
        if not tasks:
            return []

        if len(tasks) == 1:
            return [self.render_clip(tasks[0])]

        if any(t.is_killcam_replay for t in tasks):
            logger.info(
                "Batch contains tournament killcam tasks; delegating sequentially to render_clip to ensure two-pass integrity."
            )
            return [self.render_clip(t) for t in tasks]

        # 1. Validation
        batch_id = uuid.uuid4().hex[:8]
        batch_log_file = RENDER_OUTPUT_DIR / f"batch_{batch_id}.log"
        batch_log_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.cs2_exe.exists():
            return [
                RenderResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    error_message=f"CS2 executable not found at: {self.cs2_exe}",
                    log_file=batch_log_file,
                )
                for _ in tasks
            ]

        if not self.hlae_exe.exists():
            return [
                RenderResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    error_message=f"HLAE executable not found at: {self.hlae_exe}",
                    log_file=batch_log_file,
                )
                for _ in tasks
            ]

        if not self.hook_dll.exists():
            return [
                RenderResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    error_message=f"AfxHookSource2.dll not found at: {self.hook_dll}",
                    log_file=batch_log_file,
                )
                for _ in tasks
            ]

        # Ensure all tasks share the same demo file
        first_demo = tasks[0].demo_path
        if not first_demo.exists():
            return [
                RenderResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    error_message=f"Demo file not found at: {first_demo}",
                    log_file=batch_log_file,
                )
                for _ in tasks
            ]

        # 2. Sort tasks chronologically by start_tick
        sorted_tasks = sorted(tasks, key=lambda t: t.start_tick)

        job_render_dir = RENDER_OUTPUT_DIR / f"batch_{batch_id}"
        if job_render_dir.exists():
            shutil.rmtree(job_render_dir, ignore_errors=True)
        job_render_dir.mkdir(parents=True, exist_ok=True)

        staged_demo = self.csgo_dir / f"temp_batch_{batch_id}.dem"
        cfg_path = self.cfg_dir / f"render_batch_{batch_id}.cfg"

        results_by_id: dict[str, RenderResult] = {}
        detected_cs2_pid: Optional[int] = None

        try:
            with ConfigBackupManager(csgo_cfg_dir=self.cfg_dir):
                shutil.copy2(first_demo, staged_demo)

                # 3. Build BatchClipItem specifications
                batch_clips = [
                    BatchClipItem(
                        clip_id=t.task_id,
                        start_tick=t.start_tick,
                        end_tick=t.end_tick,
                        pov_steam_id=t.pov_steam_id,
                        pov_name=t.pov_name,
                        xray=t.xray,
                        hud_mode=t.hud_mode,
                        custom_crosshair=t.custom_crosshair,
                        fov=t.fov,
                        viewmodel_fov=t.viewmodel_fov,
                        crosshair_preset=t.crosshair_preset,
                        crosshair_color=t.crosshair_color,
                        radar_mode=t.radar_mode,
                        hud_scale=getattr(t, "hud_scale", None),
                        camera_switches=t.camera_switches,
                        is_killcam_replay=t.is_killcam_replay,
                        killcam_victim_steam_id=t.killcam_victim_steam_id,
                        killcam_victim_name=t.killcam_victim_name,
                        killcam_victim_start_tick=t.killcam_victim_start_tick,
                        killcam_victim_end_tick=t.killcam_victim_end_tick,
                        killcam_hero_start_tick=t.killcam_hero_start_tick,
                    )
                    for t in sorted_tasks
                ]

                fps = sorted_tasks[0].fps
                w, h = sorted_tasks[0].resolution

                logger.info(
                    "Generating multi-clip continuous batch CFG for %d clips (batch_id=%s)",
                    len(batch_clips),
                    batch_id,
                )
                generate_batch_render_cfg(
                    clips=batch_clips,
                    output_dir=job_render_dir,
                    output_cfg_path=cfg_path,
                    fps=fps,
                )

                # 4. Launch ONE CS2 process via HLAE
                demo_rel_name = f"temp_batch_{batch_id}"
                cs2_args = (
                    f"-steam -insecure +sv_lan 1 -console -condebug -novid -nojoy -high "
                    f"+fps_max 0 +mat_powersavingsmode 0 -sw -w {w} -h {h} -afxDisableSteamStorage "
                    f"+exec render_batch_{batch_id}.cfg +playdemo {demo_rel_name}"
                )

                hlae_cmd = [
                    str(self.hlae_exe.resolve()),
                    "-customLoader",
                    "-noGui",
                    "-autoStart",
                    "-hookDllPath",
                    str(self.hook_dll.resolve()),
                    "-programPath",
                    str(self.cs2_exe.resolve()),
                    "-cmdLine",
                    cs2_args,
                ]

                hlae_proc = subprocess.Popen(
                    hlae_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                # 5. Monitor CS2 process execution until all clips finish
                total_duration = sum(t.duration_seconds for t in sorted_tasks)
                max_timeout = max(300.0, total_duration * 6.0 + 200.0)
                start_time = time.time()
                cs2_seen = False

                while time.time() - start_time < max_timeout:
                    res = subprocess.run(
                        ["tasklist", "/FI", "IMAGENAME eq cs2.exe", "/FO", "CSV", "/NH"],
                        capture_output=True,
                        text=True,
                    )
                    cs2_running = "cs2.exe" in res.stdout

                    if cs2_running:
                        cs2_seen = True
                        if detected_cs2_pid is None:
                            # Extract PID from CSV output
                            try:
                                lines = [ln.strip() for ln in res.stdout.strip().splitlines() if "cs2.exe" in ln]
                                if lines:
                                    parts = [p.strip('"') for p in lines[0].split(",")]
                                    if len(parts) >= 2 and parts[1].isdigit():
                                        detected_cs2_pid = int(parts[1])
                                        logger.info(
                                            "Batch CS2 single-process confirmed running under PID: %d",
                                            detected_cs2_pid,
                                        )
                            except Exception:
                                pass
                    elif cs2_seen:
                        # CS2 finished all clips and cleanly exited
                        break

                    time.sleep(2.0)

                # If timed out while CS2 is still running, kill CS2 first to release pipe handles
                res = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq cs2.exe", "/FO", "CSV", "/NH"],
                    capture_output=True,
                    text=True,
                )
                if "cs2.exe" in res.stdout:
                    logger.warning("CS2 exceeded timeout (%ds), killing process...", max_timeout)
                    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], capture_output=True)

                # Capture HLAE output
                hlae_out, hlae_err = "", ""
                try:
                    hlae_out, hlae_err = hlae_proc.communicate(timeout=5.0)
                except subprocess.TimeoutExpired:
                    hlae_proc.terminate()
                    hlae_out, hlae_err = hlae_proc.communicate()

                batch_log_content = (
                    f"--- Batch {batch_id} Render Log ---\n"
                    f"Clips count: {len(sorted_tasks)}\n"
                    f"CS2 Confirmed PID: {detected_cs2_pid}\n"
                    f"HLAE Command: {' '.join(hlae_cmd)}\n"
                    f"CS2 Args: {cs2_args}\n"
                    f"CS2 seen: {cs2_seen}\n"
                    f"HLAE exit code: {hlae_proc.returncode}\n"
                    f"--- HLAE STDOUT ---\n{hlae_out}\n"
                    f"--- HLAE STDERR ---\n{hlae_err}\n"
                )
                try:
                    batch_log_file.write_text(batch_log_content, encoding="utf-8")
                    for t in sorted_tasks:
                        t_log = RENDER_OUTPUT_DIR / f"{t.task_id}.log"
                        t_log.write_text(batch_log_content, encoding="utf-8")
                except Exception:
                    pass

                # Kill CS2 if timed out
                res = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq cs2.exe", "/FO", "CSV", "/NH"],
                    capture_output=True,
                    text=True,
                )
                if "cs2.exe" in res.stdout:
                    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], capture_output=True)

                # 6. Locate take directories produced sequentially by HLAE
                take_dirs = sorted(
                    [d for d in job_render_dir.iterdir() if d.is_dir() and d.name.lower().startswith("take")],
                    key=lambda d: d.name,
                )
                if not take_dirs:
                    take_dirs = sorted([d for d in job_render_dir.iterdir() if d.is_dir()], key=lambda d: d.name)

                logger.info(
                    "Batch session produced %d take directories for %d requested clips",
                    len(take_dirs),
                    len(sorted_tasks),
                )

                take_idx = 0
                for task in sorted_tasks:
                    task_log_file = RENDER_OUTPUT_DIR / f"{task.task_id}.log"

                    if take_idx >= len(take_dirs):
                        results_by_id[task.task_id] = RenderResult(
                            success=False,
                            output_path=None,
                            duration_seconds=0.0,
                            error_message="HLAE take directory not found for clip",
                            log_file=task_log_file,
                        )
                        take_idx += 1
                        continue

                    take_dir = take_dirs[take_idx]
                    take_idx += 1

                    mp4s = list(take_dir.rglob("*.mp4"))
                    wavs = list(take_dir.rglob("*.wav"))

                    if not mp4s:
                        results_by_id[task.task_id] = RenderResult(
                            success=False,
                            output_path=None,
                            duration_seconds=0.0,
                            error_message=f"No video file found in take directory {take_dir.name}",
                            log_file=task_log_file,
                        )
                        continue

                    rec_video = mp4s[0]
                    rec_audio = wavs[0] if wavs else None

                    mux_res = mux_video_and_audio(
                        video_path=rec_video,
                        audio_path=rec_audio,
                        output_path=task.output_path,
                        watermark=getattr(task, "watermark", True),
                    )
                    if not mux_res.success:
                        results_by_id[task.task_id] = RenderResult(
                            success=False,
                            output_path=None,
                            duration_seconds=0.0,
                            error_message=mux_res.error_message or "Muxing failed",
                            log_file=task_log_file,
                        )
                        continue

                    mux_has_audio = mux_res.has_audio

                    # 8. QC Verification
                    is_valid, duration, v_err = verify_mp4(
                        task.output_path,
                        require_audio=mux_has_audio,
                        expected_resolution=task.resolution,
                        expected_fps=task.fps,
                    )
                    if not is_valid:
                        results_by_id[task.task_id] = RenderResult(
                            success=False,
                            output_path=task.output_path,
                            duration_seconds=duration or 0.0,
                            error_message=f"Output verification failed: {v_err}",
                            log_file=task_log_file,
                            has_audio=mux_res.has_audio,
                        )
                        continue

                    is_intact, int_err = verify_media_integrity(task.output_path)
                    if not is_intact:
                        results_by_id[task.task_id] = RenderResult(
                            success=False,
                            output_path=task.output_path,
                            duration_seconds=duration or 0.0,
                            error_message=f"Bitstream integrity check failed: {int_err}",
                            log_file=task_log_file,
                            has_audio=mux_res.has_audio,
                        )
                        continue

                    is_vis, vis_err = verify_mp4_visual_content(task.output_path)
                    if not is_vis:
                        results_by_id[task.task_id] = RenderResult(
                            success=False,
                            output_path=task.output_path,
                            duration_seconds=duration or 0.0,
                            error_message=f"Visual verification failed: {vis_err}",
                            log_file=task_log_file,
                            has_audio=mux_res.has_audio,
                        )
                        continue

                    warn_msg = mux_res.warning_message
                    if mux_res.has_audio:
                        has_sig, _, _, sig_msg = verify_mp4_audio_signal(task.output_path)
                        if not has_sig and sig_msg:
                            warn_msg = f"{warn_msg}; {sig_msg}" if warn_msg else sig_msg

                    results_by_id[task.task_id] = RenderResult(
                        success=True,
                        output_path=task.output_path,
                        duration_seconds=duration or task.duration_seconds,
                        error_message=None,
                        log_file=task_log_file,
                        has_audio=mux_res.has_audio,
                        warning_message=warn_msg,
                    )

        except Exception as ex:
            logger.exception("Batch rendering session %s failed: %s", batch_id, ex)
            for task in sorted_tasks:
                if task.task_id not in results_by_id:
                    results_by_id[task.task_id] = RenderResult(
                        success=False,
                        output_path=None,
                        duration_seconds=0.0,
                        error_message=f"Batch execution failed: {ex}",
                        log_file=batch_log_file,
                    )
        finally:
            if staged_demo.exists():
                try:
                    staged_demo.unlink(missing_ok=True)
                except Exception:
                    pass
            if cfg_path.exists():
                try:
                    cfg_path.unlink(missing_ok=True)
                except Exception:
                    pass
            if job_render_dir.exists():
                try:
                    shutil.rmtree(job_render_dir, ignore_errors=True)
                except Exception:
                    pass

        # Return results in the original caller's task order
        return [
            results_by_id.get(
                t.task_id,
                RenderResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    error_message="Unknown batch error",
                ),
            )
            for t in tasks
        ]

