"""Data models and production schemas for dem.Toshka Cinematic Studio.

Implements the Structured Production Protocol with strict schemas for:
- highlight_manifest.json
- shot_plan.json
- camera_paths.json
- capture_manifest.json
- edit_decision_list.json
- overlay_events.json
- render_manifest.json
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class CameraType(str, Enum):
    """The 8 core cinematic camera presets supported by Cinematic Studio."""

    FIRST_PERSON = "FIRST_PERSON"
    VICTIM_POV = "VICTIM_POV"
    THIRD_PERSON_CHASE = "THIRD_PERSON_CHASE"
    SHOULDER_CAM = "SHOULDER_CAM"
    FREECAM_FLYBY = "FREECAM_FLYBY"
    ORBIT_CAMERA = "ORBIT_CAMERA"
    ESTABLISHING_SHOT = "ESTABLISHING_SHOT"
    TOP_DOWN = "TOP_DOWN"


class InterpolationMode(str, Enum):
    LINEAR = "linear"
    CUBIC = "cubic"
    SCUBIC = "sCubic"
    SLINEAR = "sLinear"


class ShotPurpose(str, Enum):
    ESTABLISH = "ESTABLISH"
    APPROACH = "APPROACH"
    PRIMARY_ACTION = "PRIMARY_ACTION"
    VICTIM_REACTION = "VICTIM_REACTION"
    TRANSITION = "TRANSITION"
    CLIMAX_ACCENT = "CLIMAX_ACCENT"
    OUTRO = "OUTRO"


@dataclass
class Vector3:
    x: float
    y: float
    z: float

    def to_dict(self) -> dict[str, float]:
        return {"x": round(self.x, 3), "y": round(self.y, 3), "z": round(self.z, 3)}


@dataclass
class Rotation3:
    """Euler angles in degrees.
    In HLAE Quake coordinates:
    rx: Roll (camera tilt)
    ry: Pitch (up/down: -89 to 89)
    rz: Yaw (horizontal compass rotation: -180 to 180)
    """

    pitch: float  # ry
    yaw: float  # rz
    roll: float = 0.0  # rx

    def to_dict(self) -> dict[str, float]:
        return {
            "pitch": round(self.pitch, 3),
            "yaw": round(self.yaw, 3),
            "roll": round(self.roll, 3),
        }


@dataclass
class CampathPoint:
    """A single 3D keyframe for HLAE mirv_campath."""

    time: float  # Demo time in seconds
    tick: int  # Exact demo tick
    position: Vector3  # X, Y, Z
    rotation: Rotation3  # pitch (ry), yaw (rz), roll (rx)
    fov: float = 90.0

    def to_xml_element(self) -> str:
        return (
            "    <p>\n"
            f"      <t>{self.time:.4f}</t>\n"
            f"      <x>{self.position.x:.3f}</x>\n"
            f"      <y>{self.position.y:.3f}</y>\n"
            f"      <z>{self.position.z:.3f}</z>\n"
            f"      <rx>{self.rotation.roll:.3f}</rx>\n"
            f"      <ry>{self.rotation.pitch:.3f}</ry>\n"
            f"      <rz>{self.rotation.yaw:.3f}</rz>\n"
            f"      <fov>{self.fov:.2f}</fov>\n"
            "    </p>"
        )


@dataclass
class CameraPath:
    """A full spline trajectory for HLAE mirv_campath."""

    path_id: str
    camera_type: CameraType
    points: list[CampathPoint] = field(default_factory=list)
    position_interp: InterpolationMode = InterpolationMode.CUBIC
    rotation_interp: InterpolationMode = InterpolationMode.SCUBIC
    fov_interp: InterpolationMode = InterpolationMode.CUBIC
    hold: bool = False
    offset: float = 0.0

    def to_xml(self) -> str:
        lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            "<campath>",
            f"  <positionInterp>{self.position_interp.value}</positionInterp>",
            f"  <rotationInterp>{self.rotation_interp.value}</rotationInterp>",
            f"  <fovInterp>{self.fov_interp.value}</fovInterp>",
            f"  <offset>{self.offset:.3f}</offset>",
            f"  <hold>{1 if self.hold else 0}</hold>",
            "  <points>",
        ]
        for p in self.points:
            lines.append(p.to_xml_element())
        lines.append("  </points>")
        lines.append("</campath>")
        return "\n".join(lines)


@dataclass
class CinematicShot:
    """A single planned camera capture shot within a highlight sequence."""

    shot_id: str
    highlight_id: str
    round_number: int
    camera_type: CameraType
    purpose: ShotPurpose
    start_tick: int
    end_tick: int
    start_time: float
    end_time: float
    duration_seconds: float
    fov: float = 90.0
    pov_steam_id: Optional[str] = None
    pov_name: Optional[str] = None
    focus_target_name: Optional[str] = None
    focus_target_steam_id: Optional[str] = None
    campath: Optional[CameraPath] = None
    output_filename: str = ""
    enabled: bool = True
    # Camera coordinates at start
    start_position: Optional[Vector3] = None
    start_rotation: Optional[Rotation3] = None
    # Rendering parameters
    fps: int = 60
    resolution: str = "1920x1080"
    hud_mode: str = "none"  # Default cinematic clean
    xray: bool = False
    watermark: bool = False  # Strict default: no watermark for cinematic masters
    validation_status: str = "PLANNED"  # PLANNED, CAPTURED, VERIFIED, FAILED
    error_summary: Optional[str] = None
    # V2 Planning & Quality fields
    slow_motion_timescale: float = 1.0
    quality_score: Optional[float] = None
    clipping_risk: bool = False
    quality_status: str = "VERIFIED"  # VERIFIED, EXPERIMENTAL, NEEDS_PREVIEW_REVIEW, REJECTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "shot_id": self.shot_id,
            "highlight_id": self.highlight_id,
            "round_number": self.round_number,
            "camera_type": self.camera_type.value,
            "purpose": self.purpose.value,
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "start_time": round(self.start_time, 3),
            "end_time": round(self.end_time, 3),
            "duration_seconds": round(self.duration_seconds, 3),
            "fov": self.fov,
            "pov_steam_id": self.pov_steam_id,
            "pov_name": self.pov_name,
            "focus_target_name": self.focus_target_name,
            "focus_target_steam_id": self.focus_target_steam_id,
            "has_campath": self.campath is not None,
            "output_filename": self.output_filename,
            "enabled": self.enabled,
            "start_position": self.start_position.to_dict() if self.start_position else None,
            "start_rotation": self.start_rotation.to_dict() if self.start_rotation else None,
            "fps": self.fps,
            "resolution": self.resolution,
            "hud_mode": self.hud_mode,
            "xray": self.xray,
            "watermark": self.watermark,
            "validation_status": self.validation_status,
            "error_summary": self.error_summary,
            "slow_motion_timescale": self.slow_motion_timescale,
            "quality_score": self.quality_score,
            "clipping_risk": self.clipping_risk,
            "quality_status": self.quality_status,
        }


@dataclass
class OverlayKillEvent:
    """Rich kill event metadata for graphical kill-feed / overlay generation."""

    tick: int
    time_seconds: float
    round_number: int
    killer_name: str
    killer_steam_id: str
    victim_name: str
    victim_steam_id: str
    weapon: str
    headshot: bool
    wallbang: bool
    noscope: bool
    thrusmoke: bool
    attackerblind: bool
    kill_number_in_round: int
    is_ace: bool = False
    is_clutch: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EditDecisionClip:
    """An EDL entry representing one slice in the DaVinci Resolve timeline."""

    track_index: int  # 1 = Base POV, 2 = Cinematic B-Roll, 3 = Victim inserts, 4 = Overlays
    shot_id: str
    media_path: str
    source_in_seconds: float
    source_out_seconds: float
    timeline_in_seconds: float
    timeline_out_seconds: float
    clip_name: str
    transition_in: Optional[str] = None  # cut, cross_dissolve, whip_pan
    suggested_speed: float = 1.0  # 1.0 = normal, 0.5 = slowmo on kill

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CinematicProductionPackage:
    """Complete production manifest bundle ready for DaVinci Resolve handoff."""

    package_id: str
    demo_id: str
    demo_name: str
    map_name: str
    created_at: str
    shots: list[CinematicShot] = field(default_factory=list)
    edl_clips: list[EditDecisionClip] = field(default_factory=list)
    overlay_events: list[OverlayKillEvent] = field(default_factory=list)
    output_directory: str = ""
    resolve_project_name: str = ""
    fcpxml_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "demo_id": self.demo_id,
            "demo_name": self.demo_name,
            "map_name": self.map_name,
            "created_at": self.created_at,
            "shots": [s.to_dict() for s in self.shots],
            "edl_clips": [c.to_dict() for c in self.edl_clips],
            "overlay_events": [e.to_dict() for e in self.overlay_events],
            "output_directory": self.output_directory,
            "resolve_project_name": self.resolve_project_name,
            "fcpxml_path": self.fcpxml_path,
        }
