"""FastAPI application entrypoint for CS2 Highlights Studio."""

from __future__ import annotations

import pathlib
import uuid
from typing import Generator, Optional

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.api.schemas import (
    DemoSummary,
    HighlightDTO,
    KillDTO,
    MatchScoreboardDTO,
    MontageCreateRequest,
    MontageDTO,
    ParseDemoRequest,
    PlayerAnalyticsDTO,
    PlayerDTO,
    RenderJobCreateRequest,
    RenderJobDTO,
    RoundDTO,
)
from backend.api.services import DemoService
from backend.parser.errors import DemoParseError, InvalidDemoPathError
from backend.parser.models import SCHEMA_VERSION
from backend.parser.replay import extract_round_replay_data
from backend.render.config import RENDER_OUTPUT_DIR
from backend.render.montage import create_montage
from backend.render.queue import RenderQueueManager
from backend.render.storage_manager import (
    cleanup_all_clips,
    cleanup_clips_for_demo,
    cleanup_render_logs,
    cleanup_temporary_files,
    delete_specific_clips,
    get_clips_with_metadata,
    get_configured_output_dir,
    is_directory_writable,
    open_folder_in_explorer,
    set_configured_output_dir,
)
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.models import RenderJobModel
from backend.storage.repository import DemoRepository

# Initialize database
engine = create_db_engine()
init_db(engine)
SessionFactory = get_session_factory(engine)

# Initialize sequential render queue manager
render_queue = RenderQueueManager(session_factory=SessionFactory)


@asynccontextmanager
async def lifespan(app: FastAPI):
    render_queue.start()
    try:
        yield
    finally:
        await render_queue.stop()


def get_db() -> Generator[Session, None, None]:
    """Dependency providing a transactional SQLAlchemy session."""
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


app = FastAPI(
    title="CS2 Highlights Studio API",
    version="1.0.0",
    description="Local backend API for CS2 Highlights Studio desktop app.",
    lifespan=lifespan,
)

# Enable CORS for local desktop UI (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve rendered video clips and HTML reports statically
RENDER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/renders", StaticFiles(directory=str(RENDER_OUTPUT_DIR), html=True), name="renders")


@app.get("/api/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "schema_version": SCHEMA_VERSION}


@app.post("/api/demos/parse", response_model=DemoSummary, tags=["demos"])
def parse_demo_endpoint(
    req: ParseDemoRequest, db: Session = Depends(get_db)
) -> DemoSummary:
    """Parse a CS2 .dem file or retrieve cached analysis from SQLite."""
    repo = DemoRepository(db)
    try:
        demo = DemoService.parse_or_get_demo(req.demo_path, repo)
        return DemoService.to_summary(demo)
    except (InvalidDemoPathError, FileNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid demo path: {e}",
        )
    except DemoParseError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Demo parse error: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing demo: {e}",
        )


UPLOAD_DEMOS_DIR = pathlib.Path("demos")


@app.post("/api/demos/upload", response_model=DemoSummary, tags=["demos"])
async def upload_demo_endpoint(
    request: Request,
    filename: str = Query(..., description="Uploaded demo filename"),
    db: Session = Depends(get_db),
) -> DemoSummary:
    """Stream upload a CS2 .dem file and parse it immediately."""
    clean_name = pathlib.Path(filename).name
    if not clean_name.lower().endswith(".dem"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have .dem extension",
        )
    UPLOAD_DEMOS_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = UPLOAD_DEMOS_DIR / clean_name
    try:
        with open(dest_path, "wb") as f:
            async for chunk in request.stream():
                f.write(chunk)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded demo: {e}",
        )

    repo = DemoRepository(db)
    try:
        demo = DemoService.parse_or_get_demo(str(dest_path), repo)
        return DemoService.to_summary(demo)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Demo parse error: {e}",
        )


@app.get("/api/demos", response_model=list[DemoSummary], tags=["demos"])
def list_demos(db: Session = Depends(get_db)) -> list[DemoSummary]:
    """List all previously analyzed demos."""
    repo = DemoRepository(db)
    demos = repo.list_demos()
    return [DemoService.to_summary(d) for d in demos]


@app.get("/api/demos/{demo_id}", response_model=DemoSummary, tags=["demos"])
def get_demo(demo_id: int, db: Session = Depends(get_db)) -> DemoSummary:
    """Get demo summary by ID."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(demo_id)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo with id {demo_id} not found",
        )
    return DemoService.to_summary(demo)


@app.get("/api/demos/{demo_id}/stats", response_model=MatchScoreboardDTO, tags=["analytics"])
def get_match_stats(demo_id: int, db: Session = Depends(get_db)) -> MatchScoreboardDTO:
    """Get scoreboard and weapon analytics for a match."""
    repo = DemoRepository(db)
    scoreboard = DemoService.get_scoreboard(demo_id, repo)
    if not scoreboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo with id {demo_id} not found",
        )
    return scoreboard


@app.get("/api/demos/{demo_id}/highlights", response_model=list[HighlightDTO], tags=["highlights"])
def get_highlights(
    demo_id: int,
    pov_steam_id: Optional[str] = None,
    highlight_type: Optional[str] = None,
    round_num: Optional[int] = None,
    db: Session = Depends(get_db),
) -> list[HighlightDTO]:
    """Get highlights with optional filtering by POV, type, and round."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(demo_id)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo with id {demo_id} not found",
        )
    return DemoService.get_highlights(
        demo_id=demo_id,
        repo=repo,
        pov_steam_id=pov_steam_id,
        highlight_type=highlight_type,
        round_num=round_num,
    )


@app.get("/api/demos/{demo_id}/players", response_model=list[PlayerDTO], tags=["players"])
def get_players(demo_id: int, db: Session = Depends(get_db)) -> list[PlayerDTO]:
    """Get list of players for a demo."""
    repo = DemoRepository(db)
    players = repo.get_players(demo_id)
    return [
        PlayerDTO(
            id=p.id,
            demo_id=p.demo_id,
            name=p.name,
            steam_id=p.steam_id,
            team=p.team,
        )
        for p in players
    ]


@app.get(
    "/api/demos/{demo_id}/players/{player_identifier}/analytics",
    response_model=PlayerAnalyticsDTO,
    tags=["players", "analytics"],
)
def get_player_analytics(
    demo_id: int,
    player_identifier: str,
    db: Session = Depends(get_db),
) -> PlayerAnalyticsDTO:
    """Get in-depth FACEIT-style player performance analytics and tactical error audit."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(demo_id)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo with id {demo_id} not found",
        )
    analytics = DemoService.get_player_analytics(demo_id, player_identifier, repo)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player '{player_identifier}' not found in demo {demo_id}",
        )
    return analytics



@app.get("/api/demos/{demo_id}/rounds", response_model=list[RoundDTO], tags=["rounds"])
def get_rounds(demo_id: int, db: Session = Depends(get_db)) -> list[RoundDTO]:
    """Get rounds for a demo."""
    repo = DemoRepository(db)
    rounds = repo.get_rounds(demo_id)
    return [
        RoundDTO(
            id=r.id,
            round_num=r.round_num,
            start_tick=r.start_tick,
            freeze_end_tick=r.freeze_end_tick,
            end_tick=r.end_tick,
            official_end_tick=r.official_end_tick,
            winner=r.winner,
            reason=r.reason,
            bomb_plant_tick=r.bomb_plant_tick,
            bomb_site=r.bomb_site,
        )
        for r in rounds
    ]


@app.get("/api/demos/{demo_id}/kills", response_model=list[KillDTO], tags=["kills"])
def get_kills(
    demo_id: int,
    round_num: Optional[int] = None,
    db: Session = Depends(get_db),
) -> list[KillDTO]:
    """Get kill events for a demo with optional round filter."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(demo_id)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo with id {demo_id} not found",
        )
    kills = repo.get_kills(demo_id, round_num=round_num)
    return [
        KillDTO(
            id=k.id,
            demo_id=k.demo_id,
            tick=k.tick,
            round_num=k.round_num,
            attacker_name=k.attacker_name,
            attacker_steam_id=k.attacker_steam_id,
            attacker_team=k.attacker_team,
            victim_name=k.victim_name,
            victim_steam_id=k.victim_steam_id,
            victim_team=k.victim_team,
            weapon=k.weapon,
            headshot=k.headshot,
            noscope=k.noscope,
            thru_smoke=k.thru_smoke,
            wallbang=k.wallbang,
            is_suicide=k.is_suicide,
            is_teamkill=k.is_teamkill,
        )
        for k in kills
    ]


@app.post("/api/render-jobs", response_model=list[RenderJobDTO], tags=["rendering"])
async def create_render_jobs(
    req: RenderJobCreateRequest, db: Session = Depends(get_db)
) -> list[RenderJobDTO]:
    """Queue selected highlights for sequential video rendering."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(req.demo_id)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo with id {req.demo_id} not found",
        )

    if not req.highlight_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one highlight ID must be provided",
        )

    settings_dict = {
        "resolution": req.resolution,
        "fps": req.fps,
        "pre_roll_seconds": req.pre_roll_seconds,
        "post_roll_seconds": req.post_roll_seconds,
        "perspective": req.perspective,
        "perspective_steam_id": req.perspective_steam_id,
        "xray": req.xray,
        "hud_mode": req.hud_mode,
        "hud_scale": req.hud_scale,
        "custom_crosshair": req.custom_crosshair,
        "fov": req.fov,
        "viewmodel_fov": req.viewmodel_fov,
        "crosshair_preset": req.crosshair_preset,
        "crosshair_color": req.crosshair_color,
        "radar_mode": req.radar_mode,
    }

    # 1. Deduplicate highlight_ids in request preserving order
    seen_ids: set[str] = set()
    unique_hl_ids = [hid for hid in req.highlight_ids if not (hid in seen_ids or seen_ids.add(hid))]

    created_jobs: list[RenderJobDTO] = []
    for hl_id in unique_hl_ids:
        hl = repo.get_highlight_by_id(hl_id)
        if not hl or hl.demo_id != req.demo_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Highlight '{hl_id}' does not belong to demo {req.demo_id}",
            )

        # 2. Check for existing active job to protect against double-click duplicates
        existing_active = repo.get_active_render_job(demo_id=req.demo_id, highlight_id=hl_id)
        if existing_active:
            if existing_active.status == "pending" and render_queue.current_job_id != existing_active.id:
                await render_queue.enqueue(existing_active.id)
            created_jobs.append(
                RenderJobDTO(
                    id=existing_active.id,
                    demo_id=existing_active.demo_id,
                    highlight_id=existing_active.highlight_id,
                    status=existing_active.status,
                    progress=existing_active.progress,
                    output_path=existing_active.output_path,
                    error_summary=existing_active.error_summary,
                    log_path=existing_active.log_path,
                    settings_json=existing_active.settings_json,
                    created_at=existing_active.created_at,
                )
            )
            continue

        job_id = str(uuid.uuid4())
        job_model = repo.create_render_job(
            job_id=job_id,
            demo_id=req.demo_id,
            highlight_id=hl_id,
            settings_dict=settings_dict,
        )

        # Enqueue in sequential worker
        await render_queue.enqueue(job_id)

        created_jobs.append(
            RenderJobDTO(
                id=job_model.id,
                demo_id=job_model.demo_id,
                highlight_id=job_model.highlight_id,
                status=job_model.status,
                progress=job_model.progress,
                output_path=job_model.output_path,
                error_summary=job_model.error_summary,
                log_path=job_model.log_path,
                settings_json=job_model.settings_json,
                created_at=job_model.created_at,
            )
        )

    return created_jobs


@app.post(
    "/api/render-jobs/{job_id}/retry",
    response_model=RenderJobDTO,
    tags=["rendering"],
)
async def retry_render_job_endpoint(
    job_id: str, db: Session = Depends(get_db)
) -> RenderJobDTO:
    """Retry a failed render job."""
    repo = DemoRepository(db)
    job = repo.get_render_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Render job '{job_id}' not found",
        )
    if job.status not in ("failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job '{job_id}' is in status '{job.status}' (only 'failed' or 'cancelled' jobs can be retried)",
        )

    retried = repo.retry_render_job(job_id)
    if not retried:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset job state for retry",
        )

    await render_queue.enqueue(job_id)

    return RenderJobDTO(
        id=retried.id,
        demo_id=retried.demo_id,
        highlight_id=retried.highlight_id,
        status=retried.status,
        progress=retried.progress,
        output_path=retried.output_path,
        error_summary=retried.error_summary,
        log_path=retried.log_path,
        settings_json=retried.settings_json,
        created_at=retried.created_at,
    )


@app.post(
    "/api/render-jobs/{job_id}/cancel",
    response_model=RenderJobDTO,
    tags=["rendering"],
)
def cancel_render_job_endpoint(
    job_id: str, db: Session = Depends(get_db)
) -> RenderJobDTO:
    """Cancel a pending render job."""
    repo = DemoRepository(db)
    job = repo.get_render_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Render job '{job_id}' not found",
        )
    cancelled = repo.cancel_render_job(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job '{job_id}' in status '{job.status}' cannot be cancelled",
        )
    return RenderJobDTO(
        id=cancelled.id,
        demo_id=cancelled.demo_id,
        highlight_id=cancelled.highlight_id,
        status=cancelled.status,
        progress=cancelled.progress,
        output_path=cancelled.output_path,
        error_summary=cancelled.error_summary,
        log_path=cancelled.log_path,
        settings_json=cancelled.settings_json,
        created_at=cancelled.created_at,
    )


@app.post(
    "/api/render-jobs/retry-failed",
    response_model=list[RenderJobDTO],
    tags=["rendering"],
)
async def retry_failed_jobs_endpoint(
    demo_id: Optional[int] = Query(None, description="Optional demo ID filter"),
    db: Session = Depends(get_db),
) -> list[RenderJobDTO]:
    """Retry all failed render jobs."""
    repo = DemoRepository(db)
    all_jobs = repo.list_render_jobs(demo_id=demo_id)
    failed_jobs = [j for j in all_jobs if j.status == "failed"]
    retried_list: list[RenderJobDTO] = []

    for f_job in failed_jobs:
        retried = repo.retry_render_job(f_job.id)
        if retried:
            await render_queue.enqueue(retried.id)
            retried_list.append(
                RenderJobDTO(
                    id=retried.id,
                    demo_id=retried.demo_id,
                    highlight_id=retried.highlight_id,
                    status=retried.status,
                    progress=retried.progress,
                    output_path=retried.output_path,
                    error_summary=retried.error_summary,
                    log_path=retried.log_path,
                    settings_json=retried.settings_json,
                    created_at=retried.created_at,
                )
            )

    return retried_list


@app.get("/api/render-jobs", response_model=list[RenderJobDTO], tags=["rendering"])
def list_render_jobs(
    demo_id: Optional[int] = Query(None, description="Optional demo ID filter"),
    db: Session = Depends(get_db),
) -> list[RenderJobDTO]:
    """List render jobs ordered by created_at desc."""
    repo = DemoRepository(db)
    jobs = repo.list_render_jobs(demo_id=demo_id)
    return [
        RenderJobDTO(
            id=j.id,
            demo_id=j.demo_id,
            highlight_id=j.highlight_id,
            status=j.status,
            progress=j.progress,
            output_path=j.output_path,
            error_summary=j.error_summary,
            log_path=j.log_path,
            settings_json=j.settings_json,
            created_at=j.created_at,
        )
        for j in jobs
    ]


@app.get("/api/render-jobs/{job_id}", response_model=RenderJobDTO, tags=["rendering"])
def get_render_job(job_id: str, db: Session = Depends(get_db)) -> RenderJobDTO:
    """Get the current status, progress and output of a render job by ID."""
    repo = DemoRepository(db)
    job = repo.get_render_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Render job '{job_id}' not found",
        )
    return RenderJobDTO(
        id=job.id,
        demo_id=job.demo_id,
        highlight_id=job.highlight_id,
        status=job.status,
        progress=job.progress,
        output_path=job.output_path,
        error_summary=job.error_summary,
        log_path=job.log_path,
        settings_json=job.settings_json,
        created_at=job.created_at,
    )
@app.delete("/api/render-jobs/{job_id}", tags=["rendering"])
def delete_render_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a render job record from the database."""
    repo = DemoRepository(db)
    success = repo.delete_render_job(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Render job '{job_id}' not found",
        )
    return {"success": True, "job_id": job_id}


@app.post("/api/render-jobs/clear-completed", tags=["rendering"])
def clear_completed_render_jobs(
    demo_id: Optional[int] = Query(None, description="Optional demo ID filter"),
    db: Session = Depends(get_db),
):
    """Clear all finished (completed, failed, cancelled) render jobs."""
    repo = DemoRepository(db)
    count = repo.clear_completed_render_jobs(demo_id=demo_id)
    return {"success": True, "cleared_count": count}

@app.api_route("/api/videos/{job_id}", methods=["GET", "HEAD"], tags=["rendering"])
def get_job_video(job_id: str, db: Session = Depends(get_db)):
    """Stream rendered highlight video with audio for in-browser playback."""
    repo = DemoRepository(db)
    job = repo.get_render_job(job_id)
    if not job or not job.output_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video file not found for render job '{job_id}'",
        )
    video_path = pathlib.Path(job.output_path).resolve()
    renders_dir = pathlib.Path("renders").resolve()
    if not video_path.is_file() or video_path.suffix.lower() != ".mp4":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rendered video file does not exist on disk: {job.output_path}",
        )
    try:
        video_path.relative_to(renders_dir)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: file is outside the renders directory",
        )
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=video_path.name,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        },
    )



@app.post("/api/montage", response_model=MontageDTO, tags=["rendering"])
def create_montage_endpoint(req: MontageCreateRequest, db: Session = Depends(get_db)):
    """Concatenate completed highlight clips into a single compilation movie."""
    repo = DemoRepository(db)
    clip_paths: list[pathlib.Path] = []

    if req.filenames:
        out_dir = get_configured_output_dir()
        for fname in req.filenames:
            if ".." not in fname and "/" not in fname and "\\" not in fname:
                p = (out_dir / fname).resolve()
                if p.is_file() and p.suffix.lower() == ".mp4":
                    clip_paths.append(p)
    elif req.job_ids:
        for jid in req.job_ids:
            job = repo.get_render_job(jid)
            if job and job.status == "completed" and job.output_path:
                p = pathlib.Path(job.output_path).resolve()
                if p.is_file():
                    clip_paths.append(p)
    elif req.demo_id is not None:
        jobs = repo.list_render_jobs(demo_id=req.demo_id)
        completed_jobs = [j for j in jobs if j.status == "completed" and j.output_path]
        for cj in completed_jobs:
            p = pathlib.Path(cj.output_path).resolve()
            if p.is_file():
                clip_paths.append(p)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either filenames, job_ids or demo_id must be provided",
        )

    if not clip_paths:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed clip video files found to compile into montage",
        )

    renders_dir = pathlib.Path("renders").resolve()
    renders_dir.mkdir(parents=True, exist_ok=True)
    montage_name = f"montage_{uuid.uuid4().hex[:8]}.mp4"
    out_file = renders_dir / montage_name

    res = create_montage(clip_paths=clip_paths, output_path=out_file)
    if not res.success or not res.output_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile montage: {res.error_message}",
        )

    return MontageDTO(
        success=True,
        montage_path=str(res.output_path),
        filename=res.output_path.name,
        duration_seconds=res.duration_seconds,
        clip_count=res.clip_count,
    )


@app.api_route("/api/montage/{filename}", methods=["GET", "HEAD"], tags=["rendering"])
def get_montage_video(filename: str):
    """Stream merged montage video for in-browser playback."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: path traversal is prohibited",
        )
    renders_dir = pathlib.Path("renders").resolve()
    file_path = (renders_dir / filename).resolve()
    if not file_path.is_file() or file_path.suffix.lower() != ".mp4":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Montage video '{filename}' not found",
        )
    try:
        file_path.relative_to(renders_dir)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=file_path.name,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        },
    )


@app.get("/api/demos/{demo_id}/rounds/{round_num}/replay", tags=["replay"])
def get_round_replay(
    demo_id: int,
    round_num: int,
    step_ticks: int = Query(default=32, ge=8, le=128),
    db: Session = Depends(get_db),
):
    """Return real player world coordinates and kill events for 2D tactical replay."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(demo_id)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo {demo_id} not found",
        )
    demo_path = pathlib.Path(demo.file_path).resolve()
    if not demo_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo file missing at {demo_path}",
        )

    try:
        replay_data = extract_round_replay_data(demo_path, round_num=round_num, step_ticks=step_ticks)
        return replay_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract replay data: {e}",
        )


@app.get("/api/settings/storage", tags=["settings"])
def get_storage_settings():
    """Get current output directory path and writability status."""
    p = get_configured_output_dir()
    return {
        "output_directory": str(p),
        "is_writable": is_directory_writable(p),
    }


@app.post("/api/settings/storage", tags=["settings"])
def set_storage_settings(payload: dict):
    """Set custom output directory path."""
    target_dir = payload.get("directory")
    if not target_dir:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="directory parameter is required",
        )
    success, message, saved_path = set_configured_output_dir(target_dir)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    return {
        "success": True,
        "message": message,
        "output_directory": str(saved_path),
        "is_writable": is_directory_writable(saved_path),
    }


@app.post("/api/renders/open-folder", tags=["rendering"])
def open_output_folder():
    """Open current render output directory in Windows Explorer."""
    success = open_folder_in_explorer()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to open directory in system file explorer",
        )
    return {"success": True, "message": "Opened explorer window"}


@app.post("/api/renders/cleanup-temp", tags=["rendering"])
def cleanup_temp_artifacts():
    """Remove temporary files without touching finished MP4 clips."""
    res = cleanup_temporary_files()
    return {"success": True, "cleaned": res}


@app.post("/api/renders/delete-clips", tags=["rendering"])
def delete_clips_endpoint(payload: dict):
    """Explicitly delete selected finished MP4 clips."""
    filenames = payload.get("filenames", [])
    if not filenames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="filenames list is required",
        )
    deleted = delete_specific_clips(filenames)
    return {"success": True, "deleted": deleted}


@app.post("/api/renders/cleanup-all-clips", tags=["rendering"])
def cleanup_all_clips_endpoint():
    """Bulk delete all completed MP4 highlight clips in output directory."""
    deleted = cleanup_all_clips()
    return {"success": True, "deleted": deleted, "count": len(deleted)}


@app.post("/api/renders/cleanup-logs", tags=["rendering"])
def cleanup_logs_endpoint():
    """Delete all HLAE, FFmpeg, and temporary log files from renders and root directories."""
    deleted = cleanup_render_logs()
    return {"success": True, "deleted": deleted, "count": len(deleted)}


@app.post("/api/renders/cleanup-demo/{demo_id}", tags=["rendering"])
def cleanup_demo_clips_endpoint(demo_id: int, db: Session = Depends(get_db)):
    """Delete all rendered clips and logs belonging to a specific demo."""
    deleted = cleanup_clips_for_demo(demo_id, db)
    return {"success": True, "deleted": deleted, "count": len(deleted)}


@app.get("/api/renders/clips", tags=["rendering"])
def list_completed_clips(demo_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List all completed MP4 highlight clips with rich metadata (map, player, event type)."""
    return get_clips_with_metadata(db, demo_id=demo_id)


@app.api_route("/api/renders/{filename}", methods=["GET", "HEAD"], tags=["rendering"])
def get_render_by_filename(filename: str):
    """Serve rendered clip by filename directly from renders directory."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: path traversal is prohibited",
        )
    renders_dir = pathlib.Path("renders").resolve()
    file_path = (renders_dir / filename).resolve()
    if not file_path.is_file() or file_path.suffix.lower() != ".mp4":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video '{filename}' not found",
        )
    try:
        file_path.relative_to(renders_dir)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=file_path.name,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        },
    )



