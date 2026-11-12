"""Cinematic Capture Engine for CS2 Demo Playback.

Coordinates HLAE AfxHookSource2 demo playback, campath injection, sequential takes,
clean audio/video multiplexing, and quality verification with NO watermark.
"""

from __future__ import annotations

import logging
import pathlib
import subprocess
import time
from typing import Any, Callable, Optional

from backend.cinematic.campath_generator import export_campath_xml
from backend.cinematic.models import CameraType, CinematicProductionPackage, CinematicShot
from backend.render.cfg_backup import ConfigBackupManager
from backend.render.config import (
    DEFAULT_CFG_DIR,
    DEFAULT_CS2_EXE,
    DEFAULT_CSGO_DIR,
    DEFAULT_HLAE_EXE,
    DEFAULT_HOOK_DLL,
    FFMPEG_BIN,
    RENDER_OUTPUT_DIR,
)
from backend.render.muxer import mux_video_and_audio
from backend.render.verifier import verify_mp4

logger = logging.getLogger("demtoshka.cinematic.capture")


class CinematicCaptureEngine:
    """Orchestrates cinematic CS2 recording passes using HLAE and mirv_campath."""

    def __init__(
        self,
        cs2_exe: pathlib.Path = DEFAULT_CS2_EXE,
        csgo_dir: pathlib.Path = DEFAULT_CSGO_DIR,
        hlae_exe: pathlib.Path = DEFAULT_HLAE_EXE,
        hook_dll: pathlib.Path = DEFAULT_HOOK_DLL,
        output_dir: pathlib.Path = RENDER_OUTPUT_DIR,
    ):
        self.cs2_exe = cs2_exe
        self.csgo_dir = csgo_dir
        self.hlae_exe = hlae_exe
        self.hook_dll = hook_dll
        self.output_dir = output_dir

    def generate_shot_cfg(
        self,
        shot: CinematicShot,
        demo_name: str,
        take_output_dir: pathlib.Path,
        campath_xml_path: Optional[pathlib.Path] = None,
        jump_lead_ticks: int = 24,
    ) -> str:
        """Generate CS2 CFG commands for an individual cinematic shot."""
        fps = shot.fps
        out_dir_str = str(take_output_dir.resolve()).replace("\\", "/")

        lines = [
            "// dem.Toshka Cinematic Studio — Shot Capture",
            "sv_cheats 1",
            "engine_no_focus_sleep 0",
            "snd_mute_losefocus 0",
            "volume 0.8",
            f"host_framerate {fps}",
            "fps_max 0",
            "fps_max_ui 0",
            "fps_max_tools 0",
            "mat_powersavingsmode 0",
            "engine_low_latency_sleep_after_client_tick 0",
            "mirv_cvar_unhide_all",
            "r_show_build_info 0",
            "cl_trueview_show_status 0",
            "demo_ui_mode 0",
            "cl_spec_show_bindings 0",
            "spec_autodirector 0",
            "safezonex 1.0",
            "safezoney 1.0",
            f'mirv_streams record name "{out_dir_str}"',
            f"mirv_streams record fps {fps}",
            "mirv_streams record screen enabled 1",
            "mirv_streams record screen settings afxFfmpegYuv420p",
            "mirv_cmd clear",
        ]

        # HUD control: clean cinematic master (cl_drawhud 0) by default
        if shot.hud_mode == "none":
            lines.append("cl_drawhud 0")
        elif shot.hud_mode == "killfeed_only":
            lines.extend(["cl_drawhud 1", "cl_draw_only_deathnotices 1"])
        else:
            lines.extend(["cl_drawhud 1", "cl_draw_only_deathnotices 0"])

        # X-Ray control
        if shot.xray:
            lines.append("spec_show_xray 1")
        else:
            lines.extend(["spec_show_xray 0", "mirv_fix selectedPlayerGlow 0"])

        # Initial seek jump
        jump_tick = max(10, shot.start_tick - jump_lead_ticks)
        if shot.start_tick > 60:
            lines.append(f'mirv_cmd addAtTick 5 "demo_gototick {jump_tick}; demo_resume"')
        else:
            lines.append('mirv_cmd addAtTick 5 "demo_resume"')

        # Camera setup at jump_tick + 15
        setup_cmds: list[str] = []
        if shot.campath and campath_xml_path:
            campath_str = str(campath_xml_path.resolve()).replace("\\", "/")
            setup_cmds.extend([
                "spec_mode 6",  # Free cam for campath
                f'mirv_campath load "{campath_str}"',
                "mirv_campath enabled 1",
                "mirv_fov default",
            ])
        elif shot.camera_type == CameraType.THIRD_PERSON_CHASE:
            setup_cmds.extend(["spec_mode 5"])
            if shot.pov_steam_id:
                try:
                    acc = int(shot.pov_steam_id) - 76561197960265728
                    if acc > 0:
                        setup_cmds.append(f"spec_lock_to_accountid {acc}")
                except Exception:
                    pass
        else:
            # First person / Victim POV
            setup_cmds.extend(["spec_mode 4"])
            if shot.pov_steam_id:
                try:
                    acc = int(shot.pov_steam_id) - 76561197960265728
                    if acc > 0:
                        setup_cmds.append(f"spec_lock_to_accountid {acc}")
                except Exception:
                    pass

        if setup_cmds:
            prep_tick = max(6, jump_tick + 15)
            lines.append(f'mirv_cmd addAtTick {prep_tick} "{"; ".join(setup_cmds)}"')

        # Record start at shot.start_tick
        rec_start_parts = [
            "cl_trueview_show_status 0",
            "demo_ui_mode 0",
            "mirv_streams record start",
        ]
        if shot.campath:
            rec_start_parts.append("mirv_campath enabled 1")
        lines.append(f'mirv_cmd addAtTick {shot.start_tick} "{"; ".join(rec_start_parts)}"')

        # Record end at shot.end_tick
        rec_end_parts = [
            "mirv_streams record end",
            "mirv_campath enabled 0",
            "mirv_campath clear",
            "quit",
        ]
        lines.append(f'mirv_cmd addAtTick {shot.end_tick} "{"; ".join(rec_end_parts)}"')
        lines.append("demo_resume\n")

        return "\n".join(lines)

    def capture_shot(
        self,
        shot: CinematicShot,
        demo_path: pathlib.Path,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        timeout_seconds: int = 180,
    ) -> pathlib.Path:
        """Capture a single cinematic shot and return path to verified MP4.
        
        Strictly produces clean master footage with NO watermark.
        """
        if not demo_path.is_file():
            raise FileNotFoundError(f"Demo file not found at {demo_path}")

        shot_dir = self.output_dir / "cinematic_takes" / shot.shot_id
        shot_dir.mkdir(parents=True, exist_ok=True)

        campath_file: Optional[pathlib.Path] = None
        if shot.campath:
            campath_file = shot_dir / f"campath_{shot.shot_id}.xml"
            export_campath_xml(shot.campath, campath_file)

        cfg_content = self.generate_shot_cfg(
            shot=shot,
            demo_name=demo_path.stem,
            take_output_dir=shot_dir,
            campath_xml_path=campath_file,
        )

        cfg_file = DEFAULT_CFG_DIR / f"cinematic_{shot.shot_id}.cfg"
        cfg_file.parent.mkdir(parents=True, exist_ok=True)
        cfg_file.write_text(cfg_content, encoding="utf-8")

        if progress_callback:
            progress_callback(0.1, f"Launching CS2 for shot {shot.shot_id}")

        cmd = [
            str(self.hlae_exe),
            "-customLoader",
            "-noGui",
            "-autoStart",
            "-hookDllPath",
            str(self.hook_dll),
            "-programPath",
            str(self.cs2_exe),
            "-cmdLine",
            f"-insecure -novid -windowed -w 1920 -h 1080 +playdemo \"{demo_path.resolve()}\" +exec \"cinematic_{shot.shot_id}.cfg\"",
        ]

        with ConfigBackupManager():
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.hlae_exe.parent),
            )
            try:
                proc.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                proc.kill()
                raise TimeoutError(f"CS2 playback timed out after {timeout_seconds}s")

        if progress_callback:
            progress_callback(0.7, "Multiplexing audio and video...")

        # Find HLAE take folder (take0000)
        take_dirs = sorted(shot_dir.glob("take*"))
        if not take_dirs:
            raise RuntimeError(f"HLAE finished but no take directory found in {shot_dir}")

        target_take = take_dirs[0]
        final_mp4 = shot_dir / (shot.output_filename or f"{shot.shot_id}.mp4")

        # Multiplex video.mp4 and audio.wav with NO WATERMARK
        v_path = target_take / "video.mp4"
        a_path = target_take / "audio.wav"
        mux_res = mux_video_and_audio(
            video_path=v_path,
            audio_path=a_path if a_path.exists() else None,
            output_path=final_mp4,
            watermark=False,  # STRICT: NO WATERMARK ON MASTER CAPTURES
        )
        if not mux_res.success:
            raise RuntimeError(f"Multiplexing failed for shot {shot.shot_id}: {mux_res.error_message}")

        # Quality Control verification
        verify_mp4(final_mp4, require_audio=True)
        shot.validation_status = "VERIFIED"

        if progress_callback:
            progress_callback(1.0, f"Shot {shot.shot_id} captured and verified.")

        return final_mp4
