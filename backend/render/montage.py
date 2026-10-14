"""Montage & compilation module for CS2 Highlights Studio.

Concatenates multiple rendered highlight MP4 clips into a single continuous
movie file using FFmpeg's concat demuxer without re-encoding (lossless -c copy).
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import pathlib
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger("demtoshka.montage")

from backend.render.config import FFMPEG_BIN, RENDER_OUTPUT_DIR
from backend.render.verifier import verify_media_integrity, verify_mp4


@dataclass
class MontageResult:
    """Result of combining multiple clips into a single compilation."""

    success: bool
    output_path: Optional[pathlib.Path]
    duration_seconds: float
    clip_count: int
    error_message: Optional[str] = None


def create_montage(
    clip_paths: list[pathlib.Path],
    output_path: Optional[pathlib.Path] = None,
    ffmpeg_bin: str = FFMPEG_BIN,
) -> MontageResult:
    """Concatenate multiple highlight MP4 clips into a single montage MP4 file.

    Uses the FFmpeg concat demuxer with stream copying (-c copy) for instantaneous,
    lossless joining of identically-encoded clips.
    """
    if not clip_paths:
        return MontageResult(
            success=False,
            output_path=None,
            duration_seconds=0.0,
            clip_count=0,
            error_message="No clips provided for montage compilation",
        )

    # 1. Validate all input files exist and are non-empty
    valid_clips: list[pathlib.Path] = []
    missing_clips: list[pathlib.Path] = []
    for p in clip_paths:
        resolved = p.resolve()
        if resolved.is_file() and resolved.stat().st_size > 0:
            valid_clips.append(resolved)
        else:
            missing_clips.append(p)
            logger.warning("Skipping missing or empty clip for montage: %s", p)

    if not valid_clips:
        first_missing = missing_clips[0] if missing_clips else "none"
        return MontageResult(
            success=False,
            output_path=None,
            duration_seconds=0.0,
            clip_count=0,
            error_message=f"Clip file not found or empty: {first_missing}",
        )

    # 2. Determine target output path if not provided
    if output_path is None:
        RENDER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp_str = tempfile.NamedTemporaryFile().name.split("\\")[-1]
        output_path = RENDER_OUTPUT_DIR / f"montage_{timestamp_str}.mp4"
    else:
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_output = output_path.with_name(f"temp_montage_{output_path.name}")

    # 3. Create concat list file
    concat_file = output_path.with_name(f"concat_list_{output_path.stem}.txt")
    try:
        lines = []
        for p in valid_clips:
            # Escape single quotes and forward slash paths for FFmpeg concat format
            escaped_path = str(p).replace("\\", "/").replace("'", "'\\''")
            lines.append(f"file '{escaped_path}'")
        concat_file.write_text("\n".join(lines), encoding="utf-8")

        # 4. Execute FFmpeg concat command
        cmd = [
            ffmpeg_bin,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file.resolve()),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(temp_output.resolve()),
        ]

        logger.info("Executing FFmpeg montage concat for %d clips: %s", len(valid_clips), " ".join(cmd))
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120.0)

        if res.returncode != 0 or not temp_output.exists() or temp_output.stat().st_size == 0:
            logger.warning("Stream-copy concat failed; falling back to filter_complex normalization...")
            inputs = []
            filter_parts = []
            for i, p in enumerate(valid_clips):
                inputs.extend(["-i", str(p.resolve())])
                filter_parts.append(
                    f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=60,setsar=1[v{i}];"
                    f"[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}];"
                )
            concat_str = "".join(f"[v{i}][a{i}]" for i in range(len(valid_clips)))
            filter_complex = "".join(filter_parts) + f"{concat_str}concat=n={len(valid_clips)}:v=1:a=1[outv][outa]"
            norm_cmd = [
                ffmpeg_bin,
                "-y",
                *inputs,
                "-filter_complex",
                filter_complex,
                "-map",
                "[outv]",
                "-map",
                "[outa]",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                str(temp_output.resolve()),
            ]
            res_norm = subprocess.run(norm_cmd, capture_output=True, text=True, timeout=300.0)
            if res_norm.returncode != 0 or not temp_output.exists() or temp_output.stat().st_size == 0:
                err_msg = res_norm.stderr.strip() if res_norm.stderr else "FFmpeg normalization failed"
                logger.error("FFmpeg normalization failed: %s", err_msg)
                return MontageResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    clip_count=len(valid_clips),
                    error_message=f"FFmpeg concat failed (normalization also failed): {err_msg[:300]}",
                )

        # 5. Quality Control: Verify output container & streams
        is_valid, duration, val_err = verify_mp4(temp_output, require_audio=True)
        if not is_valid:
            if temp_output.exists():
                temp_output.unlink()
            return MontageResult(
                success=False,
                output_path=None,
                duration_seconds=0.0,
                clip_count=len(valid_clips),
                error_message=f"Montage output validation failed: {val_err}",
            )

        integrity_timeout = max(60.0, (duration or 30.0) * 2.5)
        is_intact, int_err = verify_media_integrity(temp_output, timeout=integrity_timeout)
        if not is_intact:
            if "timed out" in (int_err or "").lower():
                logger.warning(
                    "Montage integrity check timed out (%s), but container validation passed. Accepting montage.",
                    int_err,
                )
            else:
                if temp_output.exists():
                    temp_output.unlink()
                return MontageResult(
                    success=False,
                    output_path=None,
                    duration_seconds=0.0,
                    clip_count=len(valid_clips),
                    error_message=f"Montage integrity check failed: {int_err}",
                )

        # 6. Atomic move to final target path
        if output_path.exists():
            output_path.unlink()
        temp_output.rename(output_path)

        logger.info(
            "Successfully created montage with %d clips (duration: %.2fs) at %s",
            len(valid_clips),
            duration or 0.0,
            output_path,
        )

        return MontageResult(
            success=True,
            output_path=output_path,
            duration_seconds=duration or 0.0,
            clip_count=len(valid_clips),
            error_message=None,
        )

    except Exception as e:
        logger.exception("Unexpected error in montage creation: %s", e)
        if temp_output.exists():
            try:
                temp_output.unlink()
            except Exception:
                pass
        return MontageResult(
            success=False,
            output_path=None,
            duration_seconds=0.0,
            clip_count=len(valid_clips),
            error_message=str(e),
        )
    finally:
        if concat_file.exists():
            try:
                concat_file.unlink()
            except Exception:
                pass
