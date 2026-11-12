import json
import pathlib
import pytest

PHASE31_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX")

def test_phase31_audio_beat_map():
    beat_map_file = PHASE31_DIR / "audio" / "music_beat_map.json"
    assert beat_map_file.exists(), "music_beat_map.json must exist"
    data = json.loads(beat_map_file.read_text(encoding="utf-8"))
    assert data["bpm"] == 142.0, "Must be 142 BPM"
    assert "LOVELYDILLER" in data["track_name"], "Must be authentic LOVELYDILLER song"
    assert len(data["timeline_kills"]) == 5, "Must contain all 5 ACE kills"
    assert data["timeline_drop_s"] == 8.18, "Drop must sync with Kill 1 at 8.18s"

def test_phase31_sound_design_manifest():
    manifest_file = PHASE31_DIR / "audio" / "sound_design_manifest.json"
    assert manifest_file.exists(), "sound_design_manifest.json must exist"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert len(data["tracks"]) == 5, "Must define 5 Fairlight audio tracks (A1-A5)"
    master_wav = PHASE31_DIR / "audio" / data["master_output"]
    assert master_wav.exists() and master_wav.stat().st_size > 1000000, "Master audio mixdown must exist"

def test_phase31_color_grading_lut():
    lut_file = PHASE31_DIR / "color" / "egyptian_sandstone_cinematic.cube"
    assert lut_file.exists(), "3D LUT cube file must exist"
    content = lut_file.read_text(encoding="utf-8")
    assert "LUT_3D_SIZE 33" in content, "Must be 33x33x33 3D LUT"
    assert (PHASE31_DIR / "color" / "color_grade_manifest.json").exists()

def test_phase31_fusion_compositions():
    fusion_dir = PHASE31_DIR / "fusion"
    assert (fusion_dir / "WhipPan_MotionBlur.comp").exists(), "WhipPan_MotionBlur.comp must exist"
    assert (fusion_dir / "Directional_ZoomBlur.comp").exists(), "Directional_ZoomBlur.comp must exist"
    assert (fusion_dir / "Impact_Flash_Chroma.comp").exists(), "Impact_Flash_Chroma.comp must exist"
    assert (fusion_dir / "README.md").exists()

def test_phase31_motion_overlays():
    overlay_dir = PHASE31_DIR / "overlays"
    for k in range(1, 6):
        assert (overlay_dir / f"badge_16x9_kill_{k}.png").exists(), f"16:9 badge for kill {k} missing"
        assert (overlay_dir / f"badge_tiktok_kill_{k}.png").exists(), f"TikTok badge for kill {k} missing"
    assert (overlay_dir / "ace_card_16x9.png").exists()
    assert (overlay_dir / "ace_card_tiktok.png").exists()
    assert (overlay_dir / "intro_card_16x9.png").exists()
    assert (overlay_dir / "intro_card_tiktok.png").exists()

def test_phase31_video_deliverables():
    master_mp4 = PHASE31_DIR / "ACE_FINAL_V2_MASTER.mp4"
    tiktok_mp4 = PHASE31_DIR / "ACE_FINAL_V2_TIKTOK.mp4"
    preview_mp4 = PHASE31_DIR / "ACE_FINAL_V2_PREVIEW.mp4"
    assert master_mp4.exists() and master_mp4.stat().st_size > 10000000, "16:9 Master must exist and > 10MB"
    assert tiktok_mp4.exists() and tiktok_mp4.stat().st_size > 10000000, "9:16 TikTok must exist and > 10MB"
    assert preview_mp4.exists() and preview_mp4.stat().st_size > 5000000, "16:9 Preview must exist and > 5MB"

def test_phase31_davinci_resolve_project_assets():
    drp_file = PHASE31_DIR / "ACE_FINAL_V2.drp"
    fcpxml_file = PHASE31_DIR / "ACE_FINAL_V2.fcpxml"
    assert drp_file.exists() and drp_file.stat().st_size > 10000, "DaVinci Resolve project archive must exist"
    assert fcpxml_file.exists(), "FCPXML timeline must exist"

def test_phase31_qc_report_and_contact_sheets():
    qc_file = PHASE31_DIR / "qa" / "qc_report_summary.json"
    assert qc_file.exists(), "QC summary JSON must exist"
    qc_data = json.loads(qc_file.read_text(encoding="utf-8"))
    for stream_key in ["master_16x9", "tiktok_9x16", "preview_16x9"]:
        assert qc_data[stream_key]["qc_checks"]["fps_60_verified"] is True
        assert qc_data[stream_key]["qc_checks"]["duration_match"] is True
        assert qc_data[stream_key]["qc_checks"]["progressive_scan"] is True
        assert qc_data[stream_key]["qc_checks"]["audio_active"] is True
        assert qc_data[stream_key]["qc_checks"]["watermark_free"] is True
    assert (PHASE31_DIR / "qa" / "qa_contact_sheet.png").exists(), "16:9 contact sheet must exist"
    assert (PHASE31_DIR / "qa" / "qa_contact_sheet_tiktok.png").exists(), "TikTok contact sheet must exist"
