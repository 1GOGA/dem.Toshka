"""Unit tests for Cinematic Camera Library and HLAE Campath XML Generator."""

import math
import pathlib
import pytest

from backend.cinematic.camera_library import (
    calculate_look_at,
    generate_establishing_camera_path,
    generate_flyby_camera_path,
    generate_orbit_camera_path,
    generate_shoulder_cam_path,
    generate_top_down_camera_path,
)
from backend.cinematic.campath_generator import (
    CampathValidationError,
    export_campath_xml,
    validate_campath,
)
from backend.cinematic.models import (
    CameraPath,
    CameraType,
    CampathPoint,
    InterpolationMode,
    Rotation3,
    Vector3,
)


class TestCameraMath:
    def test_calculate_look_at_horizontal(self):
        from_pos = Vector3(0.0, 0.0, 0.0)
        target_pos = Vector3(100.0, 0.0, 0.0)
        rot = calculate_look_at(from_pos, target_pos)
        assert abs(rot.pitch) < 1e-3
        assert abs(rot.yaw) < 1e-3
        assert abs(rot.roll) < 1e-3

    def test_calculate_look_at_vertical(self):
        from_pos = Vector3(0.0, 0.0, 100.0)
        target_pos = Vector3(0.0, 0.0, 0.0)
        rot = calculate_look_at(from_pos, target_pos)
        assert rot.pitch == 89.0  # looking straight down, clamped to 89 deg

    def test_calculate_look_at_diagonal(self):
        from_pos = Vector3(0.0, 0.0, 0.0)
        target_pos = Vector3(100.0, 100.0, 0.0)
        rot = calculate_look_at(from_pos, target_pos)
        assert abs(rot.yaw - 45.0) < 1e-2


class TestCameraPresets:
    def test_shoulder_cam_generation(self):
        ticks = [
            {"tick": 100 + i * 16, "X": 100.0 + i * 10, "Y": 200.0, "Z": 0.0, "pitch": 0.0, "yaw": 90.0}
            for i in range(10)
        ]
        path = generate_shoulder_cam_path(ticks, tickrate=128)
        assert path.camera_type == CameraType.SHOULDER_CAM
        assert len(path.points) >= 4
        # Yaw 90 means facing positive Y. Right vector points to positive X.
        # So X should be shifted by dist_right (+22.0)
        first_pt = path.points[0]
        assert abs(first_pt.position.x - 122.0) < 1.0

    def test_orbit_camera_generation(self):
        center = Vector3(500.0, 500.0, 100.0)
        path = generate_orbit_camera_path(center, start_tick=1000, end_tick=1300, tickrate=128)
        assert path.camera_type == CameraType.ORBIT_CAMERA
        assert len(path.points) == 6
        # Check radius constraint for all points
        for pt in path.points:
            dx = pt.position.x - center.x
            dy = pt.position.y - center.y
            r = math.sqrt(dx * dx + dy * dy)
            assert abs(r - 180.0) < 1e-2

    def test_flyby_camera_generation(self):
        start = Vector3(0.0, 0.0, 50.0)
        end = Vector3(300.0, 400.0, 50.0)
        focus = Vector3(150.0, 200.0, 10.0)
        path = generate_flyby_camera_path(start, end, focus, start_tick=500, end_tick=800)
        assert path.camera_type == CameraType.FREECAM_FLYBY
        assert len(path.points) == 6
        assert abs(path.points[0].position.x - start.x) < 1e-2
        assert abs(path.points[-1].position.x - end.x) < 1e-2

    def test_establishing_shot_generation(self):
        center = Vector3(100.0, 200.0, 0.0)
        path = generate_establishing_camera_path(center, start_tick=200, end_tick=500)
        assert path.camera_type == CameraType.ESTABLISHING_SHOT
        assert len(path.points) == 5
        assert path.points[0].position.z > 300.0  # Elevated viewpoint

    def test_top_down_camera_generation(self):
        center = Vector3(100.0, 200.0, 0.0)
        path = generate_top_down_camera_path(center, start_tick=200, end_tick=500)
        assert path.camera_type == CameraType.TOP_DOWN
        assert len(path.points) == 4
        for pt in path.points:
            assert pt.rotation.pitch == -89.0


class TestCampathXml:
    def test_validate_campath_requires_points(self):
        path = CameraPath(path_id="empty", camera_type=CameraType.ORBIT_CAMERA)
        with pytest.raises(CampathValidationError):
            validate_campath(path)

    def test_validate_campath_cubic_requires_four_points(self):
        path = CameraPath(
            path_id="few",
            camera_type=CameraType.ORBIT_CAMERA,
            position_interp=InterpolationMode.CUBIC,
            points=[
                CampathPoint(time=1.0, tick=100, position=Vector3(0, 0, 0), rotation=Rotation3(0, 0, 0)),
                CampathPoint(time=2.0, tick=200, position=Vector3(1, 1, 1), rotation=Rotation3(0, 0, 0)),
            ],
        )
        with pytest.raises(CampathValidationError, match="requires at least 4 keyframes"):
            validate_campath(path)

    def test_export_campath_xml(self, tmp_path: pathlib.Path):
        center = Vector3(0.0, 0.0, 0.0)
        path = generate_orbit_camera_path(center, start_tick=100, end_tick=400)
        out_file = tmp_path / "campath_test.xml"
        xml = export_campath_xml(path, out_file)
        assert out_file.exists()
        assert "<campath>" in xml
        assert "<positionInterp>cubic</positionInterp>" in xml
        assert "<points>" in xml
        assert "<t>" in xml
        assert "<rx>0.000</rx>" in xml
