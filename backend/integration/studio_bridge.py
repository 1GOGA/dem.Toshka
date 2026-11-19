"""Cinematic Studio Integration Bridge & Manifest Protocol (v1.0.0).

Defines the contract between the main dem.Toshka analysis application and the
optional separate dem.Toshka Cinematic Studio extension.

The main application:
1. Detects whether Cinematic Studio is available locally (StudioAvailabilityDetector).
2. Generates structured, versioned StudioJobManifests (v1.0.0) from detected highlights.
3. Submits job requests to the manifests/ queue directory (StudioJobLauncher).
4. Monitors job status reports (StudioJobStatusProvider).
5. Imports completed MP4 renders back into the dem.Toshka library (RenderedAssetImporter).
6. Generates content descriptions and social media drafts (SocialPostDraftGenerator).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import pathlib
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MANIFEST_SCHEMA_VERSION = "1.0.0"
DEFAULT_MANIFESTS_DIR = pathlib.Path("manifests")
DEFAULT_JOBS_DIR = DEFAULT_MANIFESTS_DIR / "jobs"
DEFAULT_STATUS_DIR = DEFAULT_MANIFESTS_DIR / "status"


@dataclass
class DemoMetadataManifest:
    identifier: str
    file_path: str
    checksum_sha256: str
    map: str
    tickrate: int = 128
    match_date: Optional[str] = None


@dataclass
class ClipSpecificationManifest:
    round_num: int
    start_tick: int
    end_tick: int
    highlight_type: str
    highlight_score: float
    score_explanation: str
    tags: List[str] = field(default_factory=list)


@dataclass
class PlayerActorManifest:
    steam_id: Optional[str]
    name: str
    team: Optional[str] = None
    pov_preference: str = "first_person"
    role: str = "hero"


@dataclass
class EventItemManifest:
    tick: int
    event_type: str
    attacker_steam_id: Optional[str]
    victim_steam_id: Optional[str]
    weapon: Optional[str] = None
    headshot: bool = False
    wallbang: bool = False
    kill_number_in_sequence: int = 1


@dataclass
class ProductionRequestManifest:
    profile: str = "clean_cinematic"  # 'clean_cinematic' | 'broadcast_esports' | 'tiktok_vertical'
    resolution: str = "1920x1080"
    fps: int = 60
    hud_mode: str = "killfeed_only"    # 'killfeed_only' | 'tournament_hud' | 'full_hud'
    custom_camera_allowed: bool = True
    user_notes: str = ""
    output_directory: Optional[str] = None


@dataclass
class StudioJobManifest:
    """The official versioned contract sent to Cinematic Studio."""

    version: str
    job_id: str
    created_at: str
    demo: DemoMetadataManifest
    clip: ClipSpecificationManifest
    actors: Dict[str, Any]
    events: List[EventItemManifest]
    production_request: ProductionRequestManifest

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StudioJobManifest:
        demo = DemoMetadataManifest(**data["demo"])
        clip = ClipSpecificationManifest(**data["clip"])
        events = [EventItemManifest(**e) for e in data.get("events", [])]
        prod = ProductionRequestManifest(**data.get("production_request", {}))
        return cls(
            version=data.get("version", MANIFEST_SCHEMA_VERSION),
            job_id=data["job_id"],
            created_at=data["created_at"],
            demo=demo,
            clip=clip,
            actors=data.get("actors", {}),
            events=events,
            production_request=prod,
        )


class StudioAvailabilityDetector:
    """Checks whether Cinematic Studio is available and installed locally."""

    @staticmethod
    def is_studio_available(base_dir: Optional[pathlib.Path] = None) -> bool:
        """Check for Cinematic Studio binaries, env vars, or workspace sibling folder."""
        # 1. Environment variable override
        if os.getenv("DEMTOSHKA_CINEMATIC_STUDIO_DIR"):
            p = pathlib.Path(os.environ["DEMTOSHKA_CINEMATIC_STUDIO_DIR"])
            if p.exists() and (p / "backend" / "cinematic").exists():
                return True

        # 2. Local sibling workspace folder check
        cwd = base_dir or pathlib.Path.cwd()
        sibling = cwd.parent / "demToshka-CinematicStudio"
        if sibling.exists():
            return True

        # 3. Check internal cinematic engine package availability
        internal_cinematic = cwd / "backend" / "cinematic"
        if internal_cinematic.exists():
            return True

        return False

    @staticmethod
    def get_studio_status(base_dir: Optional[pathlib.Path] = None) -> Dict[str, Any]:
        available = StudioAvailabilityDetector.is_studio_available(base_dir)
        return {
            "available": available,
            "version": "1.0.0" if available else None,
            "engine": "hlae_afxhooks2" if available else None,
            "supported_profiles": [
                "clean_cinematic",
                "broadcast_esports",
                "tiktok_vertical",
                "vfx_multipass",
            ]
            if available
            else [],
            "manifest_schema": MANIFEST_SCHEMA_VERSION,
        }


class StudioJobLauncher:
    """Manages creation and submission of StudioJobManifests."""

    def __init__(self, manifests_dir: Optional[pathlib.Path] = None) -> None:
        self.jobs_dir = (manifests_dir or DEFAULT_MANIFESTS_DIR) / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def submit_job(self, manifest: StudioJobManifest) -> pathlib.Path:
        """Serialize and save the manifest file to the jobs directory."""
        file_path = self.jobs_dir / f"{manifest.job_id}.json"
        file_path.write_text(manifest.to_json(), encoding="utf-8")
        logger.info("Submitted StudioJobManifest: %s", file_path)
        return file_path


class StudioJobStatusProvider:
    """Reads status reports generated by Cinematic Studio."""

    def __init__(self, manifests_dir: Optional[pathlib.Path] = None) -> None:
        self.status_dir = (manifests_dir or DEFAULT_MANIFESTS_DIR) / "status"
        self.jobs_dir = (manifests_dir or DEFAULT_MANIFESTS_DIR) / "jobs"

    def get_status(self, job_id: str) -> Dict[str, Any]:
        """Return the current status of the requested job."""
        status_file = self.status_dir / f"{job_id}.json"
        if status_file.exists():
            try:
                return json.loads(status_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Error reading status file %s: %s", status_file, e)

        # Check if job manifest is pending
        job_file = self.jobs_dir / f"{job_id}.json"
        if job_file.exists():
            return {
                "job_id": job_id,
                "status": "pending",
                "progress_pct": 0.0,
                "stage": "queued_for_studio",
                "output_assets": [],
            }

        return {
            "job_id": job_id,
            "status": "not_found",
            "progress_pct": 0.0,
            "stage": "unknown",
            "output_assets": [],
        }


class SocialPostDraftGenerator:
    """Generates engaging post descriptions and hashtags for social platforms."""

    @staticmethod
    def generate_draft(
        player_name: str,
        map_name: str,
        highlight_type: str,
        primary_weapon: str,
        round_num: int,
        kill_count: int,
        score: float,
        duration_sec: float,
        platform: str = "telegram",  # 'telegram' | 'youtube_shorts' | 'tiktok'
    ) -> str:
        clean_map = map_name.replace("de_", "").capitalize()
        clean_weapon = primary_weapon.upper().replace("_", " ") if primary_weapon else "CS2"
        hl_upper = highlight_type.upper().replace("_", " ")

        if platform == "telegram":
            return (
                f"🔥 **{player_name} — {hl_upper} на {clean_map}!**\n\n"
                f"⚡ {kill_count} фрагов из {clean_weapon} всего за {duration_sec:.1f} сек в {round_num}-м раунде!\n"
                f"📊 Рейтинг зрелищности: **{score:.1f}/100**\n\n"
                f"#CS2 #{clean_map} #{clean_weapon} #demToshka #Highlights #CounterStrike2"
            )
        elif platform == "youtube_shorts":
            return (
                f"{player_name} {hl_upper} С {clean_weapon} НА {clean_map.upper()}! 🔥\n\n"
                f"Невероятная серия в {round_num}-м раунде ({duration_sec:.1f} сек).\n"
                f"Проанализировано и подготовлено в dem.Toshka CS2 Studio.\n\n"
                f"#CS2 #CS2Highlights #Shorts #CounterStrike #{clean_map}"
            )
        elif platform == "tiktok":
            return (
                f"{hl_upper} от {player_name} на {clean_map}! 🎯 {kill_count} kills / {clean_weapon} #{clean_map} #cs2clips #cs2daily #gaming #demtoshka"
            )
        else:
            return f"{player_name} - {hl_upper} ({clean_map}, {clean_weapon}, R{round_num})"
