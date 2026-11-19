"""Advanced CS2 Cinematic Camera Engine.

Supports 12 camera modes with Catmull-Rom spline interpolation, dynamic target tracking,
collision awareness, and mirv_campath XML interchange.
"""

from __future__ import annotations

import logging
import math
import pathlib
from typing import Any, Optional

from backend.cinematic.camera_library import (
    calculate_look_at as library_calculate_look_at,
    generate_establishing_camera_path,
    generate_flyby_camera_path,
    generate_orbit_camera_path,
    generate_shoulder_cam_path,
    generate_top_down_camera_path,
)
from backend.cinematic.models import (
    CameraPath,
    CameraType,
    CampathPoint,
    InterpolationMode,
    Rotation3,
    Vector3,
)
from backend.hlae.campath import CamKeyframe, HLAECampathManager

logger = logging.getLogger("demtoshka.cinematic.camera_engine")


class CameraEngine:
    """Orchestrates 12 camera modes and generates in-engine CS2 camera paths."""

    SUPPORTED_MODES = [
        CameraType.FIRST_PERSON,
        CameraType.VICTIM_POV,
        CameraType.THIRD_PERSON,
        CameraType.CHASE_CAMERA,
        CameraType.FREE_CAMERA,
        CameraType.ORBIT_CAMERA,
        CameraType.SHOULDER_CAMERA,
        CameraType.FOLLOW_TARGET,
        CameraType.FIXED_CAMERA,
        CameraType.CINEMATIC_FLYBY,
        CameraType.TOP_DOWN,
        CameraType.CUSTOM_PATH,
    ]

    def __init__(self, campath_manager: Optional[HLAECampathManager] = None) -> None:
        self.campath_manager = campath_manager or HLAECampathManager()

    def create_path_for_mode(
        self,
        mode: CameraType | str,
        player_ticks: Optional[list[dict[str, Any]]] = None,
        target_pos: Optional[Vector3] = None,
        anchor_pos: Optional[Vector3] = None,
        duration_seconds: float = 3.0,
        start_tick: int = 0,
        tickrate: int = 64,
        fov: float = 90.0,
    ) -> CameraPath:
        """Create a complete CameraPath matching the requested mode."""
        mode_str = str(mode.value if isinstance(mode, CameraType) else mode).upper()
        end_tick = start_tick + int(duration_seconds * tickrate)

        if mode_str in ("FIRST_PERSON", "VICTIM_POV"):
            return CameraPath(
                path_id=f"{mode_str.lower()}_{start_tick}",
                camera_type=CameraType[mode_str],
                position_interp=InterpolationMode.LINEAR,
                rotation_interp=InterpolationMode.SLINEAR,
            )

        if mode_str in ("SHOULDER_CAM", "SHOULDER_CAMERA"):
            return generate_shoulder_cam_path(
                player_ticks=player_ticks or [],
                tickrate=tickrate,
                fov=fov,
            )

        if mode_str in ("THIRD_PERSON", "THIRD_PERSON_CHASE", "CHASE_CAMERA"):
            # Third-person uses shoulder cam with slightly wider offset
            return generate_shoulder_cam_path(
                player_ticks=player_ticks or [],
                tickrate=tickrate,
                dist_back=65.0,
                dist_right=0.0,
                height_offset=70.0,
                fov=fov,
            )

        if mode_str in ("ORBIT_CAMERA",):
            center = target_pos or Vector3(0, 0, 0)
            if player_ticks and len(player_ticks) > 0:
                mid = player_ticks[len(player_ticks) // 2]
                center = Vector3(float(mid.get("X", 0)), float(mid.get("Y", 0)), float(mid.get("Z", 0)))
            return generate_orbit_camera_path(
                center_pos=center,
                start_tick=start_tick,
                end_tick=end_tick,
                tickrate=tickrate,
                fov=fov,
            )

        if mode_str in ("CINEMATIC_FLYBY", "FREECAM_FLYBY", "FREE_CAMERA"):
            p1 = anchor_pos or Vector3(-200, -200, 100)
            p2 = target_pos or Vector3(200, 200, 100)
            look = target_pos or Vector3(0, 0, 64)
            return generate_flyby_camera_path(
                start_pos=p1,
                end_pos=p2,
                target_focus=look,
                start_tick=start_tick,
                end_tick=end_tick,
                tickrate=tickrate,
                fov_start=fov,
                fov_end=fov,
            )

        if mode_str in ("FIXED_CAMERA", "ESTABLISHING_SHOT"):
            pos = anchor_pos or Vector3(0, 0, 120)
            return generate_establishing_camera_path(
                area_center=pos,
                start_tick=start_tick,
                end_tick=end_tick,
                tickrate=tickrate,
                fov=fov,
            )

        if mode_str in ("TOP_DOWN",):
            center = target_pos or Vector3(0, 0, 0)
            return generate_top_down_camera_path(
                combat_center=center,
                start_tick=start_tick,
                end_tick=end_tick,
                tickrate=tickrate,
                fov=fov,
            )

        if mode_str in ("FOLLOW_TARGET", "CUSTOM_PATH"):
            path = CameraPath(
                path_id=f"{mode_str.lower()}_{start_tick}",
                camera_type=CameraType.CUSTOM_PATH,
                position_interp=InterpolationMode.CUBIC,
                rotation_interp=InterpolationMode.SCUBIC,
            )
            if player_ticks and target_pos:
                for i, tick_data in enumerate(player_ticks[::16]):
                    pos = Vector3(float(tick_data.get("X", 0)), float(tick_data.get("Y", 0)), float(tick_data.get("Z", 0)) + 64.0)
                    rot = library_calculate_look_at(pos, target_pos)
                    time_s = (tick_data.get("tick", start_tick) - start_tick) / tickrate
                    path.points.append(
                        CampathPoint(
                            tick=tick_data.get("tick", start_tick),
                            time=time_s,
                            position=pos,
                            rotation=rot,
                            fov=fov,
                        )
                    )
            return path

        # Default fallback
        return CameraPath(
            path_id=f"default_{start_tick}",
            camera_type=CameraType.FIRST_PERSON,
        )

    def export_to_hlae_xml(self, camera_path: CameraPath, output_xml_path: pathlib.Path) -> pathlib.Path:
        """Export a domain CameraPath to standard HLAE mirv_campath XML."""
        manager = HLAECampathManager()
        for pt in camera_path.points:
            manager.add_keyframe(
                time_or_kf=pt.time,
                x=pt.position.x,
                y=pt.position.y,
                z=pt.position.z,
                pitch=pt.rotation.pitch,
                yaw=pt.rotation.yaw,
                roll=pt.rotation.roll,
                fov=pt.fov,
            )
        return manager.export_xml(output_xml_path)
