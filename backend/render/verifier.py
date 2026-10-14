"""Video output verification using FFprobe and visual luminance checks."""

from __future__ import annotations

import json
import pathlib
import subprocess
from typing import Optional

from backend.render.config import FFMPEG_BIN, FFPROBE_BIN


import os
import re


def verify_mp4(
    file_path: pathlib.Path,
    min_duration_seconds: float = 0.5,
    require_audio: bool = False,
    expected_resolution: Optional[tuple[int, int]] = None,
    expected_fps: Optional[int] = None,
    expected_video_codec: str = "h264",
    expected_audio_codec: str = "aac",
) -> tuple[bool, Optional[float], Optional[str]]:
    """Verify that an MP4 file exists, is non-empty, and has valid media streams.

    Args:
        file_path: Path to the MP4 file.
        min_duration_seconds: Minimum duration threshold.
        require_audio: If True, requires a valid audio stream (e.g. AAC) in container.
        expected_resolution: Optional (width, height) to match.
        expected_fps: Optional frame rate to match.
        expected_video_codec: Expected video codec name (default 'h264').
        expected_audio_codec: Expected audio codec name (default 'aac').

    Returns: (is_valid, actual_duration, error_message)
    """
    if not file_path.exists():
        return False, None, f"Output file does not exist: {file_path}"

    if file_path.stat().st_size == 0:
        return False, None, f"Output file is empty (0 bytes): {file_path}"

    cmd = [
        FFPROBE_BIN,
        "-v",
        "error",
        "-show_entries",
        "stream=index,codec_type,codec_name,width,height,channels,sample_rate,duration,r_frame_rate",
        "-show_entries",
        "format=format_name,duration,size",
        "-of",
        "json",
        str(file_path),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            return False, None, f"ffprobe failed with exit code {proc.returncode}: {proc.stderr.strip()}"

        data = json.loads(proc.stdout)
        format_info = data.get("format", {})
        duration_str = format_info.get("duration")
        if not duration_str:
            return False, None, "ffprobe could not determine file duration"

        duration = float(duration_str)
        if duration < min_duration_seconds:
            return False, duration, f"Clip duration {duration:.2f}s is shorter than minimum {min_duration_seconds:.2f}s"

        streams = data.get("streams", [])
        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

        if not video_streams:
            return False, duration, "File contains no valid video stream"

        v_stream = video_streams[0]
        v_codec = v_stream.get("codec_name", "").lower()
        if expected_video_codec and v_codec != expected_video_codec.lower():
            return False, duration, f"Unexpected video codec '{v_codec}', expected '{expected_video_codec}'"

        width = v_stream.get("width")
        height = v_stream.get("height")
        if not width or not height or width <= 0 or height <= 0:
            return False, duration, f"Invalid video dimensions: {width}x{height}"

        if expected_resolution:
            exp_w, exp_h = expected_resolution
            if (width, height) != (exp_w, exp_h):
                return False, duration, f"Video resolution {width}x{height} does not match expected {exp_w}x{exp_h}"

        if expected_fps:
            r_fps_str = v_stream.get("r_frame_rate", "")
            if "/" in r_fps_str:
                num, den = r_fps_str.split("/")
                fps_val = float(num) / float(den) if float(den) != 0 else 0.0
                if abs(fps_val - expected_fps) > 2.0:
                    return False, duration, f"Video frame rate {fps_val:.1f} fps does not match expected {expected_fps} fps"

        if require_audio:
            if not audio_streams:
                return False, duration, "File contains no audio stream (audio track is missing)"
            a_stream = audio_streams[0]
            a_codec = a_stream.get("codec_name", "").lower()
            if expected_audio_codec and a_codec != expected_audio_codec.lower():
                return False, duration, f"Unexpected audio codec '{a_codec}', expected '{expected_audio_codec}'"
            if a_stream.get("channels", 0) < 1:
                return False, duration, "Audio stream has invalid channel count (0 channels)"

            sample_rate = a_stream.get("sample_rate")
            if sample_rate and int(sample_rate) < 22050:
                return False, duration, f"Audio sample rate {sample_rate} Hz is unexpectedly low"

        return True, duration, None

    except subprocess.TimeoutExpired:
        return False, None, "ffprobe timed out verifying media"
    except Exception as e:
        return False, None, f"Failed to probe media: {e}"


def verify_media_integrity(file_path: pathlib.Path, timeout: float = 60.0) -> tuple[bool, Optional[str]]:
    """Decode file packets through FFmpeg null sink to verify bitstream integrity and catch corrupted frames."""
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"

    null_sink = "NUL" if os.name == "nt" else "/dev/null"
    cmd = [
        FFMPEG_BIN,
        "-v",
        "error",
        "-xerror",
        "-i",
        str(file_path),
        "-f",
        "null",
        null_sink,
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            err = proc.stderr.strip() or f"FFmpeg integrity check exited with code {proc.returncode}"
            return False, f"Media bitstream error detected: {err}"
        return True, None
    except subprocess.TimeoutExpired:
        return False, f"FFmpeg media integrity check timed out ({timeout}s)"
    except Exception as e:
        return False, f"Media integrity check failed: {e}"


def verify_mp4_audio_signal(
    file_path: pathlib.Path,
    max_silence_db: float = -80.0,
    mean_silence_db: float = -75.0,
) -> tuple[bool, Optional[float], Optional[float], Optional[str]]:
    """Analyze audio stream loudness via FFmpeg volumedetect.

    Checks:
    - Peak volume (max_volume) is above silence floor.
    - Mean volume is within realistic audible range.
    - Audio stream is decodable without bitstream failures.

    Returns:
        (has_signal, max_volume_db, mean_volume_db, warning_or_error)
        has_signal is True if non-zero audio content is detected.
    """
    if not file_path.exists():
        return False, None, None, f"File does not exist: {file_path}"

    null_sink = "NUL" if os.name == "nt" else "/dev/null"
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i",
        str(file_path),
        "-vn",
        "-af",
        "volumedetect",
        "-f",
        "null",
        null_sink,
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        stderr = proc.stderr or ""

        max_match = re.search(r"max_volume:\s*([-0-9.]+|-inf)\s*dB", stderr)
        mean_match = re.search(r"mean_volume:\s*([-0-9.]+|-inf)\s*dB", stderr)

        if not max_match:
            return False, None, None, "No audio signal detected or stream could not be decoded"

        max_val_str = max_match.group(1).strip()
        mean_val_str = mean_match.group(1).strip() if mean_match else None

        if "-inf" in max_val_str:
            max_db = -999.0
            has_signal = False
        else:
            max_db = float(max_val_str)
            has_signal = max_db > max_silence_db

        mean_db = float(mean_val_str) if mean_val_str and "-inf" not in mean_val_str else None

        if not has_signal:
            msg = f"Audio stream is digital silence (max volume {max_db:.1f} dB)"
        elif mean_db is not None and mean_db < mean_silence_db:
            msg = f"Audio stream has low average energy (mean: {mean_db:.1f} dB, peak: {max_db:.1f} dB)"
        else:
            msg = None

        return has_signal, max_db, mean_db, msg

    except subprocess.TimeoutExpired:
        return False, None, None, "FFmpeg volumedetect timed out"
    except Exception as e:
        return False, None, None, f"Audio signal check failed: {e}"



def verify_mp4_visual_content(
    file_path: pathlib.Path,
    sample_seconds: Optional[list[float]] = None,
    min_brightness: float = 10.0,
) -> tuple[bool, Optional[str]]:
    """Extract sample frames via FFmpeg and verify that video contains visible image frames.

    Guarantees that pure black screens (e.g. from GDI capture failure) are rejected.
    Returns: (is_visible, error_message)
    """
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"

    if sample_seconds is None:
        sample_seconds = [1.0, 2.0]

    for ss in sample_seconds:
        cmd = [
            FFMPEG_BIN,
            "-y",
            "-ss",
            str(ss),
            "-i",
            str(file_path),
            "-vframes",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "gray",
            "pipe:1",
        ]

        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=10)
            if proc.returncode != 0 or not proc.stdout:
                continue

            raw_bytes = proc.stdout
            mean_val = sum(raw_bytes) / len(raw_bytes)
            max_val = max(raw_bytes)

            if mean_val >= min_brightness and max_val >= 25:
                return True, None

        except subprocess.TimeoutExpired:
            return False, f"FFmpeg timed out extracting sample frame at {ss}s"
        except Exception as e:
            return False, f"Failed checking frame brightness: {e}"

    return False, f"Video content check failed: frames appear to be black or empty (brightness below {min_brightness})"
