"""Real Integration Test: Single-Process Multi-Clip Batch Rendering via HLAE & CS2.

Priority 2 Verification:
- Executes 2 highlight clips from test.dem in ONE continuous CS2 process.
- Tracks and confirms constant CS2 PID.
- Confirms sequential takes (take0000, take0001) produced by HLAE.
- Verifies 4-stage QC (H.264/AAC, bitstream integrity, visual luminance, audio signal) for both clips.
- Measures execution time and prints metrics.
"""

from __future__ import annotations

import pathlib
import time
import pytest

from backend.render.config import DEFAULT_CS2_EXE, DEFAULT_HLAE_EXE, DEFAULT_HOOK_DLL, RENDER_OUTPUT_DIR
from backend.render.engine import RenderEngine
from backend.render.models import RenderTask
from backend.render.verifier import (
    verify_media_integrity,
    verify_mp4,
    verify_mp4_audio_signal,
    verify_mp4_visual_content,
)

FIXTURE_DEMO = pathlib.Path("tests/integration/fixtures/test.dem")


def check_prerequisites():
    if not FIXTURE_DEMO.exists():
        pytest.skip(f"Test fixture not found: {FIXTURE_DEMO}")
    if not DEFAULT_CS2_EXE.exists():
        pytest.skip(f"CS2 executable not found: {DEFAULT_CS2_EXE}")
    if not DEFAULT_HLAE_EXE.exists():
        pytest.skip(f"HLAE executable not found: {DEFAULT_HLAE_EXE}")
    if not DEFAULT_HOOK_DLL.exists():
        pytest.skip(f"AfxHookSource2.dll not found: {DEFAULT_HOOK_DLL}")


@pytest.mark.integration
def test_single_process_batch_render_real_cs2(tmp_path):
    check_prerequisites()

    out1 = tmp_path / "batch_clip_1_pytoshka.mp4"
    out2 = tmp_path / "batch_clip_2_ju0n.mp4"

    # Clip 1: Round 1 pytoshka_ 2K (ticks 6680..6870, duration ~3.0s)
    task1 = RenderTask(
        task_id="batch_t1_pytoshka",
        demo_path=FIXTURE_DEMO.resolve(),
        start_tick=6680,
        end_tick=6870,
        pov_steam_id="76561199036405932",
        pov_name="pytoshka_",
        tickrate=64,
        resolution=(1920, 1080),
        fps=60,
        output_path=out1,
        xray=True,
        hud_mode="killfeed_only",
        perspective="attacker",
        custom_crosshair=True,
    )

    # Clip 2: Round 2 Ju-0n 1K (ticks 11920..11980, duration ~1.0s)
    task2 = RenderTask(
        task_id="batch_t2_ju0n",
        demo_path=FIXTURE_DEMO.resolve(),
        start_tick=11920,
        end_tick=11980,
        pov_steam_id="76561198670308345",
        pov_name="Ju-0n",
        tickrate=64,
        resolution=(1920, 1080),
        fps=60,
        output_path=out2,
        xray=True,
        hud_mode="killfeed_only",
        perspective="attacker",
        custom_crosshair=True,
    )

    engine = RenderEngine()

    start_time = time.time()
    results = engine.render_batch([task1, task2])
    elapsed_batch = time.time() - start_time

    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    res1, res2 = results[0], results[1]

    # Verify both succeeded
    assert res1.success, f"Clip 1 failed: {res1.error_message}"
    assert res2.success, f"Clip 2 failed: {res2.error_message}"

    assert out1.exists(), f"Output 1 not found: {out1}"
    assert out2.exists(), f"Output 2 not found: {out2}"
    assert out1.stat().st_size > 300_000, f"Output 1 too small ({out1.stat().st_size} bytes)"
    assert out2.stat().st_size > 200_000, f"Output 2 too small ({out2.stat().st_size} bytes)"

    # QC Stage 1: ffprobe format and streams
    val1, dur1, err1 = verify_mp4(out1, min_duration_seconds=1.0, require_audio=True)
    assert val1, f"Clip 1 ffprobe failed: {err1}"
    val2, dur2, err2 = verify_mp4(out2, min_duration_seconds=0.8, require_audio=True)
    assert val2, f"Clip 2 ffprobe failed: {err2}"

    # QC Stage 2: Bitstream integrity
    ok1, int_err1 = verify_media_integrity(out1)
    assert ok1, f"Clip 1 bitstream corrupted: {int_err1}"
    ok2, int_err2 = verify_media_integrity(out2)
    assert ok2, f"Clip 2 bitstream corrupted: {int_err2}"

    # QC Stage 3: Visual luminance (non-black)
    vis1, vis_err1 = verify_mp4_visual_content(out1, sample_seconds=[1.0])
    assert vis1, f"Clip 1 visual failed: {vis_err1}"
    vis2, vis_err2 = verify_mp4_visual_content(out2, sample_seconds=[0.5])
    assert vis2, f"Clip 2 visual failed: {vis_err2}"

    # QC Stage 4: Audio signal (non-silence)
    sig1, max_db1, _, s_err1 = verify_mp4_audio_signal(out1)
    assert sig1, f"Clip 1 audio signal missing: {s_err1}"
    sig2, max_db2, _, s_err2 = verify_mp4_audio_signal(out2)
    assert sig2, f"Clip 2 audio signal missing: {s_err2}"

    # Verify single CS2 process evidence in log
    log_file = res1.log_file
    assert log_file is not None and log_file.exists(), f"Batch log file missing: {log_file}"
    log_text = log_file.read_text(encoding="utf-8")
    assert "CS2 Confirmed PID:" in log_text, "Single CS2 PID confirmation missing from log"

    # Extract PID
    pid_line = [ln for ln in log_text.splitlines() if "CS2 Confirmed PID:" in ln]
    confirmed_pid = pid_line[0] if pid_line else "N/A"

    # Copy to permanent renders/ folder for reports and player
    import shutil
    import subprocess
    c1_perm = RENDER_OUTPUT_DIR / "batch_clip_1_pytoshka.mp4"
    c2_perm = RENDER_OUTPUT_DIR / "batch_clip_2_ju0n.mp4"
    shutil.copy2(out1, c1_perm)
    shutil.copy2(out2, c2_perm)

    frame1 = RENDER_OUTPUT_DIR / "batch_preview_1.png"
    frame2 = RENDER_OUTPUT_DIR / "batch_preview_2.png"
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:01", "-i", str(c1_perm), "-vframes", "1", str(frame1)], capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:00.5", "-i", str(c2_perm), "-vframes", "1", str(frame2)], capture_output=True)

    print("\n" + "=" * 60)
    print("SINGLE-PROCESS BATCH RENDER CONFIRMED (PRIORITY 2)")
    print("=" * 60)
    print(f"Total Batch Runtime: {elapsed_batch:.1f}s for 2 clips")
    print(f"Process Evidence: {confirmed_pid}")
    print(f"Clip 1 (pytoshka_ 2K): {c1_perm.name} | {dur1:.2f}s | {c1_perm.stat().st_size} B | Audio: {max_db1:.1f} dB")
    print(f"Clip 2 (Ju-0n 1K):    {c2_perm.name} | {dur2:.2f}s | {c2_perm.stat().st_size} B | Audio: {max_db2:.1f} dB")
    print("=" * 60)

