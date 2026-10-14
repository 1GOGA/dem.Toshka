"""File and Storage Management for CS2 Highlights Studio.

Handles custom output directories, write-permission verification,
opening folders in Windows Explorer, temporary file cleanup,
and clip lifecycle operations.
"""

from __future__ import annotations

import logging
import os
import pathlib
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger("demtoshka.storage_manager")

from backend.render.config import RENDER_OUTPUT_DIR

SETTINGS_FILE = pathlib.Path("storage_settings.json")


def get_configured_output_dir() -> pathlib.Path:
    """Return currently configured output directory or default renders/."""
    if SETTINGS_FILE.is_file():
        try:
            import json
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            custom_path = data.get("output_directory")
            if custom_path:
                p = pathlib.Path(custom_path).resolve()
                p.mkdir(parents=True, exist_ok=True)
                return p
        except Exception as e:
            logger.warning("Could not read custom storage settings: %s", e)

    RENDER_OUTPUT_DIR.resolve().mkdir(parents=True, exist_ok=True)
    return RENDER_OUTPUT_DIR.resolve()


def set_configured_output_dir(target_path_str: str) -> tuple[bool, str, pathlib.Path]:
    """Validate, create and persist a new output directory."""
    import json

    try:
        p = pathlib.Path(target_path_str).resolve()
        p.mkdir(parents=True, exist_ok=True)

        # Check write permissions
        test_file = p / f".write_test_{os.getpid()}"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink(missing_ok=True)

        SETTINGS_FILE.write_text(
            json.dumps({"output_directory": str(p)}, indent=2),
            encoding="utf-8",
        )
        return True, "Путь успешно сохранен и доступен для записи", p
    except Exception as e:
        return False, f"Ошибка доступа к папке: {e}", get_configured_output_dir()


def is_directory_writable(directory: pathlib.Path) -> bool:
    """Check if directory exists and is writable."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        test_f = directory / f".perm_check_{os.getpid()}"
        test_f.write_text("ok", encoding="utf-8")
        test_f.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def open_folder_in_explorer(folder_path: Optional[pathlib.Path] = None) -> bool:
    """Open target folder in Windows Explorer."""
    path_to_open = (folder_path or get_configured_output_dir()).resolve()
    path_to_open.mkdir(parents=True, exist_ok=True)

    try:
        if os.name == "nt":
            os.startfile(str(path_to_open))
            return True
        else:
            subprocess.run(["xdg-open", str(path_to_open)], check=False)
            return True
    except Exception as e:
        logger.error("Failed to open explorer for %s: %s", path_to_open, e)
        return False


def cleanup_temporary_files(base_dir: Optional[pathlib.Path] = None) -> dict[str, int]:
    """Remove temporary render artifacts without touching finished MP4 clips.

    Cleans:
    - take* folders
    - batch_* temporary staging directories
    - job_* temporary directories
    - unmerged .wav audio files
    - .log files older than current session
    """
    target_dir = (base_dir or get_configured_output_dir()).resolve()
    cleaned = {"directories": 0, "wav_files": 0, "log_files": 0}

    if not target_dir.exists():
        return cleaned

    for item in target_dir.iterdir():
        if item.is_dir():
            name_lower = item.name.lower()
            if (
                name_lower.startswith("job_")
                or name_lower.startswith("batch_")
                or name_lower.startswith("take")
            ):
                try:
                    shutil.rmtree(item, ignore_errors=True)
                    cleaned["directories"] += 1
                except Exception:
                    pass
        elif item.is_file():
            if item.suffix.lower() == ".wav":
                try:
                    item.unlink(missing_ok=True)
                    cleaned["wav_files"] += 1
                except Exception:
                    pass
            elif item.suffix.lower() == ".log" and item.name.startswith("temp_"):
                try:
                    item.unlink(missing_ok=True)
                    cleaned["log_files"] += 1
                except Exception:
                    pass

    return cleaned


def delete_specific_clips(
    filenames: list[str],
    base_dir: Optional[pathlib.Path] = None,
) -> list[str]:
    """Delete explicitly confirmed completed clips."""
    target_dir = (base_dir or get_configured_output_dir()).resolve()
    deleted: list[str] = []

    for fn in filenames:
        # Sanitize filename against path traversal
        if ".." in fn or "/" in fn or "\\" in fn:
            continue
        p = target_dir / fn
        if p.is_file() and p.suffix.lower() == ".mp4":
            try:
                p.unlink()
                deleted.append(fn)
            except Exception as e:
                logger.warning("Could not delete %s: %s", fn, e)

    return deleted


def cleanup_all_clips(base_dir: Optional[pathlib.Path] = None) -> list[str]:
    """Delete all completed MP4 highlight clips in the output directory."""
    target_dir = (base_dir or get_configured_output_dir()).resolve()
    deleted: list[str] = []
    if target_dir.exists():
        for f in list(target_dir.glob("*.mp4")):
            try:
                f.unlink(missing_ok=True)
                deleted.append(f.name)
            except Exception as e:
                logger.warning("Could not delete clip %s: %s", f.name, e)
    return deleted


def cleanup_render_logs(base_dir: Optional[pathlib.Path] = None) -> list[str]:
    """Delete all HLAE, FFmpeg, and temporary log files from renders directory and root."""
    target_dir = (base_dir or get_configured_output_dir()).resolve()
    deleted_logs: list[str] = []

    # 1. Clean logs inside renders/
    if target_dir.exists():
        for log_file in list(target_dir.glob("*.log")):
            try:
                log_file.unlink(missing_ok=True)
                deleted_logs.append(f"renders/{log_file.name}")
            except Exception as e:
                logger.warning("Could not delete log file %s: %s", log_file, e)

    # 2. Clean root temporary logs (backend.log, frontend.log, etc.)
    root_dir = pathlib.Path(".").resolve()
    for root_log_name in ["backend.log", "backend_err.log", "frontend.log", "frontend_err.log"]:
        root_log = root_dir / root_log_name
        if root_log.is_file():
            try:
                root_log.unlink(missing_ok=True)
                deleted_logs.append(root_log_name)
            except Exception as e:
                logger.warning("Could not delete root log %s: %s", root_log, e)

    return deleted_logs


def cleanup_clips_for_demo(
    demo_id: int,
    db_session,
    base_dir: Optional[pathlib.Path] = None,
) -> list[str]:
    """Delete MP4 clips and render job records associated with a specific demo."""
    from backend.storage.models import DemoModel, RenderJobModel

    target_dir = (base_dir or get_configured_output_dir()).resolve()
    deleted_files: list[str] = []

    # Query jobs for this demo
    jobs = db_session.query(RenderJobModel).filter(RenderJobModel.demo_id == demo_id).all()
    demo = db_session.query(DemoModel).filter(DemoModel.id == demo_id).first()
    map_clean = demo.map_name.lower().replace("de_", "").replace("cs_", "") if (demo and demo.map_name) else ""

    for job in jobs:
        if job.output_path:
            p = pathlib.Path(job.output_path).resolve()
            if p.is_file() and p.suffix.lower() == ".mp4":
                try:
                    p.unlink(missing_ok=True)
                    deleted_files.append(p.name)
                except Exception as e:
                    logger.warning("Could not delete demo clip %s: %s", p.name, e)
        # Also clean associated log
        if job.log_path:
            lp = pathlib.Path(job.log_path).resolve()
            if lp.is_file():
                try:
                    lp.unlink(missing_ok=True)
                except Exception:
                    pass

    # Check for filenames in target_dir starting with map name or demo id pattern
    if map_clean and target_dir.exists():
        for mp4_file in list(target_dir.glob(f"{map_clean}_*.mp4")):
            if mp4_file.name not in deleted_files:
                try:
                    mp4_file.unlink(missing_ok=True)
                    deleted_files.append(mp4_file.name)
                except Exception as e:
                    logger.warning("Could not delete matching map clip %s: %s", mp4_file.name, e)

    return deleted_files


def get_clips_with_metadata(
    db_session,
    demo_id: Optional[int] = None,
    base_dir: Optional[pathlib.Path] = None,
) -> list[dict]:
    """Return completed clips enriched with demo, map, and highlight metadata."""
    from backend.storage.models import DemoModel, HighlightModel, RenderJobModel

    target_dir = (base_dir or get_configured_output_dir()).resolve()
    if not target_dir.exists():
        return []

    # Pre-index jobs by output filename and id
    all_jobs = db_session.query(RenderJobModel).all()
    job_by_filename: dict[str, RenderJobModel] = {}
    for j in all_jobs:
        if j.output_path:
            fn = pathlib.Path(j.output_path).name
            job_by_filename[fn] = j

    demos_cache = {d.id: d for d in db_session.query(DemoModel).all()}
    highlights_cache = {h.id: h for h in db_session.query(HighlightModel).all()}

    results = []
    for f in sorted(target_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.name.startswith("temp_"):
            continue

        st = f.stat()
        job = job_by_filename.get(f.name)
        clip_demo_id = job.demo_id if job else None
        
        # If filtered by demo_id and not matching, skip
        if demo_id is not None and clip_demo_id != demo_id:
            # Also check if filename starts with this demo's map name
            cur_demo = demos_cache.get(demo_id)
            map_clean = cur_demo.map_name.lower().replace("de_", "").replace("cs_", "") if (cur_demo and cur_demo.map_name) else ""
            if not map_clean or not f.name.lower().startswith(map_clean):
                continue

        demo_obj = demos_cache.get(clip_demo_id) if clip_demo_id else None
        hl_obj = highlights_cache.get(job.highlight_id) if (job and job.highlight_id) else None

        # Infer map name if demo not directly linked
        map_name = demo_obj.map_name if demo_obj else None
        if not map_name:
            for known in ["mirage", "inferno", "nuke", "ancient", "anubis", "dust2", "vertigo", "overpass", "train"]:
                if f.name.lower().startswith(known):
                    map_name = f"de_{known}"
                    break

        results.append({
            "filename": f.name,
            "path": str(f.resolve()),
            "size_bytes": st.st_size,
            "modified_at": st.st_mtime,
            "is_montage": f.name.startswith("montage_"),
            "url": f"/api/montage/{f.name}",
            "demo_id": clip_demo_id,
            "map_name": map_name,
            "highlight_type": hl_obj.highlight_type if hl_obj else None,
            "player_name": hl_obj.pov_name if hl_obj else None,
            "round_num": hl_obj.round_num if hl_obj else None,
            "job_id": job.id if job else None,
        })

    return results


