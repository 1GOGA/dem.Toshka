"""
Unit tests for dem.Toshka Cinematic Studio Phase 3.4 — AI Fragmovie Reference Lab.

Covers:
- Reference analyzer directory hierarchy and inbox discovery
- Technical video probing via ffprobe
- Adaptive scene cut and transition classification
- Audio beat tracking, BPM detection and sub-bass impact alignment
- Color grading palette clustering and mood extraction
- Motion speed ramp profiling and punch-in detection
- Contact sheet generation and persistence
- Pattern catalog maintenance and profile filtering (HYBRID, HYPE, CINEMATIC)
- Authoritative Pytoshka Style Guide validation
- FastAPI Reference Lab endpoints
"""

import json
import pathlib
import pytest

from backend.cinematic.reference_analyzer import (
    FragmovieReferenceAnalyzer,
    ReferenceVideoMetadata,
    SceneCut,
    AudioBeatInfo,
    ColorPaletteInfo,
    MotionSpeedSegment,
    ExtractedPattern,
    BASE_REF_DIR,
    INBOX_DIR,
    ANALYZED_DIR,
    CONTACT_SHEETS_DIR,
    PATTERNS_DIR,
    INDEX_FILE,
    PATTERNS_MASTER_FILE,
)
from backend.api.main import (
    get_reference_inbox,
    scan_reference_inbox,
    list_analyzed_references,
    get_reference_report,
    get_editing_patterns,
    get_style_guide,
    get_contact_sheet_image,
)


class TestReferenceAnalyzerEngine:
    """Validates local multimodal analysis engine behavior and data structures."""

    @pytest.fixture
    def analyzer(self):
        return FragmovieReferenceAnalyzer()

    def test_directory_hierarchy_exists(self, analyzer):
        assert analyzer.inbox_dir.exists()
        assert analyzer.analyzed_dir.exists()
        assert analyzer.contact_sheets_dir.exists()
        assert analyzer.patterns_dir.exists()

    def test_scan_inbox_discovers_staged_references(self, analyzer):
        inbox_files = analyzer.scan_inbox()
        assert len(inbox_files) >= 1, "At least one staged reference video should be in inbox"
        assert all(f.suffix.lower() in (".mp4", ".mov", ".mkv", ".avi", ".webm") for f in inbox_files)

    def test_probe_video_extracts_technical_metadata(self, analyzer):
        inbox_files = analyzer.scan_inbox()
        assert len(inbox_files) > 0
        target = inbox_files[0]

        meta = analyzer.probe_video(target)
        assert isinstance(meta, ReferenceVideoMetadata)
        assert meta.width >= 1280
        assert meta.height >= 720
        assert meta.fps >= 24.0
        assert meta.duration_seconds > 0.0
        assert len(meta.sha256) == 64
        assert meta.video_id.startswith("ref_")

    def test_detect_cuts_returns_structured_cuts(self, analyzer):
        inbox_files = analyzer.scan_inbox()
        target = inbox_files[0]
        meta = analyzer.probe_video(target)

        cuts = analyzer.detect_cuts_and_transitions(target, meta)
        assert isinstance(cuts, list)
        for cut in cuts:
            assert isinstance(cut, SceneCut)
            assert cut.time_seconds >= 0.0
            assert cut.transition_type in (
                "HARD_CUT", "WHIP_PAN", "ZOOM_IN_OUT", "FLASH_IMPACT", "DISSOLVE", "SPEED_RAMP_CUT"
            )
            assert 0.0 <= cut.confidence <= 1.0

    def test_analyze_audio_tracks_bpm_and_sub_bass(self, analyzer):
        inbox_files = analyzer.scan_inbox()
        target = inbox_files[0]
        meta = analyzer.probe_video(target)

        if meta.has_audio:
            audio = analyzer.analyze_audio(target, meta)
            assert isinstance(audio, AudioBeatInfo)
            assert 60.0 <= audio.bpm <= 200.0
            assert isinstance(audio.beat_times, list)
            assert isinstance(audio.drop_times, list)
            assert isinstance(audio.energy_peaks, list)

    def test_color_grading_clusters_palette(self, analyzer):
        inbox_files = analyzer.scan_inbox()
        target = inbox_files[0]
        meta = analyzer.probe_video(target)

        sample_times = [0.5, min(2.0, meta.duration_seconds * 0.5)]
        palette = analyzer.analyze_color_grading(target, sample_times)
        assert isinstance(palette, ColorPaletteInfo)
        assert len(palette.dominant_colors_hex) == 5
        assert all(c.startswith("#") for c in palette.dominant_colors_hex)
        assert palette.shadow_tint_hex.startswith("#")
        assert palette.highlight_tint_hex.startswith("#")
        assert 0.0 <= palette.average_saturation <= 1.0

    def test_extract_patterns_generates_davinci_recipes(self, analyzer):
        inbox_files = analyzer.scan_inbox()
        target = inbox_files[0]
        meta = analyzer.probe_video(target)
        cuts = analyzer.detect_cuts_and_transitions(target, meta)
        audio = analyzer.analyze_audio(target, meta) if meta.has_audio else None
        color = analyzer.analyze_color_grading(target, [0.5])
        motion = analyzer.analyze_motion_and_speed(target, meta, cuts)

        patterns = analyzer.extract_patterns(meta, cuts, audio, color, motion)
        assert len(patterns) >= 1
        for p in patterns:
            assert isinstance(p, ExtractedPattern)
            assert p.category in (
                "DIRECTING", "TRANSITION", "SPEED_RAMP", "COLOR_GRADING", "SOUND_DESIGN", "CAMERA_WORK", "TYPOGRAPHY"
            )
            assert p.confidence in ("OBSERVED", "INFERRED", "RECOMMENDED", "VERIFIED_IN_RESOLVE")
            assert "page" in p.davinci_resolve_recipe
            assert any(prof in p.style_profile_affinity for prof in ("HYBRID", "HYPE", "CINEMATIC"))

    def test_query_patterns_by_profile(self, analyzer):
        hybrid = analyzer.query_patterns_by_profile("HYBRID")
        hype = analyzer.query_patterns_by_profile("HYPE")
        cinematic = analyzer.query_patterns_by_profile("CINEMATIC")

        assert isinstance(hybrid, list)
        assert isinstance(hype, list)
        assert isinstance(cinematic, list)
        assert len(hybrid) > 0


class TestPatternCatalogsAndStyleGuide:
    """Validates persistent catalogs, index files, and the authoritative Pytoshka Style Guide."""

    def test_reference_index_exists_and_populated(self):
        assert INDEX_FILE.exists(), "reference_index.json must exist"
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert len(data) >= 1, "At least one reference must be indexed"
        first = next(iter(data.values()))
        assert "reference_id" in first
        assert "filename" in first
        assert "duration_seconds" in first
        assert "cuts_count" in first

    def test_category_catalogs_exist_and_valid_json(self):
        catalog_files = [
            "transitions.json",
            "speedramps.json",
            "color_grading.json",
            "sound_design.json",
            "camera_work.json",
            "typography.json",
        ]
        for cf in catalog_files:
            p = PATTERNS_DIR / cf
            assert p.exists(), f"Pattern catalog {cf} must exist"
            data = json.loads(p.read_text(encoding="utf-8"))
            assert isinstance(data, dict), f"{cf} must be a JSON object of patterns"

    def test_master_editing_patterns_json(self):
        assert PATTERNS_MASTER_FILE.exists()
        master = json.loads(PATTERNS_MASTER_FILE.read_text(encoding="utf-8"))
        assert len(master) >= 5, f"Expected at least 5 editing patterns, got {len(master)}"

    def test_pytoshka_style_guide_integrity(self):
        guide_path = pathlib.Path("reference_library/PYTOSHKA_STYLE_GUIDE.md")
        assert guide_path.exists(), "PYTOSHKA_STYLE_GUIDE.md must exist"
        text = guide_path.read_text(encoding="utf-8")
        assert "PYTOSHKA FRAGMOVIE STYLE GUIDE" in text
        assert "Narrative Pacing & The 9 Storyboard Scenes" in text
        assert "Camera Choreography Matrix" in text
        assert "Visual Transitions & Fusion Recipes" in text
        assert "Speed Ramping & Motion Design" in text
        assert "Fairlight 6-Track Sound Design Architecture" in text
        assert "Typography & Overlay Standards" in text

    def test_skill_file_integrity(self):
        skill_path = pathlib.Path(".agents/skills/fragmovie-reference-analysis/SKILL.md")
        assert skill_path.exists(), "SKILL.md must exist"
        text = skill_path.read_text(encoding="utf-8")
        assert "fragmovie-reference-analysis" in text
        assert "multimodal" in text.lower()


class TestReferenceLabAPIEndpoints:
    """Validates FastAPI Reference Lab endpoints directly."""

    def test_get_reference_inbox_api(self):
        res = get_reference_inbox()
        assert "count" in res
        assert "items" in res
        assert res["count"] >= 1
        first = res["items"][0]
        assert "filename" in first
        assert "size_mb" in first
        assert "analyzed" in first

    def test_scan_reference_inbox_api(self):
        res = scan_reference_inbox()
        assert res["status"] == "success"
        assert res["scanned_count"] >= 1
        assert isinstance(res["files"], list)

    def test_list_analyzed_references_api(self):
        res = list_analyzed_references()
        assert "count" in res
        assert "references" in res
        assert res["count"] >= 1

    def test_get_reference_report_api(self):
        idx_res = list_analyzed_references()
        first_ref = idx_res["references"][0]
        ref_id = first_ref["reference_id"]

        report = get_reference_report(ref_id)
        assert report["reference_id"] == ref_id
        assert "metadata" in report
        assert "cuts" in report
        assert "color_grading" in report

    def test_get_editing_patterns_api_filters(self):
        # All patterns
        res_all = get_editing_patterns(profile=None, category=None)
        assert res_all["count"] >= 5

        # Profile filter
        res_hype = get_editing_patterns(profile="HYPE", category=None)
        assert res_hype["count"] >= 1

        # Category filter
        res_trans = get_editing_patterns(profile=None, category="TRANSITION")
        assert res_trans["count"] >= 1
        for p in res_trans["patterns"]:
            assert p["category"] == "TRANSITION"

    def test_get_style_guide_api(self):
        res = get_style_guide()
        assert "content" in res
        assert "path" in res
        assert "PYTOSHKA" in res["content"]
