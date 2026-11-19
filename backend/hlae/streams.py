"""HLAE mirv_streams multi-pass stream capture manager for Counter-Strike 2.

Manages video/audio stream separation, layer profiles, and AfxHookSource2 0.42.0+
FFmpeg convar option formatting.
"""

from __future__ import annotations

import enum
import pathlib
from dataclasses import dataclass, field
from typing import Optional


class StreamProfile(str, enum.Enum):
    """Pre-defined capture profiles for fragmovies, esports broadcasts, and VFX."""
    CLEAN_CINEMATIC = "clean_cinematic"    # Zero HUD, no killfeed, maximum visual fidelity
    BROADCAST_ESPORTS = "broadcast_esports" # In-game deathnotices only, realistic broadcast look
    VFX_MULTIPASS = "vfx_multipass"        # Multi-layer game + matte/depth (when supported) + audio
    AUDIO_STEMS = "audio_stems"            # Isolated game audio wav stream for external mixing
    RAW_LOSSLESS = "raw_lossless"          # Lossless RGB/YUV444 capture for Davinci Resolve grading


@dataclass
class StreamLayer:
    """A configured capture layer in mirv_streams."""
    name: str
    stream_type: str = "normal"  # normal, depth, etc.
    settings: str = "afxFfmpegYuv420p"
    record_audio: bool = False
    custom_ffmpeg_options: Optional[str] = None


class HLAEStreamManager:
    """Manages mirv_streams configuration for single and multi-pass CS2 rendering."""

    DEFAULT_FFMPEG_OPTIONS = {
        "afxFfmpegYuv420p": "-c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p",
        "afxFfmpegLossless": "-c:v libx264 -preset veryslow -qp 0 -pix_fmt yuv420p",
        "afxFfmpegProRes": "-c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le",
    }

    def __init__(self, output_dir: pathlib.Path | str) -> None:
        self.output_dir = pathlib.Path(output_dir)
        self._layers: list[StreamLayer] = []

    @staticmethod
    def format_afx_ffmpeg_options(options: str) -> str:
        """Escape FFmpeg command options for AfxHookSource2 0.42.0+ console parser.
        
        AfxHookSource2 0.42.0+ requires double curly braces {{ }} around complex
        argument strings containing spaces or flags to avoid argument splitting.
        """
        trimmed = options.strip()
        if trimmed.startswith("{{") and trimmed.endswith("}}"):
            return trimmed
        return f"{{{{ {trimmed} }}}}"

    def add_layer(
        self,
        name: str,
        stream_type: str = "normal",
        settings: str = "afxFfmpegYuv420p",
        record_audio: bool = False,
        custom_ffmpeg_options: Optional[str] = None,
    ) -> HLAEStreamManager:
        """Register a stream layer for capture."""
        self._layers.append(
            StreamLayer(
                name=name,
                stream_type=stream_type,
                settings=settings,
                record_audio=record_audio,
                custom_ffmpeg_options=custom_ffmpeg_options,
            )
        )
        return self

    def apply_profile(self, profile: StreamProfile, base_name: str = "take") -> list[str]:
        """Configure streams according to a high-level production profile."""
        self._layers.clear()

        if profile == StreamProfile.CLEAN_CINEMATIC:
            self.add_layer(
                name=f"{base_name}_cinematic",
                stream_type="normal",
                settings="afxFfmpegYuv420p",
                record_audio=True,
            )
        elif profile == StreamProfile.BROADCAST_ESPORTS:
            self.add_layer(
                name=f"{base_name}_broadcast",
                stream_type="normal",
                settings="afxFfmpegYuv420p",
                record_audio=True,
            )
        elif profile == StreamProfile.RAW_LOSSLESS:
            self.add_layer(
                name=f"{base_name}_lossless",
                stream_type="normal",
                settings="afxFfmpegLossless",
                record_audio=True,
                custom_ffmpeg_options="-c:v libx264 -preset medium -qp 0 -pix_fmt yuv420p",
            )
        elif profile == StreamProfile.AUDIO_STEMS:
            self.add_layer(
                name=f"{base_name}_audio",
                stream_type="normal",
                settings="afxFfmpegYuv420p",
                record_audio=True,
            )
        elif profile == StreamProfile.VFX_MULTIPASS:
            # Main game plate
            self.add_layer(
                name=f"{base_name}_beauty",
                stream_type="normal",
                settings="afxFfmpegYuv420p",
                record_audio=True,
            )
            # Separate secondary pass if needed
            self.add_layer(
                name=f"{base_name}_clean",
                stream_type="normal",
                settings="afxFfmpegYuv420p",
                record_audio=False,
            )

        return self.generate_commands()

    def generate_commands(self) -> list[str]:
        """Generate mirv_streams console commands for all configured layers."""
        cmds: list[str] = [
            "mirv_streams record screen enabled 0",  # Disable default screen record to use custom layers
            "mirv_streams remove all",
        ]

        # Ensure forward slashes for Source 2 path parser
        safe_output_dir = str(self.output_dir.resolve()).replace("\\", "/")
        cmds.append(f'mirv_streams record name "{safe_output_dir}"')

        for layer in self._layers:
            cmds.append(f"mirv_streams add {layer.stream_type} {layer.name}")
            cmds.append(f"mirv_streams edit {layer.name} settings {layer.settings}")

            if layer.record_audio:
                cmds.append(f"mirv_streams edit {layer.name} recordAudio 1")
            else:
                cmds.append(f"mirv_streams edit {layer.name} recordAudio 0")

            if layer.custom_ffmpeg_options:
                formatted_opt = self.format_afx_ffmpeg_options(layer.custom_ffmpeg_options)
                cmds.append(f"mirv_streams settings edit {layer.settings} options {formatted_opt}")

        cmds.append("mirv_streams record screen enabled 1")
        return cmds

    def get_output_artifacts(self, base_name: str) -> list[pathlib.Path]:
        """List anticipated video and audio file outputs from the stream configuration."""
        outputs: list[pathlib.Path] = []
        for layer in self._layers:
            outputs.append(self.output_dir / f"{layer.name}.mp4")
            if layer.record_audio:
                outputs.append(self.output_dir / f"{layer.name}.wav")
        return outputs
