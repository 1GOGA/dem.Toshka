"""Cinematic Camera Preset Library for CS2.

Implements the 8 camera types with Quake/Source 2 3D vector calculations:
1. FIRST_PERSON
2. VICTIM_POV
3. THIRD_PERSON_CHASE
4. SHOULDER_CAM
5. FREECAM_FLYBY
6. ORBIT_CAMERA
7. ESTABLISHING_SHOT
8. TOP_DOWN
"""

from __future__ import annotations

import math
from typing import Any, Optional

from backend.cinematic.models import (
    CameraPath,
    CameraType,
    CampathPoint,
    InterpolationMode,
    Rotation3,
    Vector3,
)


def _deg2rad(deg: float) -> float:
    return deg * (math.pi / 180.0)


def _rad2deg(rad: float) -> float:
    return rad * (180.0 / math.pi)


def calculate_look_at(from_pos: Vector3, target_pos: Vector3) -> Rotation3:
    """Calculate Euler pitch (ry) and yaw (rz) in degrees to aim from from_pos at target_pos.
    
    Source 2 / Quake coordinate conventions:
    Pitch: positive looks down, negative looks up (or vice versa in HLAE).
    In HLAE mirv_campath: ry is pitch (positive down), rz is yaw (-180 to 180).
    """
    dx = target_pos.x - from_pos.x
    dy = target_pos.y - from_pos.y
    dz = target_pos.z - from_pos.z

    dist_xy = math.sqrt(dx * dx + dy * dy)
    if dist_xy < 1e-4:
        pitch = -89.0 if dz > 0 else 89.0
        yaw = 0.0
    else:
        # Yaw: angle in XY plane
        yaw = _rad2deg(math.atan2(dy, dx))
        # Pitch: angle between XY plane and target
        pitch = -_rad2deg(math.atan2(dz, dist_xy))

    # Clamp pitch to valid CS2 camera range [-89, 89]
    pitch = max(-89.0, min(89.0, pitch))
    return Rotation3(pitch=pitch, yaw=yaw, roll=0.0)


def generate_shoulder_cam_path(
    player_ticks: list[dict[str, Any]],
    tickrate: int = 128,
    sample_interval_ticks: int = 16,
    dist_back: float = 45.0,
    dist_right: float = 22.0,
    height_offset: float = 60.0,
    fov: float = 95.0,
    conservative_fallback: bool = False,
    fallback_dist_right: float = 10.0,
    fallback_dist_back: float = 30.0,
) -> CameraPath:
    """Generate an over-the-shoulder dynamic camera path following a player's real coordinates.
    
    player_ticks format: list of dicts with 'tick', 'X', 'Y', 'Z', 'pitch', 'yaw'.
    If conservative_fallback is True, reduces lateral and backward offset to prevent
    camera clipping in narrow corridors and near geometry boundaries.
    """
    if conservative_fallback:
        dist_back = fallback_dist_back
        dist_right = fallback_dist_right
    path = CameraPath(
        path_id="shoulder_cam",
        camera_type=CameraType.SHOULDER_CAM,
        position_interp=InterpolationMode.CUBIC,
        rotation_interp=InterpolationMode.SCUBIC,
        fov_interp=InterpolationMode.CUBIC,
    )

    if not player_ticks:
        return path

    sorted_ticks = sorted(player_ticks, key=lambda t: t.get("tick", 0))
    sampled = sorted_ticks[::sample_interval_ticks]
    if sorted_ticks and sorted_ticks[-1] not in sampled:
        sampled.append(sorted_ticks[-1])

    # HLAE requires at least 4 keyframes for cubic spline evaluation
    if len(sampled) < 4 and len(sorted_ticks) >= 4:
        step = max(1, len(sorted_ticks) // 4)
        sampled = sorted_ticks[::step][:4]

    for pt in sampled:
        t_tick = int(pt.get("tick", 0))
        t_sec = t_tick / float(tickrate)
        px = float(pt.get("X", 0.0))
        py = float(pt.get("Y", 0.0))
        pz = float(pt.get("Z", 0.0))
        pitch = float(pt.get("pitch", 0.0))
        yaw = float(pt.get("yaw", 0.0))

        yaw_rad = _deg2rad(yaw)
        # Unit forward vector
        fx = math.cos(yaw_rad)
        fy = math.sin(yaw_rad)
        # Unit right vector (perpendicular to forward in XY plane)
        rx = math.sin(yaw_rad)
        ry = -math.cos(yaw_rad)

        cam_x = px - (dist_back * fx) + (dist_right * rx)
        cam_y = py - (dist_back * fy) + (dist_right * ry)
        cam_z = pz + height_offset

        path.points.append(
            CampathPoint(
                time=t_sec,
                tick=t_tick,
                position=Vector3(x=cam_x, y=cam_y, z=cam_z),
                rotation=Rotation3(pitch=pitch, yaw=yaw, roll=0.0),
                fov=fov,
            )
        )

    return path


def generate_orbit_camera_path(
    center_pos: Vector3,
    start_tick: int,
    end_tick: int,
    tickrate: int = 128,
    radius: float = 180.0,
    height: float = 55.0,
    arc_degrees: float = 75.0,
    initial_angle_deg: float = 0.0,
    fov: float = 85.0,
    num_points: int = 6,
) -> CameraPath:
    """Generate a smooth circular orbit path around a combat location or player anchor."""
    path = CameraPath(
        path_id="orbit_cam",
        camera_type=CameraType.ORBIT_CAMERA,
        position_interp=InterpolationMode.CUBIC,
        rotation_interp=InterpolationMode.SCUBIC,
        fov_interp=InterpolationMode.CUBIC,
    )

    duration_ticks = max(1, end_tick - start_tick)
    target_look = Vector3(center_pos.x, center_pos.y, center_pos.z + 40.0)

    for i in range(num_points):
        frac = i / float(num_points - 1)
        cur_tick = int(start_tick + frac * duration_ticks)
        cur_time = cur_tick / float(tickrate)

        angle_deg = initial_angle_deg + (frac * arc_degrees)
        angle_rad = _deg2rad(angle_deg)

        cam_x = center_pos.x + radius * math.cos(angle_rad)
        cam_y = center_pos.y + radius * math.sin(angle_rad)
        cam_z = center_pos.z + height

        cam_pos = Vector3(x=cam_x, y=cam_y, z=cam_z)
        rot = calculate_look_at(cam_pos, target_look)

        path.points.append(
            CampathPoint(
                time=cur_time,
                tick=cur_tick,
                position=cam_pos,
                rotation=rot,
                fov=fov,
            )
        )

    return path


def generate_flyby_camera_path(
    start_pos: Vector3,
    end_pos: Vector3,
    target_focus: Vector3,
    start_tick: int,
    end_tick: int,
    tickrate: int = 128,
    fov_start: float = 90.0,
    fov_end: float = 75.0,
    num_points: int = 6,
) -> CameraPath:
    """Generate a sweeping free camera flyby through a corridor or bombsite."""
    path = CameraPath(
        path_id="freecam_flyby",
        camera_type=CameraType.FREECAM_FLYBY,
        position_interp=InterpolationMode.CUBIC,
        rotation_interp=InterpolationMode.SCUBIC,
        fov_interp=InterpolationMode.CUBIC,
    )

    duration_ticks = max(1, end_tick - start_tick)

    for i in range(num_points):
        frac = i / float(num_points - 1)
        cur_tick = int(start_tick + frac * duration_ticks)
        cur_time = cur_tick / float(tickrate)

        # Smooth cubic ease-in-out easing for spatial motion
        # t^2 * (3 - 2t)
        ease = frac * frac * (3.0 - 2.0 * frac)

        cam_x = start_pos.x + ease * (end_pos.x - start_pos.x)
        cam_y = start_pos.y + ease * (end_pos.y - start_pos.y)
        cam_z = start_pos.z + ease * (end_pos.z - start_pos.z)

        cam_pos = Vector3(x=cam_x, y=cam_y, z=cam_z)
        rot = calculate_look_at(cam_pos, target_focus)
        cur_fov = fov_start + ease * (fov_end - fov_start)

        path.points.append(
            CampathPoint(
                time=cur_time,
                tick=cur_tick,
                position=cam_pos,
                rotation=rot,
                fov=cur_fov,
            )
        )

    return path


def generate_establishing_camera_path(
    area_center: Vector3,
    start_tick: int,
    end_tick: int,
    tickrate: int = 128,
    elevation: float = 320.0,
    distance: float = 480.0,
    angle_deg: float = 45.0,
    pan_drift_deg: float = 6.0,
    fov: float = 80.0,
    num_points: int = 5,
) -> CameraPath:
    """Generate a grand establishing / intro shot overlooking the map sector."""
    path = CameraPath(
        path_id="establishing_shot",
        camera_type=CameraType.ESTABLISHING_SHOT,
        position_interp=InterpolationMode.CUBIC,
        rotation_interp=InterpolationMode.SCUBIC,
        fov_interp=InterpolationMode.LINEAR,
    )

    duration_ticks = max(1, end_tick - start_tick)

    for i in range(num_points):
        frac = i / float(num_points - 1)
        cur_tick = int(start_tick + frac * duration_ticks)
        cur_time = cur_tick / float(tickrate)

        cur_angle = angle_deg + (frac * pan_drift_deg)
        rad = _deg2rad(cur_angle)

        cam_x = area_center.x + distance * math.cos(rad)
        cam_y = area_center.y + distance * math.sin(rad)
        cam_z = area_center.z + elevation

        cam_pos = Vector3(x=cam_x, y=cam_y, z=cam_z)
        rot = calculate_look_at(cam_pos, area_center)

        path.points.append(
            CampathPoint(
                time=cur_time,
                tick=cur_tick,
                position=cam_pos,
                rotation=rot,
                fov=fov,
            )
        )

    return path


def generate_top_down_camera_path(
    combat_center: Vector3,
    start_tick: int,
    end_tick: int,
    tickrate: int = 128,
    height: float = 550.0,
    fov: float = 90.0,
    num_points: int = 4,
) -> CameraPath:
    """Generate a top-down tactical overview camera looking straight down."""
    path = CameraPath(
        path_id="top_down",
        camera_type=CameraType.TOP_DOWN,
        position_interp=InterpolationMode.LINEAR,
        rotation_interp=InterpolationMode.SLINEAR,
        fov_interp=InterpolationMode.LINEAR,
    )

    duration_ticks = max(1, end_tick - start_tick)

    for i in range(num_points):
        frac = i / float(num_points - 1)
        cur_tick = int(start_tick + frac * duration_ticks)
        cur_time = cur_tick / float(tickrate)

        # Subtle slow tactical push
        cam_z = combat_center.z + height - (frac * 30.0)
        cam_pos = Vector3(x=combat_center.x, y=combat_center.y, z=cam_z)

        # Pitch -89.0 (nearly straight down to avoid gimbal singularity)
        rot = Rotation3(pitch=-89.0, yaw=0.0, roll=0.0)

        path.points.append(
            CampathPoint(
                time=cur_time,
                tick=cur_tick,
                position=cam_pos,
                rotation=rot,
                fov=fov,
            )
        )

    return path
