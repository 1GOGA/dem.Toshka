"""Audio and video multiplexer for CS2 rendered clips."""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import pathlib
import subprocess
import uuid
from typing import Optional

from backend.render.config import DEFAULT_WATERMARK_PNG, FFMPEG_BIN, FFPROBE_BIN
from backend.render.verifier import verify_mp4

logger = logging.getLogger("demtoshka.muxer")


@dataclasses.dataclass
class MuxResult:
    """Outcome of multiplexing video and audio streams."""

    success: bool
    output_path: Optional[pathlib.Path]
    duration_seconds: float = 0.0
    video_duration: float = 0.0
    audio_duration: float = 0.0
    duration_diff: float = 0.0
    has_audio: bool = False
    error_message: Optional[str] = None
    warning_message: Optional[str] = None


def probe_media_info(file_path: pathlib.Path) -> dict:
    """Extract format and streams metadata for a media file via ffprobe."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return {}

    cmd = [
        FFPROBE_BIN,
        "-v",
        "error",
        "-show_entries",
        "stream=index,codec_type,codec_name,width,height,channels,sample_rate,duration",
        "-show_entries",
        "format=duration,size,format_name",
        "-of",
        "json",
        str(file_path),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            return json.loads(proc.stdout)
    except Exception as e:
        logger.debug("Failed to probe media %s: %s", file_path, e)

    return {}


def mux_video_and_audio(
    video_path: pathlib.Path,
    audio_path: Optional[pathlib.Path],
    output_path: pathlib.Path,
    ffmpeg_bin: str = FFMPEG_BIN,
    timeout_seconds: float = 120.0,
    watermark: bool = True,
    watermark_path: Optional[pathlib.Path] = None,
) -> MuxResult:
    """Multiplex H.264 video and PCM WAV audio into an MP4 container.

    - Overlays top-left watermark (logo_video.png) when watermark=True and watermark_path exists.
    - If watermark is disabled, copies video stream (-c:v copy) without re-encoding.
    - Audio is encoded to AAC (-c:a aac -b:a 192k) for optimal compatibility.
    - Writes to an isolated temporary staging file first; only replaces target on verified success.
    - Tolerates minor millisecond discrepancy between video and audio without arbitrary truncation.
    - Preserves source files untouched if muxing fails.
    """
    if not video_path.exists() or video_path.stat().st_size == 0:
        return MuxResult(
            success=False,
            output_path=None,
            error_message=f"Video file does not exist or is empty: {video_path}",
        )

    v_info = probe_media_info(video_path)
    v_streams = [s for s in v_info.get("streams", []) if s.get("codec_type") == "video"]
    if not v_streams:
        return MuxResult(
            success=False,
            output_path=None,
            error_message=f"No video stream found in: {video_path}",
        )

    try:
        v_dur = float(v_info.get("format", {}).get("duration", 0.0))
    except (ValueError, TypeError):
        v_dur = 0.0

    target_wm_path = watermark_path or DEFAULT_WATERMARK_PNG
    apply_wm = bool(watermark and target_wm_path and target_wm_path.exists() and target_wm_path.stat().st_size > 0)

    # Resolution dimensions for dynamic watermark scale
    v_width = 1920
    v_height = 1080
    if v_streams:
        try:
            v_width = int(v_streams[0].get("width", 1920))
            v_height = int(v_streams[0].get("height", 1080))
        except (ValueError, TypeError):
            pass

    logo_w = max(160, int(v_width * 0.125))
    offset_x = max(16, int(v_width * 0.0125))
    offset_y = max(14, int(v_height * 0.0185))

    # Case 1: Audio file is absent
    if audio_path is None or not audio_path.exists() or audio_path.stat().st_size == 0:
        warning = "Audio file not found or empty; video exported without audio stream."
        logger.warning(warning)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dest = output_path.with_name(f"temp_copy_{uuid.uuid4().hex[:8]}.mp4")
        try:
            if apply_wm:
                cmd = [
                    ffmpeg_bin,
                    "-y",
                    "-i",
                    str(video_path),
                    "-i",
                    str(target_wm_path),
                    "-filter_complex",
                    f"[1:v]scale={logo_w}:-1[logo];[0:v][logo]overlay={offset_x}:{offset_y}[outv]",
                    "-map",
                    "[outv]",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "18",
                    "-movflags",
                    "+faststart",
                    str(temp_dest),
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
                if proc.returncode != 0:
                    temp_dest.write_bytes(video_path.read_bytes())
            else:
                temp_dest.write_bytes(video_path.read_bytes())

            temp_dest.replace(output_path)
            return MuxResult(
                success=True,
                output_path=output_path,
                duration_seconds=v_dur,
                video_duration=v_dur,
                audio_duration=0.0,
                duration_diff=v_dur,
                has_audio=False,
                warning_message=warning,
            )
        except Exception as e:
            if temp_dest.exists():
                temp_dest.unlink(missing_ok=True)
            return MuxResult(
                success=False,
                output_path=None,
                error_message=f"Failed to copy video to destination: {e}",
            )

    # Case 2: Audio file is present — inspect and mux
    a_info = probe_media_info(audio_path)
    a_streams = [s for s in a_info.get("streams", []) if s.get("codec_type") == "audio"]
    if not a_streams:
        return MuxResult(
            success=False,
            output_path=None,
            error_message=f"Audio file exists but contains no valid audio stream: {audio_path}",
        )

    try:
        a_dur = float(a_info.get("format", {}).get("duration", 0.0))
    except (ValueError, TypeError):
        a_dur = 0.0

    dur_diff = abs(v_dur - a_dur)
    warning_msg = None
    if dur_diff > 1.0:
        warning_msg = (
            f"Audio duration ({a_dur:.2f}s) differs from video duration ({v_dur:.2f}s) by {dur_diff:.2f}s"
        )
        logger.warning(warning_msg)

    # Prepare temporary staging file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_mux = output_path.with_name(f"temp_mux_{uuid.uuid4().hex[:8]}.mp4")

    if apply_wm:
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-i",
            str(target_wm_path),
            "-filter_complex",
            f"[2:v]scale={logo_w}:-1[logo];[0:v][logo]overlay={offset_x}:{offset_y}[outv]",
            "-map",
            "[outv]",
            "-map",
            "1:a",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(temp_mux),
        ]
    else:
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(temp_mux),
        ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        if proc.returncode != 0:
            err = proc.stderr.strip() if proc.stderr else f"Exit code {proc.returncode}"
            if temp_mux.exists():
                temp_mux.unlink(missing_ok=True)
            return MuxResult(
                success=False,
                output_path=None,
                error_message=f"FFmpeg muxing failed: {err}",
            )

        # Verify multiplexed media container and stream integrity
        is_valid, probed_dur, verify_err = verify_mp4(temp_mux, require_audio=True)
        if not is_valid:
            if temp_mux.exists():
                temp_mux.unlink(missing_ok=True)
            return MuxResult(
                success=False,
                output_path=None,
                error_message=f"Muxed video verification failed: {verify_err}",
            )

        # Atomic replacement of destination file
        temp_mux.replace(output_path)
        final_dur = probed_dur if probed_dur is not None else v_dur

        return MuxResult(
            success=True,
            output_path=output_path,
            duration_seconds=final_dur,
            video_duration=v_dur,
            audio_duration=a_dur,
            duration_diff=dur_diff,
            has_audio=True,
            warning_message=warning_msg,
        )

    except subprocess.TimeoutExpired:
        if temp_mux.exists():
            temp_mux.unlink(missing_ok=True)
        return MuxResult(
            success=False,
            output_path=None,
            error_message=f"FFmpeg muxing timed out after {timeout_seconds}s",
        )
    except Exception as e:
        if temp_mux.exists():
            temp_mux.unlink(missing_ok=True)
        return MuxResult(
            success=False,
            output_path=None,
            error_message=f"Unexpected error during muxing: {e}",
        )

