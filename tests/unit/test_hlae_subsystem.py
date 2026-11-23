"""Unit tests for HLAE and AfxHookSource2 modern subsystem."""

import pathlib
import xml.etree.ElementTree as ET
import pytest

from backend.hlae.campath import CamKeyframe, HLAECampathManager
from backend.hlae.command_builder import HLAECommandBuilder
from backend.hlae.controller import HLAEController
from backend.hlae.streams import HLAEStreamManager, StreamProfile
from backend.hlae.version import HLAEVersionDetector


def test_hlae_version_detector_real_binaries():
    hlae_exe = pathlib.Path("tools/hlae/HLAE.exe")
    hook_dll = pathlib.Path("tools/hlae/x64/AfxHookSource2.dll")

    if not hlae_exe.exists() or not hook_dll.exists():
        pytest.skip("HLAE binaries not present in tools/hlae/")

    caps = HLAEVersionDetector.detect(hlae_exe, hook_dll)
    assert caps.supports_source2 is True
    assert caps.hlae_version.startswith("2.")
    assert caps.hook_version.startswith("0.")
    assert caps.supports_ffmpeg_escaped_convars is True


def test_hlae_version_detector_missing_files(tmp_path):
    caps = HLAEVersionDetector.detect(tmp_path / "fake.exe", tmp_path / "fake.dll")
    assert caps.supports_source2 is False
    assert caps.hlae_version == "0.0.0"


def test_hlae_command_builder():
    builder = HLAECommandBuilder()
    builder.set_host_framerate(60)
    builder.set_hud_mode("cinematic")
    builder.set_xray(True)
    builder.lock_spectator_pov(12345678)
    builder.add_at_tick(2000, "mirv_streams record end")
    builder.add_at_tick(1000, "mirv_streams record start")

    cfg_text = builder.build_cfg_text()

    assert "host_framerate 60" in cfg_text
    assert "cl_draw_only_deathnotices 1" in cfg_text
    assert "spec_show_xray 1" in cfg_text
    assert "spec_player_by_accountid 12345678" in cfg_text

    # Verify chronological sorting of mirv_cmd directives
    tick_1000_idx = cfg_text.index("mirv_cmd addAtTick 1000")
    tick_2000_idx = cfg_text.index("mirv_cmd addAtTick 2000")
    assert tick_1000_idx < tick_2000_idx


def test_hlae_campath_manager_spline_and_xml(tmp_path):
    manager = HLAECampathManager()
    manager.add_keyframe(0.0, 0.0, 0.0, 64.0, pitch=0.0, yaw=0.0)
    manager.add_keyframe(1.0, 100.0, 50.0, 64.0, pitch=0.0, yaw=45.0)
    manager.add_keyframe(2.0, 200.0, 100.0, 64.0, pitch=0.0, yaw=90.0)
    manager.add_keyframe(3.0, 300.0, 150.0, 64.0, pitch=0.0, yaw=90.0)

    # Catmull-Rom interpolation between points
    interp = manager.interpolate_at_time(1.5)
    assert interp is not None
    assert 100.0 <= interp.x <= 200.0
    assert 50.0 <= interp.y <= 100.0

    # XML Export
    out_xml = tmp_path / "campath_test.xml"
    manager.export_xml(out_xml)
    assert out_xml.exists()

    tree = ET.parse(out_xml)
    root = tree.getroot()
    assert root.tag == "campath"
    points = root.findall(".//point")
    assert len(points) == 4

    # XML Import
    manager2 = HLAECampathManager()
    manager2.import_xml(out_xml)
    assert len(manager2.keyframes) == 4
    assert manager2.keyframes[0].time_seconds == 0.0


def test_hlae_stream_manager(tmp_path):
    mgr = HLAEStreamManager(tmp_path)
    cmds = mgr.apply_profile(StreamProfile.CLEAN_CINEMATIC, base_name="highlight_ace")

    assert any("mirv_streams remove all" in c for c in cmds)
    assert any("mirv_streams add normal highlight_ace_cinematic" in c for c in cmds)
    assert any("mirv_streams edit highlight_ace_cinematic recordAudio 1" in c for c in cmds)

    # AfxHookSource2 {{ }} escaping
    escaped = HLAEStreamManager.format_afx_ffmpeg_options("-c:v libx264 -crf 15")
    assert escaped == "{{ -c:v libx264 -crf 15 }}"


def test_hlae_controller_setup():
    ctrl = HLAEController(
        hlae_exe="tools/hlae/HLAE.exe",
        hook_dll="tools/hlae/x64/AfxHookSource2.dll",
        cs2_exe="D:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/bin/win64/cs2.exe",
    )
    cmd = ctrl.build_launch_args("-steam +exec test.cfg")
    assert "-customLoader" in cmd
    assert "-noGui" in cmd
    assert "-autoStart" in cmd
    assert "-hookDllPath" in cmd
    assert "-cmdLine" in cmd
    assert "-steam +exec test.cfg" in cmd
