"""Camera Path Generator and Catmull-Rom Spline Interpolator for HLAE mirv_campath."""

from __future__ import annotations

import math
import pathlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional


@dataclass
class CamKeyframe:
    """A single 3D camera keyframe with position, orientation, and field of view."""

    time_seconds: float
    x: float
    y: float
    z: float
    pitch: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0
    fov: float = 90.0

    def calculate_look_at(self, target_x: float, target_y: float, target_z: float) -> None:
        """Compute pitch and yaw to orient the camera directly towards the target coordinate."""
        dx = target_x - self.x
        dy = target_y - self.y
        dz = target_z - self.z
        dist_xy = math.sqrt(dx * dx + dy * dy)
        if dist_xy > 1e-4:
            self.yaw = math.degrees(math.atan2(dy, dx))
            self.pitch = -math.degrees(math.atan2(dz, dist_xy))


class HLAECampathManager:
    """Manages creation, mathematical interpolation, and XML serialization of HLAE camera paths."""

    def __init__(self, keyframes: Optional[list[CamKeyframe]] = None) -> None:
        self.keyframes: list[CamKeyframe] = keyframes or []

    def add_keyframe(
        self,
        time_or_kf: float | CamKeyframe,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
        roll: float = 0.0,
        fov: float = 90.0,
        tick: Optional[int] = None,
        tickrate: float = 64.0,
    ) -> CamKeyframe:
        if isinstance(time_or_kf, CamKeyframe):
            kf = time_or_kf
        else:
            time_s = time_or_kf if tick is None else (tick / max(1.0, float(tickrate)))
            kf = CamKeyframe(
                time_seconds=float(time_s),
                x=float(x),
                y=float(y),
                z=float(z),
                pitch=float(pitch),
                yaw=float(yaw),
                roll=float(roll),
                fov=float(fov),
            )
        self.keyframes.append(kf)
        self.keyframes.sort(key=lambda k: k.time_seconds)
        return kf

    @classmethod
    def create_orbit(
        cls,
        center_x: float,
        center_y: float,
        center_z: float,
        radius: float = 240.0,
        height_offset: float = 40.0,
        start_angle_deg: float = 0.0,
        end_angle_deg: float = 360.0,
        duration_s: float = 5.0,
        num_points: int = 16,
        fov: float = 75.0,
    ) -> HLAECampathManager:
        """Create a smooth 360-degree rotational orbit camera around a focal point."""
        manager = cls()
        for i in range(num_points):
            t = (i / (num_points - 1)) * duration_s
            angle_rad = math.radians(start_angle_deg + (end_angle_deg - start_angle_deg) * (i / (num_points - 1)))
            cam_x = center_x + radius * math.cos(angle_rad)
            cam_y = center_y + radius * math.sin(angle_rad)
            cam_z = center_z + height_offset

            kf = CamKeyframe(time_seconds=round(t, 4), x=round(cam_x, 2), y=round(cam_y, 2), z=round(cam_z, 2), fov=fov)
            kf.calculate_look_at(center_x, center_y, center_z + 30.0)
            manager.add_keyframe(kf)
        return manager

    @classmethod
    def create_flyby(
        cls,
        target_x: float,
        target_y: float,
        target_z: float,
        start_offset: tuple[float, float, float] = (-300.0, -150.0, 80.0),
        end_offset: tuple[float, float, float] = (300.0, 150.0, 40.0),
        duration_s: float = 3.5,
        num_points: int = 10,
        fov: float = 80.0,
    ) -> HLAECampathManager:
        """Create a cinematic linear flyby sweeping across an engagement area."""
        manager = cls()
        for i in range(num_points):
            alpha = i / (num_points - 1)
            t = alpha * duration_s
            # Smooth ease-in ease-out (smoothstep)
            ease_alpha = alpha * alpha * (3.0 - 2.0 * alpha)

            cur_x = target_x + start_offset[0] + (end_offset[0] - start_offset[0]) * ease_alpha
            cur_y = target_y + start_offset[1] + (end_offset[1] - start_offset[1]) * ease_alpha
            cur_z = target_z + start_offset[2] + (end_offset[2] - start_offset[2]) * ease_alpha

            kf = CamKeyframe(time_seconds=round(t, 4), x=round(cur_x, 2), y=round(cur_y, 2), z=round(cur_z, 2), fov=fov)
            kf.calculate_look_at(target_x, target_y, target_z + 20.0)
            manager.add_keyframe(kf)
        return manager

    def interpolate_at_time(self, time_s: float) -> Optional[CamKeyframe]:
        """Interpolate camera state at time_s using Catmull-Rom cubic splines."""
        if not self.keyframes:
            return None
        if len(self.keyframes) == 1:
            return self.keyframes[0]
        if time_s <= self.keyframes[0].time_seconds:
            return self.keyframes[0]
        if time_s >= self.keyframes[-1].time_seconds:
            return self.keyframes[-1]

        # Find interval
        idx = 0
        while idx < len(self.keyframes) - 1 and self.keyframes[idx + 1].time_seconds < time_s:
            idx += 1

        k1 = self.keyframes[idx]
        k2 = self.keyframes[idx + 1]
        k0 = self.keyframes[max(0, idx - 1)]
        k3 = self.keyframes[min(len(self.keyframes) - 1, idx + 2)]

        span = k2.time_seconds - k1.time_seconds
        u = 0.0 if span <= 1e-6 else (time_s - k1.time_seconds) / span

        def _catmull(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
            return 0.5 * (
                (2.0 * p1)
                + (-p0 + p2) * t
                + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * (t * t)
                + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * (t * t * t)
            )

        ix = _catmull(k0.x, k1.x, k2.x, k3.x, u)
        iy = _catmull(k0.y, k1.y, k2.y, k3.y, u)
        iz = _catmull(k0.z, k1.z, k2.z, k3.z, u)
        ipitch = _catmull(k0.pitch, k1.pitch, k2.pitch, k3.pitch, u)
        iyaw = _catmull(k0.yaw, k1.yaw, k2.yaw, k3.yaw, u)
        iroll = _catmull(k0.roll, k1.roll, k2.roll, k3.roll, u)
        ifov = _catmull(k0.fov, k1.fov, k2.fov, k3.fov, u)

        return CamKeyframe(time_seconds=time_s, x=ix, y=iy, z=iz, pitch=ipitch, yaw=iyaw, roll=iroll, fov=ifov)

    def interpolate_at_tick(self, tick: int, tickrate: float = 64.0) -> Optional[CamKeyframe]:
        """Interpolate camera state at demo tick."""
        time_s = tick / max(1.0, float(tickrate))
        return self.interpolate_at_time(time_s)

    def import_xml(self, xml_path: pathlib.Path) -> HLAECampathManager:
        """Import keyframes from an XML file into this manager instance."""
        loaded = self.load_xml(xml_path)
        self.keyframes = loaded.keyframes
        return self

    def export_xml(self, output_path: pathlib.Path) -> pathlib.Path:
        """Export keyframes to standard HLAE mirv_campath XML file."""
        root = ET.Element("campath", version="1")
        points_elem = ET.SubElement(root, "points")

        for kf in self.keyframes:
            pt = ET.SubElement(points_elem, "point")
            ET.SubElement(pt, "time").text = f"{kf.time_seconds:.6f}"
            ET.SubElement(pt, "x").text = f"{kf.x:.2f}"
            ET.SubElement(pt, "y").text = f"{kf.y:.2f}"
            ET.SubElement(pt, "z").text = f"{kf.z:.2f}"
            ET.SubElement(pt, "pitch").text = f"{kf.pitch:.2f}"
            ET.SubElement(pt, "yaw").text = f"{kf.yaw:.2f}"
            ET.SubElement(pt, "roll").text = f"{kf.roll:.2f}"
            ET.SubElement(pt, "fov").text = f"{kf.fov:.2f}"

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(str(output_path), encoding="utf-8", xml_declaration=True)
        return output_path

    @classmethod
    def load_xml(cls, xml_path: pathlib.Path) -> HLAECampathManager:
        """Load an existing mirv_campath XML file into memory."""
        tree = ET.parse(str(xml_path))
        root = tree.getroot()
        manager = cls()

        for pt in root.findall(".//point"):
            t = float(pt.findtext("time", "0.0"))
            x = float(pt.findtext("x", "0.0"))
            y = float(pt.findtext("y", "0.0"))
            z = float(pt.findtext("z", "0.0"))
            pitch = float(pt.findtext("pitch", "0.0"))
            yaw = float(pt.findtext("yaw", "0.0"))
            roll = float(pt.findtext("roll", "0.0"))
            fov = float(pt.findtext("fov", "90.0"))
            manager.add_keyframe(CamKeyframe(t, x, y, z, pitch, yaw, roll, fov))

        return manager
