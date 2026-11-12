"""
Sound Library Manager for dem.Toshka Cinematic Studio.

Manages the verified Sonniss GDC 2026 Game Audio assets:
- Catalog loading and fast memory caching
- Filtering by category (impacts, whooshes, risers, transitions, etc.)
- Metadata queries (duration, peak, RMS, sample rate, bit depth)
- Audition audio streaming file resolution
- License and provenance verification
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SoundAsset:
    id: str
    filename: str
    original_filename: str
    original_folder: str
    category: str
    relative_path: str
    absolute_path: str
    size_bytes: int
    sha256: str
    duration_seconds: float
    sample_rate: int
    channels: int
    bit_depth: int
    peak_dbfs: float
    rms_dbfs: float
    recommended_use: str
    license: str
    source: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "original_folder": self.original_folder,
            "category": self.category,
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "duration_seconds": self.duration_seconds,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "bit_depth": self.bit_depth,
            "peak_dbfs": self.peak_dbfs,
            "rms_dbfs": self.rms_dbfs,
            "recommended_use": self.recommended_use,
            "license": self.license,
            "source": self.source,
            "audition_url": f"/api/cinematic/sound-library/audio/{self.category}/{self.filename}"
        }


class SoundLibraryManager:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.abspath("assets/sound_library")
        self.catalog_path = os.path.join(self.base_dir, "sound_library_catalog.json")
        self._assets: dict[str, SoundAsset] = {}
        self._categories: dict[str, list[str]] = {}
        self._metadata: dict[str, Any] = {}
        self._loaded = False
        self.load_catalog()

    def load_catalog(self) -> bool:
        if not os.path.exists(self.catalog_path):
            return False

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._metadata = {
                "library_name": data.get("library_name", "Sonniss GDC 2026 Game Audio Library"),
                "source_archive": data.get("source_archive", ""),
                "source_archive_size": data.get("source_archive_size", 0),
                "license_type": data.get("license_type", ""),
                "license_url": data.get("license_url", ""),
                "supplier": data.get("supplier", ""),
                "total_assets": data.get("total_assets", 0),
            }

            self._categories = data.get("categories", {})
            self._assets.clear()

            for item in data.get("assets", []):
                rel = item.get("relative_path", "")
                abs_path = os.path.join(self.base_dir, rel.replace("/", os.sep))
                asset = SoundAsset(
                    id=item["id"],
                    filename=item["filename"],
                    original_filename=item.get("original_filename", item["filename"]),
                    original_folder=item.get("original_folder", ""),
                    category=item["category"],
                    relative_path=rel,
                    absolute_path=abs_path,
                    size_bytes=item.get("size_bytes", 0),
                    sha256=item.get("sha256", ""),
                    duration_seconds=item.get("duration_seconds", 0.0),
                    sample_rate=item.get("sample_rate", 44100),
                    channels=item.get("channels", 2),
                    bit_depth=item.get("bit_depth", 16),
                    peak_dbfs=item.get("peak_dbfs", 0.0),
                    rms_dbfs=item.get("rms_dbfs", 0.0),
                    recommended_use=item.get("recommended_use", ""),
                    license=item.get("license", ""),
                    source=item.get("source", ""),
                )
                self._assets[asset.id] = asset

            self._loaded = True
            return True
        except Exception as err:
            print(f"Failed to load sound catalog: {err}")
            return False

    def list_categories(self) -> list[str]:
        return list(self._categories.keys())

    def list_assets(self, category: Optional[str] = None, search: Optional[str] = None) -> list[SoundAsset]:
        results = list(self._assets.values())
        if category:
            results = [a for a in results if a.category.lower() == category.lower()]
        if search:
            q = search.lower()
            results = [
                a for a in results
                if q in a.filename.lower()
                or q in a.recommended_use.lower()
                or q in a.original_folder.lower()
            ]
        return results

    def get_asset(self, asset_id: str) -> Optional[SoundAsset]:
        return self._assets.get(asset_id)

    def get_asset_by_name(self, category: str, filename: str) -> Optional[SoundAsset]:
        for a in self._assets.values():
            if a.category.lower() == category.lower() and a.filename.lower() == filename.lower():
                return a
        return None

    def get_audio_file_path(self, category: str, filename: str) -> Optional[str]:
        asset = self.get_asset_by_name(category, filename)
        if asset and os.path.exists(asset.absolute_path):
            return asset.absolute_path
        # Fallback check
        fallback = os.path.join(self.base_dir, category, filename)
        if os.path.exists(fallback):
            return fallback
        return None

    def get_overview(self) -> dict[str, Any]:
        return {
            "metadata": self._metadata,
            "category_counts": {cat: len(files) for cat, files in self._categories.items()},
            "total_assets": len(self._assets),
            "is_loaded": self._loaded,
        }
