"""Type-safe console command generator for Counter-Strike 2 and HLAE / AfxHookSource2."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScheduledCommand:
    """A command scheduled to execute at a precise demo tick."""

    tick: int
    command: str


class HLAECommandBuilder:
    """Builds robust, validated CS2 configuration scripts for automated HLAE replay and capture."""

    def __init__(self) -> None:
        self._initial_commands: list[str] = []
        self._scheduled_commands: list[ScheduledCommand] = []
        self._shutdown_commands: list[str] = []

    def add_command(self, cmd: str) -> HLAECommandBuilder:
        """Add an immediate command executed upon script execution."""
        cleaned = cmd.strip()
        if cleaned:
            self._initial_commands.append(cleaned)
        return self

    def add_at_tick(self, tick: int, cmd: str) -> HLAECommandBuilder:
        """Schedule a command to execute at a specific demo tick using mirv_cmd."""
        cleaned = cmd.strip()
        if cleaned:
            self._scheduled_commands.append(ScheduledCommand(tick=int(tick), command=cleaned))
        return self

    def set_host_framerate(self, fps: int = 60) -> HLAECommandBuilder:
        """Lock in-engine frame delta for smooth video recording without frame drops."""
        return self.add_command(f"host_framerate {int(fps)}")

    def set_hud_mode(self, mode: str = "full") -> HLAECommandBuilder:
        """Configure HUD presentation (full, clean, deathnotices_only, minimal)."""
        if mode == "clean" or mode == "cinematic":
            self.add_command("cl_draw_only_deathnotices 1")
            self.add_command("r_show_build_info 0")
            self.add_command("cl_sanitize_player_names 0")
        elif mode == "deathnotices_only" or mode == "killfeed_only":
            self.add_command("cl_draw_only_deathnotices 1")
            self.add_command("r_show_build_info 0")
        elif mode == "hidden":
            self.add_command("cl_drawhud 0")
            self.add_command("r_show_build_info 0")
        else:  # "full"
            self.add_command("cl_draw_only_deathnotices 0")
            self.add_command("cl_drawhud 1")
            self.add_command("r_show_build_info 0")
        return self

    def set_xray(self, enabled: bool = True) -> HLAECommandBuilder:
        """Toggle spectator player outlines / X-ray visibility."""
        val = 1 if enabled else 0
        return self.add_command(f"spec_show_xray {val}")

    def lock_spectator_pov(self, account_id: Optional[int], name: Optional[str] = None) -> HLAECommandBuilder:
        """Lock spectator camera to target player by 32-bit AccountID or name."""
        self.add_command("spec_autodirector 0")
        self.add_command("spec_mode 4")
        if account_id:
            self.add_command(f"spec_player_by_accountid {account_id}")
        elif name:
            safe_name = name.replace('"', "")
            self.add_command(f'spec_player "{safe_name}"')
        return self

    def load_campath(self, campath_xml: pathlib.Path) -> HLAECommandBuilder:
        """Load and enable in-engine camera spline path."""
        safe_path = str(campath_xml.resolve()).replace("\\", "/")
        self.add_command("mirv_campath clear")
        self.add_command(f'mirv_campath load "{safe_path}"')
        self.add_command("mirv_campath enabled 1")
        self.add_command("mirv_campath draw 0")
        return self

    def configure_stream_recording(
        self,
        output_name: str,
        settings_preset: str = "afxFfmpegYuv420p",
        record_audio: bool = True,
    ) -> HLAECommandBuilder:
        """Configure mirv_streams for hardware-synchronized frame capture."""
        safe_name = output_name.replace('"', "").replace(" ", "_")
        self.add_command("mirv_streams record screen enabled 1")
        self.add_command(f"mirv_streams record screen settings {settings_preset}")
        self.add_command(f'mirv_streams record name "{safe_name}"')
        if record_audio:
            self.add_command("mirv_streams record screen recordAudio 1")
        return self

    def schedule_recording_window(
        self,
        start_tick: int,
        end_tick: int,
        quit_on_finish: bool = True,
    ) -> HLAECommandBuilder:
        """Schedule start and end of recording across exact ticks."""
        self.add_at_tick(start_tick, "mirv_streams record start")
        if quit_on_finish:
            self.add_at_tick(end_tick, "mirv_streams record end ; quit")
        else:
            self.add_at_tick(end_tick, "mirv_streams record end")
        return self

    def build_cfg_text(self) -> str:
        """Generate formatted Counter-Strike 2 CFG script content."""
        lines: list[str] = [
            "// dem.Toshka Professional HLAE & CS2 Production Script",
            "// Generated automatically with tick-synchronized execution",
            "",
            "// --- 1. Initial Engine & Display Environment ---",
        ]
        lines.extend(self._initial_commands)
        lines.append("")

        if self._scheduled_commands:
            lines.append("// --- 2. Scheduled mirv_cmd Tick Directives ---")
            # Sort scheduled commands chronologically by tick
            sorted_sched = sorted(self._scheduled_commands, key=lambda x: x.tick)
            for item in sorted_sched:
                safe_cmd = item.command.replace('"', '\\"')
                lines.append(f'mirv_cmd addAtTick {item.tick} "{safe_cmd}"')
            lines.append("")

        if self._shutdown_commands:
            lines.append("// --- 3. Finalization Commands ---")
            lines.extend(self._shutdown_commands)
            lines.append("")

        return "\n".join(lines) + "\n"
