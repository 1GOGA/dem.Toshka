"""Automatic Shot Director for dem.Toshka Cinematic Studio.

Scores highlights using multi-factor gameplay intelligence and plans
cinematic camera choreography without redundant camera overhead.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
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


@dataclass
class CameraQualityReport:
    """Detailed quality, framing, and safety evaluation for a cinematic camera shot."""

    shot_id: str
    camera_type: CameraType
    score: float  # 0.0 - 100.0
    player_visibility: float  # 0.0 - 1.0
    victim_visibility: float  # 0.0 - 1.0
    camera_distance: float  # Estimated units from subject
    fov_suitability: float  # 0.0 - 1.0
    trajectory_smoothness: float  # 0.0 - 1.0
    clipping_risk: bool = False
    wall_proximity_est: float = 120.0
    status: str = "VERIFIED"  # "VERIFIED", "EXPERIMENTAL", "NEEDS_PREVIEW_REVIEW", "REJECTED"
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CameraQualityScorer:
    """Evaluates camera shots for visibility, framing, trajectory smoothness, and clipping risk."""

    def score_shot(
        self,
        shot: CinematicShot,
        hero_pos: Optional[Vector3] = None,
        victim_pos: Optional[Vector3] = None,
        corridor_narrow: bool = False,
    ) -> CameraQualityReport:
        cam_type = shot.camera_type
        player_vis = 1.0
        victim_vis = 0.5
        cam_dist = 0.0
        fov_suit = 1.0
        smoothness = 1.0
        clipping_risk = False
        wall_prox = 150.0
        status = "VERIFIED"
        recommendations: list[str] = []

        # 1. FOV Suitability (CS2 sweet spot: 70 - 105 degrees)
        if shot.fov < 65.0 or shot.fov > 110.0:
            fov_suit = 0.7
            recommendations.append(f"Unusual FOV {shot.fov:.1f}deg; standard CS2 cinematic FOV is 75-95deg.")
        else:
            fov_suit = 1.0

        # 2. Camera-type specific physical safety & framing evaluation
        if cam_type == CameraType.FIRST_PERSON:
            # Native in-engine player model view: 0% clipping risk, 100% player perspective
            cam_dist = 0.0
            player_vis = 1.0
            victim_vis = 0.8
            status = "VERIFIED"

        elif cam_type == CameraType.VICTIM_POV:
            # Native in-engine victim model view: 0% clipping risk
            cam_dist = 0.0
            player_vis = 0.6
            victim_vis = 1.0
            status = "VERIFIED"

        elif cam_type == CameraType.SHOULDER_CAM:
            # Over-the-shoulder dynamic spline: EXPERIMENTAL until full mesh raycasting in Source 2
            cam_dist = 50.0
            player_vis = 0.95
            status = "EXPERIMENTAL"
            wall_prox = 45.0 if corridor_narrow else 90.0

            if corridor_narrow:
                clipping_risk = True
                recommendations.append(
                    "Narrow corridor detected: applied conservative fallback offset (dist_right=10.0) to prevent wall penetration."
                )
            else:
                recommendations.append("Experimental shoulder cam: Quake spline follows player yaw smoothly.")

        elif cam_type == CameraType.FREECAM_FLYBY:
            cam_dist = 180.0
            wall_prox = 70.0
            if corridor_narrow:
                clipping_risk = True
                status = "NEEDS_PREVIEW_REVIEW"
                recommendations.append(
                    "Freecam path traverses restricted sector: marked for preview review due to potential ceiling/wall proximity."
                )
            else:
                status = "VERIFIED"

        elif cam_type == CameraType.ORBIT_CAMERA:
            cam_dist = 190.0
            wall_prox = 110.0
            status = "VERIFIED"
            player_vis = 0.9

        elif cam_type == CameraType.ESTABLISHING_SHOT:
            cam_dist = 480.0
            wall_prox = 250.0
            status = "VERIFIED"
            player_vis = 0.75

        elif cam_type == CameraType.TOP_DOWN:
            cam_dist = 550.0
            wall_prox = 300.0
            status = "VERIFIED"
            player_vis = 0.8

        # 3. Trajectory smoothness check on campath
        if shot.campath and len(shot.campath.points) >= 2:
            pts = shot.campath.points
            max_vel = 0.0
            for i in range(1, len(pts)):
                dt = max(1e-4, pts[i].time - pts[i - 1].time)
                dx = pts[i].position.x - pts[i - 1].position.x
                dy = pts[i].position.y - pts[i - 1].position.y
                dz = pts[i].position.z - pts[i - 1].position.z
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                vel = dist / dt
                if vel > max_vel:
                    max_vel = vel

            # High velocity or acceleration jerk check
            if max_vel > 1200.0:  # > 1200 units/sec is very fast for cinematic cam
                smoothness = 0.75
                recommendations.append(f"High camera speed ({max_vel:.0f} units/s); review spline pacing.")
            else:
                smoothness = 0.98

        # Compute composite quality score (0 - 100)
        base_score = (
            player_vis * 35.0
            + fov_suit * 25.0
            + smoothness * 25.0
            + (15.0 if not clipping_risk else 5.0)
        )
        final_score = round(max(0.0, min(100.0, base_score)), 1)

        return CameraQualityReport(
            shot_id=shot.shot_id,
            camera_type=cam_type,
            score=final_score,
            player_visibility=player_vis,
            victim_visibility=victim_vis,
            camera_distance=round(cam_dist, 1),
            fov_suitability=fov_suit,
            trajectory_smoothness=smoothness,
            clipping_risk=clipping_risk,
            wall_proximity_est=round(wall_prox, 1),
            status=status,
            recommendations=recommendations,
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

        # Apply camera quality scoring
        quality_scorer = CameraQualityScorer()
        for s in shots:
            report = quality_scorer.score_shot(s)
            s.quality_score = report.score
            s.clipping_risk = report.clipping_risk
            s.quality_status = report.status

        return shots


@dataclass
class NarrativePacingDecision:
    """Narrative direction and pacing analysis for highlight editing."""

    highlight_id: str
    dramatic_intensity: float  # 0.0 - 1.0
    rapid_multikill: bool  # fast bursts where First-Person POV must NOT be cut away
    slow_motion_segments: list[dict[str, Any]] = field(default_factory=list)
    selected_shots: list[CinematicShot] = field(default_factory=list)
    discarded_cameras: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "highlight_id": self.highlight_id,
            "dramatic_intensity": round(self.dramatic_intensity, 2),
            "rapid_multikill": self.rapid_multikill,
            "slow_motion_segments": self.slow_motion_segments,
            "selected_shots": [s.to_dict() for s in self.selected_shots],
            "discarded_cameras": self.discarded_cameras,
        }


class CinematicDirectorV2(AutomaticShotDirector):
    """Cinematic Director V2: Advanced narrative choreography, camera quality scoring,
    clipping mitigation, and purposeful montage planning.
    
    Never generates all 8 camera angles by default; selects only purposeful takes
    that elevate storytelling and gameplay momentum.
    """

    def __init__(
        self,
        scorer: Optional[HighlightScorer] = None,
        quality_scorer: Optional[CameraQualityScorer] = None,
    ):
        super().__init__(scorer=scorer)
        self.quality_scorer = quality_scorer or CameraQualityScorer()

    def plan_cinematic_production(
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
        map_name: str = "de_anubis",
        corridor_narrow: bool = False,
    ) -> NarrativePacingDecision:
        """Create a complete narrative production plan with quality verification."""
        selected_shots: list[CinematicShot] = []
        discarded: list[dict[str, str]] = []
        slow_mo_segments: list[dict[str, Any]] = []

        total_duration_sec = (end_tick - start_tick) / float(tickrate)
        htype = highlight_type.lower()
        is_ace = "ace" in htype or len(kills) >= 5
        is_clutch = "clutch" in htype

        # 1. Pacing & Burst Analysis
        sorted_kills = sorted(kills, key=lambda k: int(k.get("tick", 0)))
        rapid_multikill = False
        if len(sorted_kills) >= 2:
            intervals = [
                (sorted_kills[i]["tick"] - sorted_kills[i - 1]["tick"]) / float(tickrate)
                for i in range(1, len(sorted_kills))
            ]
            if any(dt < 1.2 for dt in intervals):
                rapid_multikill = True

        # Calculate dramatic intensity based on kills, headshots, wallbangs
        hs_count = sum(1 for k in kills if k.get("headshot"))
        wb_count = sum(1 for k in kills if k.get("wallbang") or k.get("penetrated", 0) > 0)
        intensity = min(1.0, 0.4 + (len(kills) * 0.1) + (hs_count * 0.08) + (wb_count * 0.12))

        # 2. Track V1: Master Hero POV (Continuous Primary Backbone)
        hero_shot = CinematicShot(
            shot_id=f"{highlight_id}_hero_pov",
            highlight_id=highlight_id,
            round_number=round_number,
            camera_type=CameraType.FIRST_PERSON,
            purpose=ShotPurpose.PRIMARY_ACTION,
            start_tick=start_tick,
            end_tick=end_tick,
            start_time=start_tick / float(tickrate),
            end_time=end_tick / float(tickrate),
            duration_seconds=total_duration_sec,
            fov=90.0,
            pov_steam_id=hero_steam_id,
            pov_name=hero_name,
            focus_target_name=hero_name,
            focus_target_steam_id=hero_steam_id,
            output_filename=f"shot_{highlight_id}_01_hero_pov.mp4",
            fps=fps,
        )
        report = self.quality_scorer.score_shot(hero_shot, corridor_narrow=corridor_narrow)
        hero_shot.quality_score = report.score
        hero_shot.clipping_risk = report.clipping_risk
        hero_shot.quality_status = report.status
        selected_shots.append(hero_shot)

        # 3. Track V2: Cinematic Approach / Establishing Shot (Lead-in Setup)
        lead_in_ticks = int(tickrate * 2.5)
        approach_start = max(0, start_tick - lead_in_ticks)
        first_kill_tick = sorted_kills[0].get("tick", start_tick) if sorted_kills else start_tick

        if (first_kill_tick - start_tick) > int(tickrate * 1.5) or is_ace or is_clutch:
            if player_ticks:
                relevant = [t for t in player_ticks if approach_start <= t.get("tick", 0) <= first_kill_tick]
                if len(relevant) >= 4:
                    # Apply conservative fallback if corridor_narrow
                    shoulder_path = generate_shoulder_cam_path(
                        relevant,
                        tickrate=tickrate,
                        fov=92.0,
                        conservative_fallback=corridor_narrow,
                    )
                    approach_shot = CinematicShot(
                        shot_id=f"{highlight_id}_shoulder_approach",
                        highlight_id=highlight_id,
                        round_number=round_number,
                        camera_type=CameraType.SHOULDER_CAM,
                        purpose=ShotPurpose.APPROACH,
                        start_tick=approach_start,
                        end_tick=first_kill_tick,
                        start_time=approach_start / float(tickrate),
                        end_time=first_kill_tick / float(tickrate),
                        duration_seconds=(first_kill_tick - approach_start) / float(tickrate),
                        fov=92.0,
                        campath=shoulder_path,
                        focus_target_name=hero_name,
                        focus_target_steam_id=hero_steam_id,
                        output_filename=f"shot_{highlight_id}_02_shoulder_approach.mp4",
                        fps=fps,
                    )
                    app_report = self.quality_scorer.score_shot(approach_shot, corridor_narrow=corridor_narrow)
                    approach_shot.quality_score = app_report.score
                    approach_shot.clipping_risk = app_report.clipping_risk
                    approach_shot.quality_status = app_report.status
                    selected_shots.append(approach_shot)
            elif sorted_kills:
                # Open establishing crane if no player ticks
                k0 = sorted_kills[0]
                kx = float(k0.get("attacker_X") or k0.get("X") or 0.0)
                ky = float(k0.get("attacker_Y") or k0.get("Y") or 0.0)
                kz = float(k0.get("attacker_Z") or k0.get("Z") or 0.0)
                est_path = generate_establishing_camera_path(
                    area_center=Vector3(kx, ky, kz),
                    start_tick=approach_start,
                    end_tick=first_kill_tick,
                    tickrate=tickrate,
                    elevation=280.0,
                    distance=420.0,
                )
                est_shot = CinematicShot(
                    shot_id=f"{highlight_id}_establishing_intro",
                    highlight_id=highlight_id,
                    round_number=round_number,
                    camera_type=CameraType.ESTABLISHING_SHOT,
                    purpose=ShotPurpose.ESTABLISH,
                    start_tick=approach_start,
                    end_tick=first_kill_tick,
                    start_time=approach_start / float(tickrate),
                    end_time=first_kill_tick / float(tickrate),
                    duration_seconds=(first_kill_tick - approach_start) / float(tickrate),
                    fov=80.0,
                    campath=est_path,
                    output_filename=f"shot_{highlight_id}_02_establishing_intro.mp4",
                    fps=fps,
                )
                est_report = self.quality_scorer.score_shot(est_shot, corridor_narrow=corridor_narrow)
                est_shot.quality_score = est_report.score
                est_shot.clipping_risk = est_report.clipping_risk
                est_shot.quality_status = est_report.status
                selected_shots.append(est_shot)

        # 4. Track V3: High-Impact Victim POV Reaction (Exactly 1 targeted insert)
        # Select the single most dramatic kill (prioritize wallbang, then headshot, then final kill)
        dramatic_victim: Optional[dict[str, Any]] = None
        for k in sorted_kills:
            if k.get("wallbang") or k.get("penetrated", 0) > 0:
                dramatic_victim = k
                break
        if not dramatic_victim:
            for k in sorted_kills:
                if k.get("headshot"):
                    dramatic_victim = k
                    break
        if not dramatic_victim and sorted_kills:
            dramatic_victim = sorted_kills[-1]

        if dramatic_victim:
            vic_steam = str(dramatic_victim.get("victim_steamid") or dramatic_victim.get("user_steamid") or "")
            vic_name = str(dramatic_victim.get("victim_name") or dramatic_victim.get("user_name") or "Victim")
            v_kill_tick = int(dramatic_victim.get("tick", start_tick))

            # 1.4s window around impact
            v_start = max(start_tick, v_kill_tick - int(tickrate * 0.9))
            v_end = min(end_tick, v_kill_tick + int(tickrate * 0.6))

            vic_shot = CinematicShot(
                shot_id=f"{highlight_id}_victim_reaction",
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
                output_filename=f"shot_{highlight_id}_03_victim_reaction.mp4",
                fps=fps,
            )
            v_report = self.quality_scorer.score_shot(vic_shot, corridor_narrow=corridor_narrow)
            vic_shot.quality_score = v_report.score
            vic_shot.clipping_risk = v_report.clipping_risk
            vic_shot.quality_status = v_report.status
            selected_shots.append(vic_shot)

        # 5. Outro Climax: Orbit Camera for Ace / Clutch celebration (Track V2)
        if (is_ace or is_clutch or len(kills) >= 4) and sorted_kills:
            last_kill = sorted_kills[-1]
            lx = float(last_kill.get("attacker_X") or last_kill.get("X") or 0.0)
            ly = float(last_kill.get("attacker_Y") or last_kill.get("Y") or 0.0)
            lz = float(last_kill.get("attacker_Z") or last_kill.get("Z") or 0.0)
            last_tick = int(last_kill.get("tick", end_tick))

            orbit_start = max(start_tick, last_tick - int(tickrate * 0.5))
            orbit_end = min(end_tick + int(tickrate * 1.5), last_tick + int(tickrate * 2.5))
            orbit_path = generate_orbit_camera_path(
                center_pos=Vector3(x=lx, y=ly, z=lz),
                start_tick=orbit_start,
                end_tick=orbit_end,
                tickrate=tickrate,
                radius=175.0,
                height=45.0,
                arc_degrees=70.0,
                fov=85.0,
            )
            orbit_shot = CinematicShot(
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
            orb_report = self.quality_scorer.score_shot(orbit_shot, corridor_narrow=corridor_narrow)
            orbit_shot.quality_score = orb_report.score
            orbit_shot.clipping_risk = orb_report.clipping_risk
            orbit_shot.quality_status = orb_report.status
            selected_shots.append(orbit_shot)

        # 6. Explicitly Document Discarded Cameras (Director's Editorial Log)
        discarded.append({
            "camera_type": CameraType.TOP_DOWN.value,
            "reason": "Top-down perspective abstracts combat emotions; reserved strictly for 2D tactical analysis.",
        })
        discarded.append({
            "camera_type": CameraType.THIRD_PERSON_CHASE.value,
            "reason": "Redundant with Shoulder Cam; shoulder framing provides tighter weapon alignment.",
        })
        if any(s.camera_type == CameraType.ORBIT_CAMERA for s in selected_shots):
            discarded.append({
                "camera_type": CameraType.FREECAM_FLYBY.value,
                "reason": "Orbit camera selected for outro; additional flyby would dilute climax focus.",
            })
        if len(kills) > 1:
            discarded.append({
                "camera_type": "SECONDARY_VICTIM_POVS",
                "reason": f"Discarded {len(kills)-1} additional victim cameras to avoid montage visual whiplash.",
            })

        # 7. Slow-Motion Segments for Key Impacts
        for k in sorted_kills:
            if k.get("headshot") or k.get("wallbang"):
                ktick = int(k.get("tick", 0))
                slow_mo_segments.append({
                    "tick": ktick,
                    "time_seconds": ktick / float(tickrate),
                    "victim_name": k.get("victim_name", "Target"),
                    "weapon": k.get("weapon", "rifle"),
                    "start_tick": ktick - int(tickrate * 0.25),
                    "end_tick": ktick + int(tickrate * 0.35),
                    "timescale": 0.40,  # 40% slowmo impact
                    "reason": "Headshot / Penetration critical impact accent",
                })

        return NarrativePacingDecision(
            highlight_id=highlight_id,
            dramatic_intensity=intensity,
            rapid_multikill=rapid_multikill,
            slow_motion_segments=slow_mo_segments,
            selected_shots=selected_shots,
            discarded_cameras=discarded,
        )
