import json
import pathlib
import pytest

V3_DIR = pathlib.Path("renders/ACE_FINAL_V3_AUDIO_KILLFEED")

def test_phase32_sfx_library_and_index():
    index_file = V3_DIR / "sound_library_index.json"
    assert index_file.exists(), "sound_library_index.json must exist"
    data = json.loads(index_file.read_text(encoding="utf-8"))
    assert len(data) == 21, "Must contain 21 curated sound assets"
    
    categories = set(item["category"] for item in data)
    assert len(categories) == 7, "Must cover all 7 sound categories"
    for cat in categories:
        cat_dir = V3_DIR / "sfx_library" / cat
        assert cat_dir.exists() and any(cat_dir.iterdir()), f"Category dir {cat} must contain sound files"

def test_phase32_sound_licenses():
    lic_file = V3_DIR / "sound_library_licenses.json"
    assert lic_file.exists(), "sound_library_licenses.json must exist"
    data = json.loads(lic_file.read_text(encoding="utf-8"))
    assert "Sonniss" in data["licensor"] or "Sonniss" in data["license_agreement"]
    assert data["grant_of_rights"]["commercial_use_permitted"] is True

def test_phase32_fairlight_audio_stems_and_master():
    audio_dir = V3_DIR / "audio"
    for i in range(1, 7):
        stem_files = list(audio_dir.glob(f"stem_a{i}_*.wav"))
        assert len(stem_files) == 1, f"Stem A{i} missing"
        assert stem_files[0].stat().st_size > 100000
    master_wav = audio_dir / "audio_master_v3.wav"
    assert master_wav.exists() and master_wav.stat().st_size > 2000000
    assert (V3_DIR / "audio_mix_report.md").exists()

def test_phase32_killfeed_event_manifest():
    manifest_file = V3_DIR / "killfeed_event_manifest.json"
    assert manifest_file.exists(), "killfeed_event_manifest.json must exist"
    events = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert len(events) == 5, "Must contain all 5 ACE kills"
    
    # Check exact demo ticks and frames
    expected = [
        (120927, 470, "Tiger07"),
        (121263, 627, "zuuuuuhhhhn"),
        (121491, 732, "ProfyfGames"),
        (121595, 780, "freekjkeee"),
        (121920, 932, "axuenchik002")
    ]
    for ev, (exp_tick, exp_frame, exp_victim) in zip(events, expected):
        assert ev["tick"] == exp_tick
        assert ev["timeline_frame"] == exp_frame
        assert ev["victim"] == exp_victim
    assert (V3_DIR / "event_to_timeline_mapping_report.md").exists()

def test_phase32_stacked_overlays():
    ov_dir = V3_DIR / "overlays"
    states = ["state_1_kill1", "state_2_kill1_2", "state_3_kill1_2_3", "state_4_kill2_3_4", "state_5_kill3_4_5"]
    for s in states:
        assert (ov_dir / f"killfeed_16x9_{s}.png").exists(), f"16:9 overlay for {s} missing"
        assert (ov_dir / f"killfeed_tiktok_{s}.png").exists(), f"TikTok overlay for {s} missing"
    assert (ov_dir / "ace_card_16x9.png").exists()
    assert (ov_dir / "ace_card_tiktok.png").exists()

def test_phase32_video_deliverables():
    master_mp4 = V3_DIR / "ACE_FINAL_V3_MASTER.mp4"
    tiktok_mp4 = V3_DIR / "ACE_FINAL_V3_TIKTOK.mp4"
    preview_mp4 = V3_DIR / "ACE_FINAL_V3_PREVIEW.mp4"
    assert master_mp4.exists() and master_mp4.stat().st_size > 20000000
    assert tiktok_mp4.exists() and tiktok_mp4.stat().st_size > 20000000
    assert preview_mp4.exists() and preview_mp4.stat().st_size > 5000000

def test_phase32_davinci_resolve_assets():
    drp_file = V3_DIR / "ACE_FINAL_V3.drp"
    fcpxml_file = V3_DIR / "ACE_FINAL_V3.fcpxml"
    assert drp_file.exists() and drp_file.stat().st_size > 10000
    assert fcpxml_file.exists()

def test_phase32_qa_reports_and_contact_sheets():
    qa_dir = V3_DIR / "qa"
    assert (qa_dir / "qa_kill_sync_contact_sheet.png").exists()
    assert (qa_dir / "qa_v3_master_contact_sheet.png").exists()
    assert (qa_dir / "qa_v3_tiktok_contact_sheet.png").exists()
    assert (qa_dir / "qc_report_summary.json").exists()
    qc_data = json.loads((qa_dir / "qc_report_summary.json").read_text(encoding="utf-8"))
    for stream_key in ["master_16x9", "tiktok_9x16", "preview_16x9"]:
        assert qc_data[stream_key]["qc_checks"]["fps_60_verified"] is True
        assert qc_data[stream_key]["qc_checks"]["duration_match"] is True
        assert qc_data[stream_key]["qc_checks"]["progressive_scan"] is True
        assert qc_data[stream_key]["qc_checks"]["audio_active"] is True
        assert qc_data[stream_key]["qc_checks"]["watermark_free"] is True

def test_phase32_audio_video_synchronization():
    import scipy.io.wavfile as wavfile
    import numpy as np
    
    stem_a1 = V3_DIR / "audio" / "stem_a1_gameplay.wav"
    assert stem_a1.exists(), "Stem A1 must exist"
    sr, data = wavfile.read(str(stem_a1))
    
    # In uncorrected version, gunshot occurred at ~5.56s (2.15s before video)
    # Check that before 7.0s, gunshot energy is low (only footsteps / approach)
    early_chunk = np.abs(data[int(5.0 * sr):int(6.5 * sr), 0])
    early_max = np.max(early_chunk)
    
    # Check gunshot transient around Kill 1 (7.5s - 8.0s)
    k1_chunk = np.abs(data[int(7.5 * sr):int(8.0 * sr), 0])
    k1_max = np.max(k1_chunk)
    k1_t = 7.5 + np.argmax(k1_chunk) / sr
    
    assert 7.65 <= k1_t <= 7.85, f"Gunshot audio transient at {k1_t:.3f}s must align with video Kill 1 (7.83s)"
    assert k1_max > 2.0 * early_max, "Kill 1 gunshot transient must be significantly louder than pre-peek approach"
