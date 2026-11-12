"""Structured Production Protocol Manifest Manager for dem.Toshka Cinematic Studio.

Generates and serializes the 7 production files:
1. highlight_manifest.json
2. shot_plan.json
3. camera_paths.json
4. capture_manifest.json
5. edit_decision_list.json
6. overlay_events.json
7. render_manifest.json
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

from backend.cinematic.models import (
    CinematicProductionPackage,
    CinematicShot,
    EditDecisionClip,
    OverlayKillEvent,
)


def write_manifests(
    package: CinematicProductionPackage,
    target_directory: pathlib.Path,
) -> dict[str, pathlib.Path]:
    """Write all 7 production manifests to disk.
    
    Returns a dictionary mapping manifest name to its file path.
    """
    target_directory.mkdir(parents=True, exist_ok=True)
    manifest_paths: dict[str, pathlib.Path] = {}

    # 1. highlight_manifest.json
    hl_manifest = {
        "package_id": package.package_id,
        "demo_id": package.demo_id,
        "demo_name": package.demo_name,
        "map_name": package.map_name,
        "created_at": package.created_at,
        "total_shots": len(package.shots),
        "total_duration_seconds": sum(s.duration_seconds for s in package.shots),
    }
    p1 = target_directory / "highlight_manifest.json"
    p1.write_text(json.dumps(hl_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_paths["highlight_manifest"] = p1

    # 2. shot_plan.json
    p2 = target_directory / "shot_plan.json"
    shot_plan = {
        "package_id": package.package_id,
        "shots": [s.to_dict() for s in package.shots],
    }
    p2.write_text(json.dumps(shot_plan, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_paths["shot_plan"] = p2

    # 3. camera_paths.json
    p3 = target_directory / "camera_paths.json"
    camera_paths_data = []
    for s in package.shots:
        if s.campath:
            camera_paths_data.append({
                "shot_id": s.shot_id,
                "path_id": s.campath.path_id,
                "camera_type": s.campath.camera_type.value,
                "points_count": len(s.campath.points),
                "points": [
                    {
                        "time": round(pt.time, 4),
                        "tick": pt.tick,
                        "position": pt.position.to_dict(),
                        "rotation": pt.rotation.to_dict(),
                        "fov": pt.fov,
                    }
                    for pt in s.campath.points
                ],
            })
    p3.write_text(json.dumps(camera_paths_data, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_paths["camera_paths"] = p3

    # 4. capture_manifest.json
    p4 = target_directory / "capture_manifest.json"
    capture_data = {
        "package_id": package.package_id,
        "capture_queue": [
            {
                "shot_id": s.shot_id,
                "output_filename": s.output_filename,
                "start_tick": s.start_tick,
                "end_tick": s.end_tick,
                "fps": s.fps,
                "resolution": s.resolution,
                "hud_mode": s.hud_mode,
                "xray": s.xray,
                "watermark": s.watermark,
                "status": s.validation_status,
            }
            for s in package.shots
            if s.enabled
        ],
    }
    p4.write_text(json.dumps(capture_data, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_paths["capture_manifest"] = p4

    # 5. edit_decision_list.json
    p5 = target_directory / "edit_decision_list.json"
    edl_data = {
        "package_id": package.package_id,
        "timeline_name": package.resolve_project_name or f"CS2_{package.map_name}_Edit",
        "edl_clips": [c.to_dict() for c in package.edl_clips],
    }
    p5.write_text(json.dumps(edl_data, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_paths["edit_decision_list"] = p5

    # 6. overlay_events.json
    p6 = target_directory / "overlay_events.json"
    p6.write_text(
        json.dumps([e.to_dict() for e in package.overlay_events], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    manifest_paths["overlay_events"] = p6

    # 7. render_manifest.json
    p7 = target_directory / "render_manifest.json"
    render_data = {
        "package_id": package.package_id,
        "target_fps": 60,
        "color_space": "Rec.709",
        "video_format": "H.264 / AAC",
        "tracks": {
            "video_track_1": "Hero First-Person Master Action",
            "video_track_2": "Cinematic B-Roll (Shoulder / Flyby / Orbit)",
            "video_track_3": "Victim Reaction Inserts",
            "video_track_4": "Graphical Overlays & Killfeed",
            "audio_track_1": "In-Game Direct 3D Capture Audio (PCM/AAC)",
        },
    }
    p7.write_text(json.dumps(render_data, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_paths["render_manifest"] = p7

    return manifest_paths
