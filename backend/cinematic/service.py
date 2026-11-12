"""Cinematic Studio Service.

Coordinates database models, highlight scoring, AI shot planning,
and production package creation for the API layer.
"""

from __future__ import annotations

import json
import pathlib
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.cinematic.camera_library import (
    generate_establishing_camera_path,
    generate_flyby_camera_path,
    generate_orbit_camera_path,
    generate_shoulder_cam_path,
    generate_top_down_camera_path,
)
from backend.cinematic.campath_generator import export_campath_xml
from backend.cinematic.manifest_manager import write_manifests
from backend.cinematic.models import (
    CameraPath,
    CameraType,
    CampathPoint,
    CinematicProductionPackage,
    CinematicShot,
    EditDecisionClip,
    InterpolationMode,
    OverlayKillEvent,
    Rotation3,
    ShotPurpose,
    Vector3,
)
from backend.cinematic.overlay_generator import export_svg_killfeed
from backend.cinematic.resolve_export import generate_cmx3600_edl, generate_fcpxml
from backend.cinematic.shot_director import AutomaticShotDirector, HighlightScorer
from backend.render.config import RENDER_OUTPUT_DIR
from backend.storage.repository import DemoRepository


class CinematicService:
    """Business logic coordinator for dem.Toshka Cinematic Studio."""

    def __init__(self, output_root: pathlib.Path = RENDER_OUTPUT_DIR):
        self.output_root = output_root
        self.scorer = HighlightScorer()
        self.director = AutomaticShotDirector(scorer=self.scorer)

    def get_ranked_highlights(self, session: Session, demo_id: int) -> list[dict[str, Any]]:
        """Fetch all highlights for demo and rank them by gameplay intensity."""
        repo = DemoRepository(session)
        demo = repo.get_by_id(demo_id)
        if not demo:
            return []

        raw_highlights = repo.get_highlights(demo_id)
        all_kills = repo.get_kills(demo_id)

        # Index kills by round
        kills_by_round: dict[int, list[Any]] = {}
        for k in all_kills:
            kills_by_round.setdefault(k.round_num, []).append(k)

        results: list[dict[str, Any]] = []

        for hl in raw_highlights:
            r_kills = kills_by_round.get(hl.round_num, [])
            hl_kills: list[dict[str, Any]] = []
            s_tick = getattr(hl, "clip_start_tick", getattr(hl, "start_tick", 0))
            e_tick = getattr(hl, "clip_end_tick", getattr(hl, "end_tick", 0))

            for k in r_kills:
                # Include kills belonging to this highlight interval and POV
                if s_tick <= k.tick <= e_tick:
                    if not hl.pov_steam_id or str(k.attacker_steam_id) == str(hl.pov_steam_id):
                        hl_kills.append({
                            "tick": k.tick,
                            "attacker_name": k.attacker_name,
                            "attacker_steamid": k.attacker_steam_id,
                            "victim_name": k.victim_name,
                            "victim_steamid": k.victim_steam_id,
                            "weapon": k.weapon,
                            "headshot": bool(k.headshot),
                            "wallbang": bool(getattr(k, "wallbang", getattr(k, "penetrated", False))),
                            "penetrated": 1 if bool(getattr(k, "wallbang", getattr(k, "penetrated", False))) else 0,
                            "noscope": bool(getattr(k, "noscope", False)),
                            "thrusmoke": bool(getattr(k, "thrusmoke", False)),
                            "attackerblind": bool(getattr(k, "attackerblind", False)),
                            "attackerinair": bool(getattr(k, "attackerinair", False)),
                        })

            is_clutch = "clutch" in (hl.highlight_type or "").lower()
            clutch_enemies = 1 if is_clutch else 0
            if is_clutch and "1v" in (hl.highlight_type or "").lower():
                try:
                    part = (hl.highlight_type or "").lower().split("1v")[1]
                    clutch_enemies = int(part[0])
                except Exception:
                    clutch_enemies = 2

            score = self.scorer.score_highlight(
                highlight_type=hl.highlight_type or "multikill",
                kills=hl_kills,
                is_clutch=is_clutch,
                clutch_enemies=clutch_enemies,
            )

            results.append({
                "id": hl.id,
                "demo_id": hl.demo_id,
                "highlight_type": hl.highlight_type,
                "round_num": hl.round_num,
                "start_tick": s_tick,
                "end_tick": e_tick,
                "kill_start_tick": hl.kill_start_tick,
                "kill_end_tick": hl.kill_end_tick,
                "pov_steam_id": hl.pov_steam_id,
                "pov_name": hl.pov_name,
                "score": score,
                "kills_count": len(hl_kills),
                "kills": hl_kills,
                "has_headshot": any(k["headshot"] for k in hl_kills),
                "has_wallbang": any(k["wallbang"] for k in hl_kills),
                "is_ace": "ace" in (hl.highlight_type or "").lower() or len(hl_kills) >= 5,
                "is_clutch": is_clutch,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def plan_cinematic_shots(
        self,
        session: Session,
        demo_id: int,
        highlight_ids: list[str],
        fps: int = 60,
    ) -> list[dict[str, Any]]:
        """Create structured camera shot plan for selected highlights."""
        repo = DemoRepository(session)
        demo = repo.get_by_id(demo_id)
        if not demo:
            return []

        demo_path = pathlib.Path(getattr(demo, "file_path", getattr(demo, "source_path", "match.dem")))
        all_planned_shots: list[CinematicShot] = []

        # Optional demoparser2 tick extractor if demo exists locally
        dp = None
        if demo_path.is_file():
            try:
                import demoparser2
                dp = demoparser2.DemoParser(str(demo_path))
            except Exception:
                dp = None

        tickrate = 128  # Default or extract from demo

        for hl_id in highlight_ids:
            hl = repo.get_highlight_by_id(hl_id)
            if not hl:
                continue

            s_tick = getattr(hl, "clip_start_tick", getattr(hl, "start_tick", 0))
            e_tick = getattr(hl, "clip_end_tick", getattr(hl, "end_tick", 0))

            r_kills = repo.get_kills(demo_id, round_num=hl.round_num)
            hl_kills: list[dict[str, Any]] = []
            for k in r_kills:
                if s_tick <= k.tick <= e_tick:
                    if not hl.pov_steam_id or str(k.attacker_steam_id) == str(hl.pov_steam_id):
                        hl_kills.append({
                            "tick": k.tick,
                            "attacker_name": k.attacker_name,
                            "attacker_steamid": k.attacker_steam_id,
                            "victim_name": k.victim_name,
                            "victim_steamid": k.victim_steam_id,
                            "weapon": k.weapon,
                            "headshot": bool(k.headshot),
                            "wallbang": bool(getattr(k, "wallbang", getattr(k, "penetrated", False))),
                            "penetrated": 1 if bool(getattr(k, "wallbang", getattr(k, "penetrated", False))) else 0,
                        })

            # Extract player coordinates if demo is accessible
            player_ticks: list[dict[str, Any]] = []
            if dp and hl.pov_steam_id:
                try:
                    p_start = max(0, s_tick - 128)
                    p_end = e_tick + 64
                    sampled_ticks = list(range(p_start, p_end + 1, 8))
                    t_df = dp.parse_ticks(["X", "Y", "Z", "pitch", "yaw"], ticks=sampled_ticks)
                    s_int = int(hl.pov_steam_id)
                    p_df = t_df[t_df["steamid"] == s_int]
                    player_ticks = p_df.to_dict("records")
                except Exception:
                    player_ticks = []

            shots = self.director.plan_shots_for_highlight(
                highlight_id=hl.id,
                round_number=hl.round_num,
                start_tick=s_tick,
                end_tick=e_tick,
                hero_steam_id=hl.pov_steam_id or "",
                hero_name=hl.pov_name or "Hero",
                kills=hl_kills,
                highlight_type=hl.highlight_type or "multikill",
                player_ticks=player_ticks,
                tickrate=tickrate,
                fps=fps,
            )
            all_planned_shots.extend(shots)

        return [s.to_dict() for s in all_planned_shots]

    def create_production_package(
        self,
        session: Session,
        demo_id: int,
        shots_data: list[dict[str, Any]],
        project_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Compile production package with 7 manifests, FCPXML, EDL, and SVG overlays."""
        repo = DemoRepository(session)
        demo = repo.get_by_id(demo_id)
        if not demo:
            raise ValueError(f"Demo with ID {demo_id} not found.")

        pkg_id = f"pkg_{uuid.uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc).isoformat()
        map_name = (demo.map_name or "cs2_map").replace("de_", "").upper()
        proj_name = project_name or f"CS2 {map_name} Cinematic Master"

        pkg_dir = self.output_root / "cinematic_packages" / pkg_id
        pkg_dir.mkdir(parents=True, exist_ok=True)

        shots: list[CinematicShot] = []
        overlay_events: list[OverlayKillEvent] = []

        all_kills = repo.get_kills(demo_id)

        for s_dict in shots_data:
            c_type = CameraType(s_dict.get("camera_type", CameraType.FIRST_PERSON.value))
            purpose = ShotPurpose(s_dict.get("purpose", ShotPurpose.PRIMARY_ACTION.value))

            shot = CinematicShot(
                shot_id=s_dict["shot_id"],
                highlight_id=s_dict["highlight_id"],
                round_number=s_dict["round_number"],
                camera_type=c_type,
                purpose=purpose,
                start_tick=s_dict["start_tick"],
                end_tick=s_dict["end_tick"],
                start_time=s_dict["start_time"],
                end_time=s_dict["end_time"],
                duration_seconds=s_dict["duration_seconds"],
                fov=s_dict.get("fov", 90.0),
                pov_steam_id=s_dict.get("pov_steam_id"),
                pov_name=s_dict.get("pov_name"),
                focus_target_name=s_dict.get("focus_target_name"),
                focus_target_steam_id=s_dict.get("focus_target_steam_id"),
                output_filename=s_dict.get("output_filename", f"{s_dict['shot_id']}.mp4"),
                enabled=s_dict.get("enabled", True),
                fps=s_dict.get("fps", 60),
                resolution=s_dict.get("resolution", "1920x1080"),
                hud_mode=s_dict.get("hud_mode", "none"),
                xray=s_dict.get("xray", False),
                watermark=False,  # Strict: no watermark
            )
            shots.append(shot)

            # Collect overlay events for this shot
            for k in all_kills:
                if shot.start_tick <= k.tick <= shot.end_tick:
                    overlay_events.append(
                        OverlayKillEvent(
                            tick=k.tick,
                            time_seconds=k.tick / 128.0,
                            round_number=k.round_num,
                            killer_name=k.attacker_name or "Hero",
                            killer_steam_id=k.attacker_steam_id or "",
                            victim_name=k.victim_name or "Victim",
                            victim_steam_id=k.victim_steam_id or "",
                            weapon=k.weapon or "ak47",
                            headshot=bool(k.headshot),
                            wallbang=bool(getattr(k, "wallbang", getattr(k, "penetrated", False))),
                            noscope=False,
                            thrusmoke=False,
                            attackerblind=False,
                            kill_number_in_round=1,
                        )
                    )

        # Build EDL clips
        edl_clips: list[EditDecisionClip] = []
        tl_cursor = 0.0
        for s in shots:
            if s.enabled:
                lane = 1 if s.purpose == ShotPurpose.PRIMARY_ACTION else (2 if s.purpose == ShotPurpose.APPROACH else 3)
                edl_clips.append(
                    EditDecisionClip(
                        track_index=lane,
                        shot_id=s.shot_id,
                        media_path=str((pkg_dir / s.output_filename).as_posix()),
                        source_in_seconds=0.0,
                        source_out_seconds=s.duration_seconds,
                        timeline_in_seconds=tl_cursor,
                        timeline_out_seconds=tl_cursor + s.duration_seconds,
                        clip_name=s.output_filename,
                    )
                )
                if s.purpose == ShotPurpose.PRIMARY_ACTION:
                    tl_cursor += s.duration_seconds

        pkg = CinematicProductionPackage(
            package_id=pkg_id,
            demo_id=str(demo_id),
            demo_name=pathlib.Path(getattr(demo, "file_path", getattr(demo, "source_path", "match.dem"))).name,
            map_name=map_name,
            created_at=created_at,
            shots=shots,
            edl_clips=edl_clips,
            overlay_events=overlay_events,
            output_directory=str(pkg_dir.resolve()),
            resolve_project_name=proj_name,
        )

        # 1. Write the 7 production JSON manifests
        manifest_paths = write_manifests(pkg, pkg_dir)

        # 2. Write DaVinci Resolve FCPXML
        fcpxml_path = pkg_dir / "DaVinci_Resolve_Project.fcpxml"
        generate_fcpxml(pkg, fps=60, output_path=fcpxml_path)
        pkg.fcpxml_path = str(fcpxml_path.resolve())

        # 3. Write CMX 3600 EDL
        edl_path = pkg_dir / "Timeline.edl"
        generate_cmx3600_edl(pkg, fps=60, output_path=edl_path)

        # 4. Generate SVG Overlays
        overlay_files = export_svg_killfeed(overlay_events, pkg_dir / "overlays")

        return {
            "package_id": pkg_id,
            "project_name": proj_name,
            "output_directory": str(pkg_dir.resolve()),
            "total_shots": len([s for s in shots if s.enabled]),
            "fcpxml_path": str(fcpxml_path.resolve()),
            "edl_path": str(edl_path.resolve()),
            "manifests": {k: str(v.resolve()) for k, v in manifest_paths.items()},
            "overlay_count": len(overlay_files),
        }
