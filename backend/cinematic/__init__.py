"""dem.Toshka Cinematic Studio module."""

from backend.cinematic.camera_library import (
    calculate_look_at,
    generate_establishing_camera_path,
    generate_flyby_camera_path,
    generate_orbit_camera_path,
    generate_shoulder_cam_path,
    generate_top_down_camera_path,
)
from backend.cinematic.campath_generator import export_campath_xml, validate_campath
from backend.cinematic.capture_engine import CinematicCaptureEngine
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
from backend.cinematic.overlay_generator import (
    export_svg_killfeed,
    generate_svg_killfeed_badge,
)
from backend.cinematic.resolve_export import generate_cmx3600_edl, generate_fcpxml
from backend.cinematic.shot_director import (
    AutomaticShotDirector,
    HighlightScorer,
    detect_quick_flick,
)

__all__ = [
    "CameraPath",
    "CameraType",
    "CampathPoint",
    "CinematicProductionPackage",
    "CinematicShot",
    "EditDecisionClip",
    "InterpolationMode",
    "OverlayKillEvent",
    "Rotation3",
    "ShotPurpose",
    "Vector3",
    "calculate_look_at",
    "generate_establishing_camera_path",
    "generate_flyby_camera_path",
    "generate_orbit_camera_path",
    "generate_shoulder_cam_path",
    "generate_top_down_camera_path",
    "export_campath_xml",
    "validate_campath",
    "CinematicCaptureEngine",
    "write_manifests",
    "export_svg_killfeed",
    "generate_svg_killfeed_badge",
    "generate_fcpxml",
    "generate_cmx3600_edl",
    "AutomaticShotDirector",
    "HighlightScorer",
    "detect_quick_flick",
]
