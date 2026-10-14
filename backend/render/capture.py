"""Video capture engine utilizing FFmpeg gdigrab on Windows."""

from __future__ import annotations

import pathlib
import subprocess
import time
from typing import Optional

from backend.render.config import FFMPEG_BIN


def capture_window_ffmpeg(
    output_mp4: pathlib.Path,
    duration_seconds: float,
    window_title: str = "Counter-Strike 2",
    fps: int = 60,
    log_file: Optional[pathlib.Path] = None,
) -> tuple[bool, Optional[str]]:
    """Capture a specific window using FFmpeg's gdigrab frame grabber.

    Returns (success, error_message).
    """
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        FFMPEG_BIN,
        "-y",
        "-f",
        "gdigrab",
        "-framerate",
        str(fps),
        "-i",
        f"title={window_title}",
        "-t",
        f"{duration_seconds:.2f}",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        str(output_mp4),
    ]

    log_fp = None
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_fp = open(log_file, "w", encoding="utf-8")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=log_fp or subprocess.PIPE,
            stderr=log_fp or subprocess.PIPE,
            text=True,
        )

        timeout = duration_seconds + 15.0
        try:
            _, stderr = proc.communicate(timeout=timeout)
            if proc.returncode != 0:
                err_msg = stderr.strip() if stderr else f"FFmpeg exited with code {proc.returncode}"
                return False, f"FFmpeg capture failed: {err_msg}"
            return True, None
        except subprocess.TimeoutExpired:
            proc.kill()
            return False, f"FFmpeg capture timed out after {timeout:.1f}s"

    except Exception as e:
        return False, f"Failed to start FFmpeg process: {e}"
    finally:
        if log_fp:
            log_fp.close()

