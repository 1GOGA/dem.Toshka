from __future__ import annotations

from dataclasses import dataclass, field
import pathlib
from typing import Optional

from backend.render.profiles import RenderProfileType, get_profile

STEAM64_BASE = 76561197960265728


@dataclass
class BatchClipItem:
    """Specification of a single highlight clip to record during a batch session."""

    clip_id: str
    start_tick: int
    end_tick: int
    pov_steam_id: Optional[str] = None
    pov_name: Optional[str] = None
    xray: bool = True
    hud_mode: str = "full"
    custom_crosshair: bool = True
    profile: RenderProfileType = RenderProfileType.CLEAN_COMPETITIVE
    fov: Optional[int] = None
    viewmodel_fov: Optional[int] = None
    crosshair_preset: str = "pro_cyan"
    crosshair_color: Optional[str] = None
    radar_mode: str = "player_focus"
    hud_scale: Optional[float] = None
    overhead_mode: Optional[bool] = None
    killfeed_only: Optional[bool] = None
    teamcounter_mode: Optional[bool] = None
    camera_switches: list[tuple[int, Optional[str], Optional[str]]] = field(default_factory=list)
    # Tournament Killcam Replay (Victim death POV -> Rewind -> Hero POV)
    is_killcam_replay: bool = False
    killcam_victim_steam_id: Optional[str] = None
    killcam_victim_name: Optional[str] = None
    killcam_victim_start_tick: Optional[int] = None
    killcam_victim_end_tick: Optional[int] = None
    killcam_hero_start_tick: Optional[int] = None


def steam64_to_account_id(steam64: str) -> Optional[int]:
    """Convert SteamID64 string to 32-bit AccountID used by Source 2."""
    try:
        val = int(steam64)
        if val > STEAM64_BASE:
            return val - STEAM64_BASE
    except (ValueError, TypeError):
        pass
    return None


def _build_radar_commands(radar_mode: str = "player_focus") -> list[str]:
    """Build tournament broadcast or dynamic in-game radar convars.
    
    Enforces authentic circular (round) radar by disabling CS2's spectator square radar.
    """
    if radar_mode == "dynamic_large":
        # Ultra-large dynamic rotating round radar: tracks player movement and rotates with aim
        return [
            "cl_hud_radar_scale 1.30",
            "cl_radar_always_centered 1",
            "cl_radar_scale 0.70",
            "cl_radar_rotate 1",
            "cl_radar_icon_scale_min 0.90",
            "cl_radar_square_when_spectating 0",
            "cl_radar_square_always 0",
            "cl_radar_square_with_scoreboard 0",
        ]
    elif radar_mode == "broadcast_giant":
        # Ultra-large tournament overview: maximum radar size with full map coverage
        return [
            "cl_hud_radar_scale 1.30",
            "cl_radar_always_centered 0",
            "cl_radar_scale 0.52",
            "cl_radar_rotate 0",
            "cl_radar_icon_scale_min 0.85",
            "cl_radar_square_when_spectating 0",
            "cl_radar_square_always 0",
            "cl_radar_square_with_scoreboard 0",
        ]
    elif radar_mode == "broadcast":
        # Pro tournament broadcast: full map overview in circular radar, north fixed, large sharp icons
        return [
            "cl_hud_radar_scale 1.25",
            "cl_radar_always_centered 0",
            "cl_radar_scale 0.55",
            "cl_radar_rotate 0",
            "cl_radar_icon_scale_min 0.75",
            "cl_radar_square_when_spectating 0",
            "cl_radar_square_always 0",
            "cl_radar_square_with_scoreboard 0",
        ]
    elif radar_mode == "compact":
        return [
            "cl_hud_radar_scale 0.95",
            "cl_radar_always_centered 1",
            "cl_radar_scale 0.70",
            "cl_radar_rotate 1",
            "cl_radar_icon_scale_min 0.6",
            "cl_radar_square_when_spectating 0",
            "cl_radar_square_always 0",
            "cl_radar_square_with_scoreboard 0",
        ]
    elif radar_mode == "hidden":
        return [
            "cl_radar_scale 0",
            "cl_hud_radar_scale 0",
        ]
    else:  # "player_focus"
        return [
            "cl_hud_radar_scale 1.15",
            "cl_radar_always_centered 1",
            "cl_radar_scale 0.65",
            "cl_radar_rotate 1",
            "cl_radar_icon_scale_min 0.7",
            "cl_radar_square_when_spectating 0",
            "cl_radar_square_always 0",
            "cl_radar_square_with_scoreboard 0",
        ]


def _build_spec_commands(account_id: Optional[int], pov_name: Optional[str] = None) -> list[str]:
    """Build list of console commands to lock spectator camera to the target player."""
    cmds = ["spec_autodirector 0", "spec_mode 4"]
    if account_id:
        cmds.append(f"spec_lock_to_accountid {account_id}")
    if pov_name:
        safe_name = pov_name.replace('"', "").replace(";", "").strip()
        if safe_name:
            cmds.append(f"spec_player {safe_name}")
    return cmds


def _build_crosshair_commands(preset: str = "pro_cyan", color: Optional[str] = None) -> list[str]:
    """Build clean static pro movie and tournament crosshair commands."""
    if preset in ("hidden", "none"):
        return ["crosshair 0"]
    if preset == "default":
        return ["crosshair 1"]

    colors = {
        "cyan": (0, 255, 180),
        "green": (0, 255, 0),
        "yellow": (255, 215, 0),
        "white": (255, 255, 255),
        "pink": (255, 105, 180),
        "red": (255, 60, 60),
        "blue": (60, 150, 255),
    }
    r, g, b = colors.get((color or "cyan").lower(), (0, 255, 180))

    if preset == "dot":
        # Minimalist movie dot crosshair
        return [
            "crosshair 1",
            "cl_crosshairstyle 4",
            "cl_crosshairsize 0",
            "cl_crosshairgap -5",
            "cl_crosshairthickness 1.5",
            "cl_crosshair_drawoutline 1",
            "cl_crosshair_outlinethickness 1.0",
            "cl_crosshairdot 1",
            "cl_crosshaircolor 5",
            f"cl_crosshaircolor_r {r}",
            f"cl_crosshaircolor_g {g}",
            f"cl_crosshaircolor_b {b}",
            "cl_crosshairusealpha 1",
            "cl_crosshairalpha 255",
            "cl_crosshair_recoil 0",
            "cl_crosshair_sniper_width 1",
        ]
    elif preset == "minimal_white":
        # Ultra-thin clean tournament crosshair
        return [
            "crosshair 1",
            "cl_crosshairstyle 4",
            "cl_crosshairsize 1.2",
            "cl_crosshairgap -2.0",
            "cl_crosshairthickness 0.8",
            "cl_crosshair_drawoutline 1",
            "cl_crosshair_outlinethickness 1.0",
            "cl_crosshairdot 0",
            "cl_crosshaircolor 5",
            "cl_crosshaircolor_r 255",
            "cl_crosshaircolor_g 255",
            "cl_crosshaircolor_b 255",
            "cl_crosshairusealpha 1",
            "cl_crosshairalpha 255",
            "cl_crosshair_recoil 0",
            "cl_crosshair_sniper_width 1",
        ]
    elif preset == "green_clean":
        # Classic CS:GO pro green crosshair
        return [
            "crosshair 1",
            "cl_crosshairstyle 4",
            "cl_crosshairsize 1.5",
            "cl_crosshairgap -3.0",
            "cl_crosshairthickness 1.0",
            "cl_crosshair_drawoutline 0",
            "cl_crosshairdot 0",
            "cl_crosshaircolor 1",
            "cl_crosshairusealpha 1",
            "cl_crosshairalpha 255",
            "cl_crosshair_recoil 0",
            "cl_crosshair_sniper_width 1",
        ]
    else:  # "pro_cyan" (default tournament movie crosshair)
        return [
            "crosshair 1",
            "cl_crosshairstyle 4",
            "cl_crosshairsize 2.0",
            "cl_crosshairgap -2.5",
            "cl_crosshairthickness 1.0",
            "cl_crosshair_drawoutline 1",
            "cl_crosshair_outlinethickness 1.0",
            "cl_crosshairdot 0",
            "cl_crosshaircolor 5",
            f"cl_crosshaircolor_r {r}",
            f"cl_crosshaircolor_g {g}",
            f"cl_crosshaircolor_b {b}",
            "cl_crosshairusealpha 1",
            "cl_crosshairalpha 255",
            "cl_crosshair_recoil 0",
            "cl_crosshair_sniper_width 1",
        ]


def _build_fov_commands(fov: Optional[int] = None, viewmodel_fov: Optional[int] = None) -> list[str]:
    """Build camera FOV and tournament viewmodel commands."""
    cmds: list[str] = []
    if fov and fov > 0:
        cmds.append(f"fov_cs_debug {fov}")
    if viewmodel_fov and viewmodel_fov > 0:
        cmds.append(f"viewmodel_fov {viewmodel_fov}")
        cmds.append("viewmodel_offset_x 2.5")
        cmds.append("viewmodel_offset_y 0")
        cmds.append("viewmodel_offset_z -1.5")
    return cmds


def _build_hud_commands(
    hud_mode: str,
    hud_scale: Optional[float] = None,
    overhead_mode: Optional[bool] = None,
    killfeed_only: Optional[bool] = None,
    teamcounter_mode: Optional[bool] = None,
) -> list[str]:
    """Build HUD commands based on mode and optional explicit scaling and toggles."""
    cmds: list[str] = []
    if hud_mode == "real":
        # REAL OBS POV: Native match recording appearance
        # Normal rotating radar, health/ammo/money/grenades visible, spectator target banner suppressed,
        # player count numbers instead of spectator cards, no X-Ray wallhacks.
        scale = hud_scale if hud_scale is not None else 1.0
        cmds.extend([
            "cl_drawhud 1",
            "cl_draw_only_deathnotices 0",
            f"hud_scaling {scale}",
            "hud_showtargetid 0",
            "cl_spec_show_bindings 0",
            "cl_hide_avatar_images 1",
            "cl_teamid_overhead_mode 0",
            "cl_teamcounter_playercount_mode 1",
            "cl_hud_telemetry_frametime_show 0",
            "cl_hud_telemetry_net_misdelivery_show 0",
            "cl_hud_telemetry_ping_show 0",
        ])
    elif hud_mode == "huge_esports":
        scale = hud_scale if hud_scale is not None else 1.15
        cmds.extend([
            "cl_drawhud 1",
            "cl_draw_only_deathnotices 0",
            f"hud_scaling {scale}",
            "cl_teamcounter_playercount_mode 0",
        ])
    elif hud_mode == "huge_killfeed":
        scale = hud_scale if hud_scale is not None else 1.15
        cmds.extend([
            "cl_drawhud 1",
            "cl_draw_only_deathnotices 1",
            f"hud_scaling {scale}",
        ])
    elif hud_mode == "killfeed_only":
        scale = hud_scale if hud_scale is not None else 0.95
        cmds.extend([
            "cl_drawhud 1",
            "cl_draw_only_deathnotices 1",
            f"hud_scaling {scale}",
        ])
    elif hud_mode == "none":
        cmds.append("cl_drawhud 0")
    else:  # "full"
        scale = hud_scale if hud_scale is not None else 0.95
        cmds.extend([
            "cl_drawhud 1",
            "cl_draw_only_deathnotices 0",
            f"hud_scaling {scale}",
            "cl_teamcounter_playercount_mode 0",
        ])

    # Apply explicit overrides from advanced HUD switches if defined
    if overhead_mode is not None:
        cmds.append(f"cl_teamid_overhead_mode {1 if overhead_mode else 0}")
    if killfeed_only is not None:
        cmds.append(f"cl_draw_only_deathnotices {1 if killfeed_only else 0}")
    if teamcounter_mode is not None:
        cmds.append(f"cl_teamcounter_playercount_mode {1 if teamcounter_mode else 0}")

    return cmds


def generate_render_cfg(
    start_tick: int,
    pov_steam_id: Optional[str] = None,
    pov_name: Optional[str] = None,
    output_cfg_path: Optional[pathlib.Path] = None,
    end_tick: Optional[int] = None,
    output_dir: Optional[pathlib.Path] = None,
    fps: int = 60,
    jump_lead_ticks: int = 20,
    xray: bool = True,
    hud_mode: str = "full",
    hud_scale: Optional[float] = None,
    custom_crosshair: bool = True,
    fov: Optional[int] = None,
    viewmodel_fov: Optional[int] = None,
    crosshair_preset: str = "pro_cyan",
    crosshair_color: Optional[str] = None,
    radar_mode: str = "player_focus",
    overhead_mode: Optional[bool] = None,
    killfeed_only: Optional[bool] = None,
    teamcounter_mode: Optional[bool] = None,
    camera_switches: Optional[list[tuple[int, Optional[str], Optional[str]]]] = None,
    is_killcam_replay: bool = False,
    killcam_victim_steam_id: Optional[str] = None,
    killcam_victim_name: Optional[str] = None,
    killcam_victim_start_tick: Optional[int] = None,
    killcam_victim_end_tick: Optional[int] = None,
    killcam_hero_start_tick: Optional[int] = None,
) -> str:
    """Generate the CS2 .cfg file content for demo seeking and HLAE recording.

    If output_cfg_path is provided, writes the content to disk.
    """
    if hud_mode == "real":
        if radar_mode == "broadcast":
            radar_mode = "player_focus"
        xray = False

    account_id = steam64_to_account_id(pov_steam_id) if pov_steam_id else None

    lines = [
        "// Generated by CS2 Highlights Studio",
        "sv_cheats 1",
        "engine_no_focus_sleep 0",
        "snd_mute_losefocus 0",
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
        "spec_mode 4",
        "safezonex 1.0",
        "safezoney 1.0",
    ]
    lines.extend(_build_radar_commands(radar_mode))
    lines.extend([
        "cl_teamcounter_playercount_mode 0",
        "cl_hud_telemetry_frametime_show 0",
        "cl_hud_telemetry_net_misdelivery_show 0",
        "cl_hud_telemetry_ping_show 0",
    ])

    # FOV & Viewmodel configuration (tournament fragmovie camera)
    fov_cmds = _build_fov_commands(fov, viewmodel_fov)
    if fov_cmds:
        lines.extend(fov_cmds)

    # Pro crosshair configuration
    if custom_crosshair:
        lines.extend(_build_crosshair_commands(preset=crosshair_preset, color=crosshair_color))
    elif crosshair_preset in ("hidden", "none"):
        lines.append("crosshair 0")

    # X-Ray configuration
    if xray:
        lines.append("spec_show_xray 1")
    else:
        lines.extend([
            "spec_show_xray 0",
            "mirv_fix selectedPlayerGlow 0",
        ])

    # HUD configuration
    lines.extend(
        _build_hud_commands(
            hud_mode,
            hud_scale,
            overhead_mode=overhead_mode,
            killfeed_only=killfeed_only,
            teamcounter_mode=teamcounter_mode,
        )
    )

    spec_cmds = _build_spec_commands(account_id, pov_name)

    if output_dir and end_tick is not None:
        out_dir_str = str(output_dir.resolve()).replace("\\", "/")
        lines.extend([
            f'mirv_streams record name "{out_dir_str}"',
            f"mirv_streams record fps {fps}",
            "mirv_streams record screen enabled 1",
            "mirv_streams record screen settings afxFfmpegYuv420p",
            "mirv_cmd clear",
        ])

        radar_tick5 = "cl_radar_square_when_spectating 0; cl_radar_square_always 0; cl_radar_square_with_scoreboard 0"
        radar_rot_tick5 = "cl_radar_rotate 1; cl_radar_always_centered 1" if radar_mode == "player_focus" else None

        # Schedule initial seek forward if starting past early ticks
        if start_tick > 60:
            jump_tick = max(10, start_tick - jump_lead_ticks)
            lines.append(f'mirv_cmd addAtTick 5 "demo_gototick {jump_tick}; demo_resume"')
            lines.append(f'mirv_cmd addAtTick 5 "{radar_tick5}"')
            if radar_rot_tick5:
                lines.append(f'mirv_cmd addAtTick 5 "{radar_rot_tick5}"')

            if spec_cmds:
                lines.append(f'mirv_cmd addAtTick {jump_tick + 20} "{"; ".join(spec_cmds)}; demo_resume"')
        else:
            if spec_cmds:
                lines.append(f'mirv_cmd addAtTick 5 "{"; ".join(spec_cmds)}"')
            lines.append(f'mirv_cmd addAtTick 5 "{radar_tick5}"')
            if radar_rot_tick5:
                lines.append(f'mirv_cmd addAtTick 5 "{radar_rot_tick5}"')

        # Schedule highlight recording start and end with guaranteed TrueView & demo UI suppression
        if hud_mode == "real":
            lines.append(f'mirv_cmd addAtTick {start_tick} "hud_showtargetid 0; cl_hide_avatar_images 1; cl_teamid_overhead_mode 0"')
            lines.append(f'mirv_cmd addAtTick {start_tick} "cl_teamcounter_playercount_mode 1"')

        if radar_mode != "hidden":
            lines.append(f'mirv_cmd addAtTick {start_tick} "{radar_tick5}"')
            if radar_rot_tick5:
                lines.append(f'mirv_cmd addAtTick {start_tick} "{radar_rot_tick5}"')

        rec_start_parts = list(spec_cmds) + [
            "cl_trueview_show_status 0",
            "demo_ui_mode 0",
            "cl_spec_show_bindings 0",
            "mirv_streams record start",
        ]
        lines.append(f'mirv_cmd addAtTick {start_tick} "{"; ".join(rec_start_parts)}"')

        # Dynamic in-clip camera switches (e.g. dynamic switches during play)
        if camera_switches:
            for sw_tick, sw_steam, sw_name in sorted(camera_switches, key=lambda s: s[0]):
                if start_tick < sw_tick < end_tick:
                    sw_acc = steam64_to_account_id(sw_steam) if sw_steam else None
                    sw_cmds = _build_spec_commands(sw_acc, sw_name)
                    if sw_cmds:
                        lines.append(f'mirv_cmd addAtTick {sw_tick} "{"; ".join(sw_cmds)}"')

        lines.append(f'mirv_cmd addAtTick {end_tick} "mirv_streams record end; quit"')
    else:
        # Fallback demo_gototick and spec commands for direct playback compatibility
        lines.append(f"demo_gototick {start_tick}")
        lines.extend(spec_cmds)

    lines.append("demo_resume")
    lines.append("")

    content = "\n".join(lines)

    if output_cfg_path:
        output_cfg_path.parent.mkdir(parents=True, exist_ok=True)
        output_cfg_path.write_text(content, encoding="utf-8")

    return content


def generate_batch_render_cfg(
    clips: list[BatchClipItem],
    output_dir: pathlib.Path,
    output_cfg_path: Optional[pathlib.Path] = None,
    fps: int = 60,
    jump_lead_ticks: int = 20,
) -> str:
    """Generate a single CS2 .cfg file that records multiple highlight clips in ONE continuous game session.

    Clips must be sorted by start_tick in ascending order.
    HLAE will produce sequential takes: take0000, take0001, take0002...
    """
    if not clips:
        raise ValueError("At least one clip must be provided for batch render config")

    # Sort clips chronologically by earliest demo event (victim start if killcam replay, else start_tick)
    sorted_clips = sorted(
        clips,
        key=lambda c: (
            c.killcam_victim_start_tick
            if (c.is_killcam_replay and c.killcam_victim_start_tick is not None)
            else c.start_tick
        ),
    )

    for c in sorted_clips:
        if c.hud_mode == "real":
            if c.radar_mode == "broadcast":
                c.radar_mode = "player_focus"
            c.xray = False

    out_dir_str = str(output_dir.resolve()).replace("\\", "/")

    lines = [
        "// Generated by CS2 Highlights Studio — Batch Session",
        "sv_cheats 1",
        "engine_no_focus_sleep 0",
        "snd_mute_losefocus 0",
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
        "spec_mode 4",
        "safezonex 1.0",
        "safezoney 1.0",
    ]
    first_clip = sorted_clips[0]
    lines.extend(_build_radar_commands(first_clip.radar_mode))
    lines.extend([
        "cl_teamcounter_playercount_mode 0",
        "cl_hud_telemetry_frametime_show 0",
        "cl_hud_telemetry_net_misdelivery_show 0",
        "cl_hud_telemetry_ping_show 0",
        f'mirv_streams record name "{out_dir_str}"',
        f"mirv_streams record fps {fps}",
        "mirv_streams record screen enabled 1",
        "mirv_streams record screen settings afxFfmpegYuv420p",
        "mirv_cmd clear",
    ])

    # Global camera, crosshair, and HUD defaults from the first clip
    fov_cmds = _build_fov_commands(first_clip.fov, first_clip.viewmodel_fov)
    if fov_cmds:
        lines.extend(fov_cmds)

    if first_clip.custom_crosshair:
        lines.extend(_build_crosshair_commands(preset=first_clip.crosshair_preset, color=first_clip.crosshair_color))
    elif first_clip.crosshair_preset in ("hidden", "none"):
        lines.append("crosshair 0")

    if first_clip.xray:
        lines.append("spec_show_xray 1")
    else:
        lines.extend(["spec_show_xray 0", "mirv_fix selectedPlayerGlow 0"])

    lines.extend(
        _build_hud_commands(
            first_clip.hud_mode,
            getattr(first_clip, "hud_scale", None),
            overhead_mode=getattr(first_clip, "overhead_mode", None),
            killfeed_only=getattr(first_clip, "killfeed_only", None),
            teamcounter_mode=getattr(first_clip, "teamcounter_mode", None),
        )
    )

    radar_tick5 = "cl_radar_square_when_spectating 0; cl_radar_square_always 0; cl_radar_square_with_scoreboard 0"
    radar_rot_tick5 = "cl_radar_rotate 1; cl_radar_always_centered 1" if first_clip.radar_mode == "player_focus" else None

    for idx, clip in enumerate(sorted_clips):
        acc_id = steam64_to_account_id(clip.pov_steam_id) if clip.pov_steam_id else None
        spec_cmds = _build_spec_commands(acc_id, clip.pov_name)

        jump_tick = max(10, clip.start_tick - jump_lead_ticks)

        if idx == 0:
            # First clip: schedule initial seek at tick 5 with round radar enforced
            if clip.start_tick > 60:
                lines.append(f'mirv_cmd addAtTick 5 "demo_gototick {jump_tick}; demo_resume"')
                lines.append(f'mirv_cmd addAtTick 5 "{radar_tick5}"')
                if radar_rot_tick5:
                    lines.append(f'mirv_cmd addAtTick 5 "{radar_rot_tick5}"')
                if spec_cmds:
                    lines.append(f'mirv_cmd addAtTick {jump_tick + 20} "{"; ".join(spec_cmds)}; demo_resume"')
            else:
                if spec_cmds:
                    lines.append(f'mirv_cmd addAtTick 5 "{"; ".join(spec_cmds)}"')
                lines.append(f'mirv_cmd addAtTick 5 "{radar_tick5}"')
                if radar_rot_tick5:
                    lines.append(f'mirv_cmd addAtTick 5 "{radar_rot_tick5}"')

        # Start recording this clip with clean HUD & camera lock
        if clip.hud_mode == "real":
            lines.append(f'mirv_cmd addAtTick {clip.start_tick} "hud_showtargetid 0; cl_hide_avatar_images 1; cl_teamid_overhead_mode 0"')
            lines.append(f'mirv_cmd addAtTick {clip.start_tick} "cl_teamcounter_playercount_mode 1"')

        if clip.radar_mode != "hidden":
            clip_rot = "cl_radar_rotate 1; cl_radar_always_centered 1" if clip.radar_mode == "player_focus" else None
            lines.append(f'mirv_cmd addAtTick {clip.start_tick} "{radar_tick5}"')
            if clip_rot:
                lines.append(f'mirv_cmd addAtTick {clip.start_tick} "{clip_rot}"')

        start_parts = list(spec_cmds) + ["mirv_streams record start"]
        lines.append(f'mirv_cmd addAtTick {clip.start_tick} "{"; ".join(start_parts)}"')

        # Dynamic in-clip camera switches
        if clip.camera_switches:
            for sw_tick, sw_steam, sw_name in sorted(clip.camera_switches, key=lambda s: s[0]):
                if clip.start_tick < sw_tick < clip.end_tick:
                    sw_acc = steam64_to_account_id(sw_steam) if sw_steam else None
                    sw_cmds = _build_spec_commands(sw_acc, sw_name)
                    if sw_cmds:
                        lines.append(f'mirv_cmd addAtTick {sw_tick} "{"; ".join(sw_cmds)}"')

        # End recording for this clip
        if idx == len(sorted_clips) - 1:
            # Final clip: stop recording and quit CS2
            lines.append(f'mirv_cmd addAtTick {clip.end_tick} "mirv_streams record end; quit"')
        else:
            next_clip = sorted_clips[idx + 1]
            next_start = next_clip.start_tick
            next_jump = max(10, next_start - jump_lead_ticks)
            next_acc_id = steam64_to_account_id(next_clip.pov_steam_id)
            next_spec_cmds = _build_spec_commands(next_acc_id, next_clip.pov_name)

            if next_jump > clip.end_tick + 30:
                # Fast-forward jump forward directly to next clip lead-in
                lines.append(f'mirv_cmd addAtTick {clip.end_tick} "mirv_streams record end; demo_gototick {next_jump}; demo_resume"')
                if next_spec_cmds:
                    lines.append(f'mirv_cmd addAtTick {next_jump + 20} "{"; ".join(next_spec_cmds)}; demo_resume"')
            else:
                # Seamless transition between closely spaced highlights
                lines.append(f'mirv_cmd addAtTick {clip.end_tick} "mirv_streams record end; demo_resume"')
                prep_tick = max(clip.end_tick + 1, next_start - 15)
                if next_spec_cmds and prep_tick < next_start:
                    lines.append(f'mirv_cmd addAtTick {prep_tick} "{"; ".join(next_spec_cmds)}; demo_resume"')

    lines.append("demo_resume")
    lines.append("")

    content = "\n".join(lines)
    if output_cfg_path:
        output_cfg_path.parent.mkdir(parents=True, exist_ok=True)
        output_cfg_path.write_text(content, encoding="utf-8")

    return content
