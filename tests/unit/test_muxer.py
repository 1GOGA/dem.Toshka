"""Unit tests for Video and Audio Multiplexer (muxer.py) and Audio Verifier."""

from __future__ import annotations

import pathlib
import pytest

from backend.render.muxer import mux_video_and_audio, probe_media_info
from backend.render.verifier import verify_mp4, verify_mp4_audio_signal


POC_VIDEO = pathlib.Path("renders/hlae_poc/take0000/video.mp4")
POC_AUDIO = pathlib.Path("renders/hlae_poc/take0000/audio.wav")


class TestMuxerBasics:
    def test_missing_video_returns_error(self, tmp_path):
        missing_vid = tmp_path / "missing_video.mp4"
        audio = tmp_path / "audio.wav"
        audio.touch()
        out = tmp_path / "output.mp4"

        res = mux_video_and_audio(missing_vid, audio, out)
        assert not res.success
        assert "video file does not exist" in (res.error_message or "").lower()

    def test_empty_video_returns_error(self, tmp_path):
        empty_vid = tmp_path / "empty.mp4"
        empty_vid.touch()
        audio = tmp_path / "audio.wav"
        audio.touch()
        out = tmp_path / "output.mp4"

        res = mux_video_and_audio(empty_vid, audio, out)
        assert not res.success
        assert "empty" in (res.error_message or "").lower()

    def test_missing_audio_exports_video_with_warning(self, tmp_path):
        if not POC_VIDEO.exists():
            pytest.skip("PoC video fixture not present on disk")

        missing_audio = tmp_path / "missing_audio.wav"
        out = tmp_path / "out_no_audio.mp4"

        res = mux_video_and_audio(POC_VIDEO, missing_audio, out)
        assert res.success
        assert res.output_path == out
        assert out.exists()
        assert not res.has_audio
        assert res.warning_message is not None
        assert "audio file not found" in res.warning_message.lower()

        # Probing the output with require_audio=False passes, require_audio=True fails
        valid_no_req, _, _ = verify_mp4(out, require_audio=False)
        assert valid_no_req
        valid_req, _, err = verify_mp4(out, require_audio=True)
        assert not valid_req
        assert "audio track is missing" in (err or "").lower()

    def test_none_audio_exports_video_with_warning(self, tmp_path):
        if not POC_VIDEO.exists():
            pytest.skip("PoC video fixture not present on disk")

        out = tmp_path / "out_none_audio.mp4"
        res = mux_video_and_audio(POC_VIDEO, None, out)
        assert res.success
        assert not res.has_audio
        assert out.exists()

    def test_invalid_audio_file_returns_error(self, tmp_path):
        if not POC_VIDEO.exists():
            pytest.skip("PoC video fixture not present on disk")

        corrupt_audio = tmp_path / "corrupt.wav"
        corrupt_audio.write_text("This is not a real WAV audio file")
        out = tmp_path / "out_corrupt.mp4"

        res = mux_video_and_audio(POC_VIDEO, corrupt_audio, out)
        assert not res.success
        assert "no valid audio stream" in (res.error_message or "").lower()
        # Staging cleanup: destination must not be created
        assert not out.exists()

    def test_ffmpeg_binary_invalid_returns_error(self, tmp_path):
        if not POC_VIDEO.exists() or not POC_AUDIO.exists():
            pytest.skip("PoC fixtures not present on disk")

        out = tmp_path / "out_fail.mp4"
        res = mux_video_and_audio(
            POC_VIDEO,
            POC_AUDIO,
            out,
            ffmpeg_bin="nonexistent_ffmpeg_executable_xyz",
        )
        assert not res.success
        assert "nonexistent_ffmpeg" in (res.error_message or "").lower() or "unexpected error" in (res.error_message or "").lower()


class TestMuxerWithRealPocFixtures:
    def test_successful_video_audio_muxing(self, tmp_path):
        if not POC_VIDEO.exists() or not POC_AUDIO.exists():
            pytest.skip("PoC fixtures not present on disk")

        out = tmp_path / "muxed_clip.mp4"
        res = mux_video_and_audio(POC_VIDEO, POC_AUDIO, out)

        assert res.success
        assert res.output_path == out
        assert out.exists()
        assert out.stat().st_size > 1_000_000
        assert res.has_audio
        assert res.duration_seconds > 4.0
        assert res.duration_diff < 0.1  # PoC video and audio durations within 5ms

        # 1. Verify container with require_audio=True
        is_valid, probed_dur, err = verify_mp4(out, require_audio=True)
        assert is_valid, f"Verification failed: {err}"
        assert probed_dur is not None and probed_dur > 4.0

        # 2. Check stream types via probe
        info = probe_media_info(out)
        streams = info.get("streams", [])
        codecs = {s.get("codec_type"): s.get("codec_name") for s in streams}
        assert codecs.get("video") == "h264"
        assert codecs.get("audio") == "aac"

        # 3. Check audio loudness signal
        has_signal, max_db, mean_db, sig_msg = verify_mp4_audio_signal(out)
        assert has_signal, f"Audio signal check failed: {sig_msg}"
        assert max_db is not None and max_db > -40.0
        assert mean_db is not None and mean_db > -60.0


class TestAudioVerifier:
    def test_verify_audio_signal_missing_file(self, tmp_path):
        missing = tmp_path / "missing.mp4"
        has_sig, max_db, mean_db, err = verify_mp4_audio_signal(missing)
        assert not has_sig
        assert "does not exist" in (err or "").lower()

    def test_verify_audio_signal_on_poc_audio(self):
        if not POC_AUDIO.exists():
            pytest.skip("PoC audio fixture not present")

        has_sig, max_db, mean_db, err = verify_mp4_audio_signal(POC_AUDIO)
        assert has_sig
        assert err is None
        assert max_db is not None and max_db > -30.0
        assert mean_db is not None and mean_db > -50.0

