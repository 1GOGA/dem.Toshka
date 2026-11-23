"""Unit tests for the CS2 Cinematic Camera Engine."""

from backend.cinematic.camera_engine import CameraEngine
from backend.cinematic.models import CameraType, Vector3


def test_camera_engine_supported_modes():
    engine = CameraEngine()
    assert len(engine.SUPPORTED_MODES) == 12
    assert CameraType.SHOULDER_CAMERA in engine.SUPPORTED_MODES
    assert CameraType.CINEMATIC_FLYBY in engine.SUPPORTED_MODES
    assert CameraType.ORBIT_CAMERA in engine.SUPPORTED_MODES


def test_camera_engine_create_paths():
    engine = CameraEngine()

    dummy_ticks = [
        {"tick": 1000, "X": 0.0, "Y": 0.0, "Z": 64.0, "pitch": 0.0, "yaw": 0.0},
        {"tick": 1016, "X": 10.0, "Y": 5.0, "Z": 64.0, "pitch": 0.0, "yaw": 5.0},
        {"tick": 1032, "X": 20.0, "Y": 10.0, "Z": 64.0, "pitch": 0.0, "yaw": 10.0},
        {"tick": 1048, "X": 30.0, "Y": 15.0, "Z": 64.0, "pitch": 0.0, "yaw": 15.0},
    ]

    # Shoulder camera path
    shoulder_path = engine.create_path_for_mode(CameraType.SHOULDER_CAMERA, player_ticks=dummy_ticks)
    assert shoulder_path.camera_type == CameraType.SHOULDER_CAM
    assert len(shoulder_path.points) > 0

    # Orbit path
    orbit_path = engine.create_path_for_mode(
        CameraType.ORBIT_CAMERA,
        target_pos=Vector3(100, 100, 64),
        duration_seconds=2.0,
    )
    assert orbit_path.camera_type == CameraType.ORBIT_CAMERA
    assert len(orbit_path.points) > 0

    # Cinematic Flyby path
    flyby_path = engine.create_path_for_mode(
        CameraType.CINEMATIC_FLYBY,
        anchor_pos=Vector3(-100, 0, 100),
        target_pos=Vector3(100, 0, 100),
        duration_seconds=3.0,
    )
    assert flyby_path.camera_type == CameraType.FREECAM_FLYBY
    assert len(flyby_path.points) > 0


def test_camera_engine_export_hlae_xml(tmp_path):
    engine = CameraEngine()
    orbit_path = engine.create_path_for_mode(
        CameraType.ORBIT_CAMERA,
        target_pos=Vector3(0, 0, 64),
        duration_seconds=2.0,
    )
    out_xml = tmp_path / "test_engine_campath.xml"
    engine.export_to_hlae_xml(orbit_path, out_xml)

    assert out_xml.exists()
    content = out_xml.read_text(encoding="utf-8")
    assert "<campath" in content
    assert "<point" in content
