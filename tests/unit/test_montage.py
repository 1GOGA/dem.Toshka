"""Unit tests for Highlight Montage compiler."""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

from backend.render.montage import create_montage, MontageResult


class TestMontageCompiler:
    def test_empty_clips_returns_unsuccessful_result(self, tmp_path):
        out = tmp_path / "montage.mp4"
        result = create_montage([], out)
        assert isinstance(result, MontageResult)
        assert not result.success
        assert "No clips provided" in (result.error_message or "")

    def test_missing_input_clip_returns_unsuccessful_result(self, tmp_path):
        missing = tmp_path / "missing.mp4"
        out = tmp_path / "montage.mp4"
        result = create_montage([missing], out)
        assert isinstance(result, MontageResult)
        assert not result.success
        assert "Clip file not found" in (result.error_message or "")

    @patch("backend.render.montage.subprocess.run")
    @patch("backend.render.montage.verify_media_integrity")
    @patch("backend.render.montage.verify_mp4")
    def test_successful_montage_compilation(self, mock_verify, mock_integrity, mock_subproc, tmp_path):
        # Create dummy input files
        clip1 = tmp_path / "clip1.mp4"
        clip2 = tmp_path / "clip2.mp4"
        clip1.write_bytes(b"dummy1")
        clip2.write_bytes(b"dummy2")

        out = tmp_path / "output_montage.mp4"

        # Mock FFmpeg subprocess execution
        def fake_ffmpeg_run(*args, **kwargs):
            # Simulate FFmpeg creating the temporary output file
            temp_out = out.with_name(f"temp_montage_{out.name}")
            temp_out.write_bytes(b"dummy_montage_mp4")
            res = MagicMock()
            res.returncode = 0
            res.stdout = "FFmpeg success"
            res.stderr = ""
            return res

        mock_subproc.side_effect = fake_ffmpeg_run
        mock_verify.return_value = (True, 12.0, None)
        mock_integrity.return_value = (True, None)

        result = create_montage([clip1, clip2], out)

        assert isinstance(result, MontageResult)
        assert result.success
        assert result.output_path == out
        assert result.clip_count == 2
        assert result.duration_seconds == 12.0
        assert mock_subproc.called

    @patch("backend.render.montage.subprocess.run")
    def test_ffmpeg_failure_returns_unsuccessful_result(self, mock_subproc, tmp_path):
        clip1 = tmp_path / "clip1.mp4"
        clip1.write_bytes(b"dummy1")
        out = tmp_path / "output_montage.mp4"

        res = MagicMock()
        res.returncode = 1
        res.stderr = "Invalid data found when processing input"
        mock_subproc.return_value = res

        result = create_montage([clip1], out)
        assert isinstance(result, MontageResult)
        assert not result.success
        assert "FFmpeg concat failed" in (result.error_message or "")

