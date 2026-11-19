"""Unit tests for the Cinematic Studio Integration Bridge & Manifest Protocol."""

from __future__ import annotations

import json
import pathlib
import pytest

from backend.integration.studio_bridge import (
    ClipSpecificationManifest,
    DemoMetadataManifest,
    EventItemManifest,
    PlayerActorManifest,
    ProductionRequestManifest,
    SocialPostDraftGenerator,
    StudioAvailabilityDetector,
    StudioJobLauncher,
    StudioJobManifest,
    StudioJobStatusProvider,
)


@pytest.fixture
def sample_manifest() -> StudioJobManifest:
    demo = DemoMetadataManifest(
        identifier="demo_123",
        file_path="C:\\CS2\\match.dem",
        checksum_sha256="abcdef1234567890",
        map="de_mirage",
        tickrate=128,
        match_date="2026-11-19T12:00:00Z",
    )
    clip = ClipSpecificationManifest(
        round_num=5,
        start_tick=10000,
        end_tick=12000,
        highlight_type="ace",
        highlight_score=95.0,
        score_explanation="Clean ACE with AWP",
        tags=["ace", "awp"],
    )
    actors = {
        "primary_player": {
            "steam_id": "76561198000000001",
            "name": "pytoshka_",
            "team": "ct",
            "pov_preference": "first_person",
        }
    }
    events = [
        EventItemManifest(
            tick=10500,
            event_type="kill",
            attacker_steam_id="76561198000000001",
            victim_steam_id="76561198000000002",
            weapon="awp",
            headshot=True,
            wallbang=False,
            kill_number_in_sequence=1,
        )
    ]
    prod = ProductionRequestManifest(
        profile="clean_cinematic",
        resolution="1920x1080",
        fps=60,
        hud_mode="killfeed_only",
    )
    return StudioJobManifest(
        version="1.0.0",
        job_id="job_test_001",
        created_at="2026-11-19T12:00:00Z",
        demo=demo,
        clip=clip,
        actors=actors,
        events=events,
        production_request=prod,
    )


class TestStudioBridge:
    def test_availability_detector_status(self):
        status = StudioAvailabilityDetector.get_studio_status()
        assert "available" in status
        assert "manifest_schema" in status
        assert status["manifest_schema"] == "1.0.0"
        assert isinstance(status["supported_profiles"], list)

    def test_manifest_serialization_roundtrip(self, sample_manifest: StudioJobManifest):
        json_str = sample_manifest.to_json()
        data = json.loads(json_str)

        assert data["version"] == "1.0.0"
        assert data["job_id"] == "job_test_001"
        assert data["demo"]["map"] == "de_mirage"
        assert data["clip"]["highlight_type"] == "ace"
        assert len(data["events"]) == 1
        assert data["events"][0]["weapon"] == "awp"

        # Deserialize back
        reconstructed = StudioJobManifest.from_dict(data)
        assert reconstructed.job_id == sample_manifest.job_id
        assert reconstructed.demo.map == sample_manifest.demo.map
        assert reconstructed.clip.highlight_score == 95.0
        assert reconstructed.events[0].headshot is True

    def test_job_launcher_and_status_provider(self, tmp_path: pathlib.Path, sample_manifest: StudioJobManifest):
        launcher = StudioJobLauncher(manifests_dir=tmp_path)
        status_provider = StudioJobStatusProvider(manifests_dir=tmp_path)

        # Before submission
        st_before = status_provider.get_status("job_test_001")
        assert st_before["status"] == "not_found"

        # Submit job
        saved_file = launcher.submit_job(sample_manifest)
        assert saved_file.exists()
        assert saved_file.name == "job_test_001.json"

        # Now status should be pending
        st_pending = status_provider.get_status("job_test_001")
        assert st_pending["status"] == "pending"
        assert st_pending["stage"] == "queued_for_studio"

        # Simulate completed status written by Cinematic Studio
        status_dir = tmp_path / "status"
        status_dir.mkdir(parents=True, exist_ok=True)
        completed_status = {
            "job_id": "job_test_001",
            "status": "completed",
            "progress_pct": 100.0,
            "stage": "done",
            "output_assets": [{"file_path": "C:\\renders\\clip.mp4"}],
        }
        (status_dir / "job_test_001.json").write_text(json.dumps(completed_status), encoding="utf-8")

        st_done = status_provider.get_status("job_test_001")
        assert st_done["status"] == "completed"
        assert st_done["progress_pct"] == 100.0
        assert len(st_done["output_assets"]) == 1

    def test_social_post_draft_generator(self):
        draft_tg = SocialPostDraftGenerator.generate_draft(
            player_name="pytoshka_",
            map_name="de_mirage",
            highlight_type="ace",
            primary_weapon="awp",
            round_num=12,
            kill_count=5,
            score=98.5,
            duration_sec=7.2,
            platform="telegram",
        )
        assert "pytoshka_" in draft_tg
        assert "ACE" in draft_tg
        assert "Mirage" in draft_tg
        assert "AWP" in draft_tg
        assert "98.5" in draft_tg
        assert "#CS2" in draft_tg

        draft_yt = SocialPostDraftGenerator.generate_draft(
            player_name="pytoshka_",
            map_name="de_anubis",
            highlight_type="clutch_1v3",
            primary_weapon="ak47",
            round_num=15,
            kill_count=3,
            score=91.0,
            duration_sec=14.0,
            platform="youtube_shorts",
        )
        assert "Shorts" in draft_yt
        assert "dem.Toshka" in draft_yt

        draft_tt = SocialPostDraftGenerator.generate_draft(
            player_name="pytoshka_",
            map_name="de_nuke",
            highlight_type="ace",
            primary_weapon="m4a1_silencer",
            round_num=8,
            kill_count=5,
            score=94.0,
            duration_sec=9.5,
            platform="tiktok",
        )
        assert "#cs2clips" in draft_tt
