"""Unit tests for Manifest Manager and FCPXML Exporter."""

import json
import pathlib
import xml.etree.ElementTree as ET

from backend.cinematic.manifest_manager import write_manifests
from backend.cinematic.models import (
    CameraType,
    CinematicProductionPackage,
    CinematicShot,
    EditDecisionClip,
    OverlayKillEvent,
    ShotPurpose,
    Vector3,
)
from backend.cinematic.resolve_export import generate_cmx3600_edl, generate_fcpxml


def _create_sample_package() -> CinematicProductionPackage:
    shot1 = CinematicShot(
        shot_id="shot_01",
        highlight_id="hl_01",
        round_number=3,
        camera_type=CameraType.FIRST_PERSON,
        purpose=ShotPurpose.PRIMARY_ACTION,
        start_tick=1000,
        end_tick=1300,
        start_time=10.0,
        end_time=13.0,
        duration_seconds=3.0,
        pov_steam_id="76561198000000001",
        pov_name="Hero",
        output_filename="shot_01_hero.mp4",
    )
    shot2 = CinematicShot(
        shot_id="shot_02",
        highlight_id="hl_01",
        round_number=3,
        camera_type=CameraType.VICTIM_POV,
        purpose=ShotPurpose.VICTIM_REACTION,
        start_tick=1100,
        end_tick=1200,
        start_time=11.0,
        end_time=12.0,
        duration_seconds=1.0,
        pov_steam_id="76561198000000002",
        pov_name="Victim",
        output_filename="shot_02_victim.mp4",
    )
    edl1 = EditDecisionClip(
        track_index=1,
        shot_id="shot_01",
        media_path="/renders/shot_01_hero.mp4",
        source_in_seconds=0.0,
        source_out_seconds=3.0,
        timeline_in_seconds=0.0,
        timeline_out_seconds=3.0,
        clip_name="Hero Master",
    )
    event1 = OverlayKillEvent(
        tick=1150,
        time_seconds=11.5,
        round_number=3,
        killer_name="Hero",
        killer_steam_id="76561198000000001",
        victim_name="Victim",
        victim_steam_id="76561198000000002",
        weapon="ak47",
        headshot=True,
        wallbang=False,
        noscope=False,
        thrusmoke=False,
        attackerblind=False,
        kill_number_in_round=1,
        is_ace=False,
        is_clutch=False,
    )
    return CinematicProductionPackage(
        package_id="pkg_test_01",
        demo_id="demo_123",
        demo_name="test_match.dem",
        map_name="de_mirage",
        created_at="2026-11-12T10:00:00Z",
        shots=[shot1, shot2],
        edl_clips=[edl1],
        overlay_events=[event1],
        output_directory="renders/cinematic",
    )


class TestManifestManager:
    def test_write_manifests_creates_all_seven_files(self, tmp_path: pathlib.Path):
        pkg = _create_sample_package()
        paths = write_manifests(pkg, tmp_path)

        expected_files = [
            "highlight_manifest",
            "shot_plan",
            "camera_paths",
            "capture_manifest",
            "edit_decision_list",
            "overlay_events",
            "render_manifest",
        ]
        for name in expected_files:
            assert name in paths
            assert paths[name].exists()

        # Check JSON parsing
        hl_json = json.loads(paths["highlight_manifest"].read_text(encoding="utf-8"))
        assert hl_json["package_id"] == "pkg_test_01"
        assert hl_json["total_shots"] == 2

        edl_json = json.loads(paths["edit_decision_list"].read_text(encoding="utf-8"))
        assert len(edl_json["edl_clips"]) == 1


class TestResolveExporter:
    def test_generate_fcpxml_valid_structure(self, tmp_path: pathlib.Path):
        pkg = _create_sample_package()
        out_fcpxml = tmp_path / "project.fcpxml"
        xml_str = generate_fcpxml(pkg, fps=60, output_path=out_fcpxml)

        assert out_fcpxml.exists()
        root = ET.fromstring(xml_str)
        assert root.tag == "fcpxml"
        assert root.attrib.get("version") == "1.9"

        # Check resources
        resources = root.find("resources")
        assert resources is not None
        assets = resources.findall("asset")
        assert len(assets) == 2

        # Check markers on hero clip
        markers = root.findall(".//marker")
        assert len(markers) >= 1
        assert "KILL: Hero [ak47] Victim" in markers[0].attrib.get("value", "")

    def test_generate_cmx3600_edl(self, tmp_path: pathlib.Path):
        pkg = _create_sample_package()
        out_edl = tmp_path / "project.edl"
        edl_str = generate_cmx3600_edl(pkg, fps=60, output_path=out_edl)

        assert out_edl.exists()
        assert "TITLE: CS2_Cinematic_Edit" in edl_str
        assert "001  AX       V     C" in edl_str
