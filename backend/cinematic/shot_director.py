"""Automatic Shot Director for dem.Toshka Cinematic Studio.

Scores highlights using multi-factor gameplay intelligence and plans
cinematic camera choreography without redundant camera overhead.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from backend.cinematic.camera_library import (
    generate_establishing_camera_path,
    generate_flyby_camera_path,
    generate_orbit_camera_path,
    generate_shoulder_cam_path,
    generate_top_down_camera_path,
)
from backend.cinematic.models import (
    CameraPath,
    CameraType,
    CinematicShot,
    OverlayKillEvent,
    Rotation3,
    ShotPurpose,
    Vector3,
)


class HighlightScorer:
    """Configurable gameplay highlight evaluation and scoring engine."""

    def __init__(
        self,
        weight_ace: float = 100.0,
        weight_4k: float = 75.0,
        weight_3k: float = 50.0,
        weight_2k: float = 25.0,
        weight_clutch_per_enemy: float = 30.0,
        weight_headshot: float = 8.0,
        weight_wallbang: float = 18.0,
        weight_noscope: float = 22.0,
        weight_thrusmoke: float = 18.0,
        weight_inair: float = 15.0,
        weight_blind: float = 15.0,
        weight_flick: float = 20.0,
    ):
        self.weight_ace = weight_ace
        self.weight_4k = weight_4k
        self.weight_3k = weight_3k
        self.weight_2k = weight_2k
        self.weight_clutch_per_enemy = weight_clutch_per_enemy
        self.weight_headshot = weight_headshot
        self.weight_wallbang = weight_wallbang
        self.weight_noscope = weight_noscope
        self.weight_thrusmoke = weight_thrusmoke
        self.weight_inair = weight_inair
        self.weight_blind = weight_blind
        self.weight_flick = weight_flick

    def score_highlight(
        self,
        highlight_type: str,
        kills: list[dict[str, Any]],
        is_clutch: bool = False,
        clutch_enemies: int = 0,
        has_flick: bool = False,
    ) -> float:
        score = 0.0
        htype = highlight_type.lower()
        if "ace" in htype:
            score += self.weight_ace
        elif "4k" in htype:
            score += self.weight_4k
        elif "3k" in htype or "triple" in htype:
            score += self.weight_3k
        elif "2k" in htype or "double" in htype:
            score += self.weight_2k
        else:
            score += 10.0

        if is_clutch and clutch_enemies > 0:
            score += self.weight_clutch_per_enemy * clutch_enemies

        for k in kills:
            if k.get("headshot"):
                score += self.weight_headshot
            if k.get("wallbang") or k.get("penetrated", 0) > 0:
                score += self.weight_wallbang
            if k.get("noscope"):
                score += self.weight_noscope
            if k.get("thrusmoke"):
                score += self.weight_thrusmoke
            if k.get("attackerblind"):
                score += self.weight_blind
            if k.get("attackerinair"):
                score += self.weight_inair

        if has_flick:
            score += self.weight_flick

        return round(score, 1)


def detect_quick_flick(
    player_ticks: list[dict[str, Any]],
    kill_tick: int,
    window_ticks: int = 16,
    threshold_deg_per_tick: float = 7.0,
) -> bool:
    """Detect authentic quick flick based on real view angle velocity before kill."""
    if not player_ticks:
        return False

    relevant = [
        t for t in player_ticks
        if (kill_tick - window_ticks) <= t.get("tick", 0) <= kill_tick
    ]
    if len(relevant) < 2:
        return False

    sorted_ticks = sorted(relevant, key=lambda t: t.get("tick", 0))
    for i in range(1, len(sorted_ticks)):
        prev = sorted_ticks[i - 1]
        curr = sorted_ticks[i]
        dt = curr.get("tick", 0) - prev.get("tick", 0)
        if dt <= 0:
            continue

        dyaw = abs(float(curr.get("yaw", 0.0)) - float(prev.get("yaw", 0.0)))
        # Handle 180 wrap-around
        if dyaw > 180.0:
            dyaw = 360.0 - dyaw
        dpitch = abs(float(curr.get("pitch", 0.0)) - float(prev.get("pitch", 0.0)))

        angular_dist = math.sqrt(dyaw * dyaw + dpitch * dpitch)
        rate = angular_dist / dt
        if rate >= threshold_deg_per_tick:
            return True

    return False


class AutomaticShotDirector:
    """Directs camera choices and choreography for each highlight moment."""

    def __init__(self, scorer: Optional[HighlightScorer] = None):
        self.scorer = scorer or HighlightScorer()

    def plan_shots_for_highlight(
        self,
        highlight_id: str,
        round_number: int,
        start_tick: int,
        end_tick: int,
        hero_steam_id: str,
        hero_name: str,
        kills: list[dict[str, Any]],
        highlight_type: str = "multikill",
        player_ticks: Optional[list[dict[str, Any]]] = None,
        tickrate: int = 128,
        fps: int = 60,
    ) -> list[CinematicShot]:
        """Plan choreography of camera shots for a highlight."""
        shots: list[CinematicShot] = []
        htype = highlight_type.lower()
        duration_ticks = end_tick - start_tick
        total_seconds = duration_ticks / float(tickrate)
        lead_in_ticks = int(tickrate * 2.0)
        outro_ticks = int(tickrate * 2.0)

        # 1. Main Action Hero POV (Always preserved as Master Track)
        shots.append(
            CinematicShot(
                shot_id=f"{highlight_id}_hero_pov",
                highlight_id=highlight_id,
                round_number=round_number,
                camera_type=CameraType.FIRST_PERSON,
                purpose=ShotPurpose.PRIMARY_ACTION,
                start_tick=start_tick,
                end_tick=end_tick,
                start_time=start_tick / float(tickrate),
                end_time=end_tick / float(tickrate),
                duration_seconds=total_seconds,
                fov=90.0,
                pov_steam_id=hero_steam_id,
                pov_name=hero_name,
                focus_target_name=hero_name,
                focus_target_steam_id=hero_steam_id,
                output_filename=f"shot_{highlight_id}_01_hero_pov.mp4",
                fps=fps,
            )
        )

        # Extract primary victim if available
        first_victim = kills[0] if kills else None
        has_wallbang = any(k.get("wallbang") or k.get("penetrated", 0) > 0 for k in kills)
        is_ace = "ace" in htype or len(kills) >= 5
        is_clutch = "clutch" in htype

        # 2. Add Victim POV insert if dramatic (Wallbang, Ace final kill, or Headshot duel)
        if first_victim and (has_wallbang or is_ace or len(kills) >= 3):
            vic_steam = str(first_victim.get("victim_steamid") or first_victim.get("user_steamid") or "")
            vic_name = str(first_victim.get("victim_name") or first_victim.get("user_name") or "Victim")
            v_kill_tick = int(first_victim.get("tick", start_tick))

            v_start = max(start_tick, v_kill_tick - int(tickrate * 1.5))
            v_end = min(end_tick, v_kill_tick + int(tickrate * 0.8))

            shots.append(
                CinematicShot(
                    shot_id=f"{highlight_id}_victim_insert",
                    highlight_id=highlight_id,
                    round_number=round_number,
                    camera_type=CameraType.VICTIM_POV,
                    purpose=ShotPurpose.VICTIM_REACTION,
                    start_tick=v_start,
                    end_tick=v_end,
                    start_time=v_start / float(tickrate),
                    end_time=v_end / float(tickrate),
                    duration_seconds=(v_end - v_start) / float(tickrate),
                    fov=90.0,
                    pov_steam_id=vic_steam,
                    pov_name=vic_name,
                    focus_target_name=vic_name,
                    focus_target_steam_id=vic_steam,
                    output_filename=f"shot_{highlight_id}_02_victim_insert.mp4",
                    fps=fps,
                )
            )

        # 3. Third-person Chase or Shoulder Cam for dynamic approach
        if (is_ace or is_clutch or len(kills) >= 3) and player_ticks:
            approach_start = max(0, start_tick - lead_in_ticks)
            approach_end = min(end_tick, start_tick + int(tickrate * 1.5))
            relevant_ticks = [
                t for t in player_ticks
                if approach_start <= t.get("tick", 0) <= approach_end
            ]

            if len(relevant_ticks) >= 4:
                shoulder_path = generate_shoulder_cam_path(
                    relevant_ticks,
                    tickrate=tickrate,
                    fov=95.0,
                )
                shots.append(
                    CinematicShot(
                        shot_id=f"{highlight_id}_shoulder_approach",
                        highlight_id=highlight_id,
                        round_number=round_number,
                        camera_type=CameraType.SHOULDER_CAM,
                        purpose=ShotPurpose.APPROACH,
                        start_tick=approach_start,
                        end_tick=approach_end,
                        start_time=approach_start / float(tickrate),
                        end_time=approach_end / float(tickrate),
                        duration_seconds=(approach_end - approach_start) / float(tickrate),
                        fov=95.0,
                        campath=shoulder_path,
                        focus_target_name=hero_name,
                        focus_target_steam_id=hero_steam_id,
                        output_filename=f"shot_{highlight_id}_03_shoulder_approach.mp4",
                        fps=fps,
                    )
                )

        # 4. Establishing Shot or Orbit Camera for Ace / Clutch Outro
        if is_ace or is_clutch:
            first_kill = kills[0] if kills else {}
            hx = float(first_kill.get("attacker_X") or first_kill.get("X") or 0.0)
            hy = float(first_kill.get("attacker_Y") or first_kill.get("Y") or 0.0)
            hz = float(first_kill.get("attacker_Z") or first_kill.get("Z") or 0.0)
            center = Vector3(x=hx, y=hy, z=hz)

            orbit_start = end_tick - outro_ticks
            orbit_end = end_tick + int(tickrate * 1.0)
            orbit_path = generate_orbit_camera_path(
                center_pos=center,
                start_tick=orbit_start,
                end_tick=orbit_end,
                tickrate=tickrate,
                radius=190.0,
                height=50.0,
                arc_degrees=80.0,
                fov=85.0,
            )
            shots.append(
                CinematicShot(
                    shot_id=f"{highlight_id}_climax_orbit",
                    highlight_id=highlight_id,
                    round_number=round_number,
                    camera_type=CameraType.ORBIT_CAMERA,
                    purpose=ShotPurpose.CLIMAX_ACCENT,
                    start_tick=orbit_start,
                    end_tick=orbit_end,
                    start_time=orbit_start / float(tickrate),
                    end_time=orbit_end / float(tickrate),
                    duration_seconds=(orbit_end - orbit_start) / float(tickrate),
                    fov=85.0,
                    campath=orbit_path,
                    focus_target_name=hero_name,
                    focus_target_steam_id=hero_steam_id,
                    output_filename=f"shot_{highlight_id}_04_climax_orbit.mp4",
                    fps=fps,
                )
            )

        return shots
