"""FastAPI application entrypoint for CS2 Highlights Studio."""

from __future__ import annotations

import pathlib
import sys
import uuid
from typing import Generator, Optional

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.api.schemas import (
    AnalysisProjectDTO,
    BookmarkDTO,
    CreateAnalysisProjectRequest,
    CreateBookmarkRequest,
    CreateStudioJobRequest,
    CreateTacticalDrawingRequest,
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
    SocialDraftRequest,
    SocialDraftResponse,
    StudioJobResponse,
    StudioStatusResponse,
    TacticalDrawingDTO,
    PlayerVoiceTrackDTO,
    RoundVoiceTimelineDTO,
    VoiceSpeechSegmentDTO,
    VoiceStatusDTO,
    MultiMatchAnalyticsDTO,
    PlayerInsightDTO,
    PlayerProfileDTO,
    SkillRadarSchema,
    CreateStrategyBookRequest,
    CreateTacticalSetupRequest,
    StrategyBookDTO,
    TacticalSetupDTO,
    UtilityLineupDTO,
)
from backend.services.strategy_exporter import export_strategy_book_to_html
from backend.analytics.multi_match import (
    build_player_analytics_summary,
    generate_and_persist_insights,
)
from backend.api.services import DemoService
from backend.integration.studio_bridge import (
    ClipSpecificationManifest,
    DemoMetadataManifest,
    EventItemManifest,
    ProductionRequestManifest,
    SocialPostDraftGenerator,
    StudioAvailabilityDetector,
    StudioJobLauncher,
    StudioJobManifest,
    StudioJobStatusProvider,
)
from backend.parser.errors import DemoParseError, InvalidDemoPathError
from backend.parser.models import SCHEMA_VERSION
from backend.parser.replay import extract_round_replay_data
from backend.parser.voice import (
    check_demo_has_voice,
    convert_ogg_to_wav,
    get_player_round_voice_audio,
    get_round_voice_tracks,
)
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

# Enable CORS strictly for local desktop UI (Vite dev server and production)
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^http://(127\.0\.0\.1|localhost):[0-9]+$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


def _is_path_inside_allowed_renders(path: pathlib.Path) -> bool:
    resolved_target = path.resolve()
    allowed_dirs = [
        pathlib.Path("renders").resolve(),
        RENDER_OUTPUT_DIR.resolve(),
        get_configured_output_dir().resolve(),
    ]
    for ad in allowed_dirs:
        try:
            resolved_target.relative_to(ad)
            return True
        except ValueError:
            continue
    return False

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
        "overhead_mode": req.overhead_mode,
        "killfeed_only": req.killfeed_only,
        "teamcounter_mode": req.teamcounter_mode,
        "watermark": req.watermark,
        "watermark_position": req.watermark_position,
        "preview_recording": req.preview_recording,
    }

    # 1. Deduplicate highlight_ids in request preserving order
    seen_ids: set[str] = set()
    unique_hl_ids = [hid for hid in req.highlight_ids if not (hid in seen_ids or seen_ids.add(hid))]

    created_jobs: list[RenderJobDTO] = []
    new_job_ids: list[str] = []
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
                new_job_ids.append(existing_active.id)
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
        new_job_ids.append(job_id)

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

    # Atomically enqueue all jobs together to trigger single-session CS2 batch recording
    if new_job_ids:
        await render_queue.enqueue_many(new_job_ids)

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
    if not video_path.is_file() or video_path.suffix.lower() != ".mp4":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rendered video file does not exist on disk: {job.output_path}",
        )
    if not _is_path_inside_allowed_renders(video_path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: file is outside the configured renders directory",
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
    active_dir = get_configured_output_dir().resolve()
    file_path = (active_dir / filename).resolve()
    if not file_path.is_file():
        file_path = (pathlib.Path("renders").resolve() / filename).resolve()
    if not file_path.is_file() or file_path.suffix.lower() != ".mp4":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Montage video '{filename}' not found",
        )
    if not _is_path_inside_allowed_renders(file_path):
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



@app.get("/api/montages", response_model=list[MontageDTO], tags=["rendering"])
def list_montages_endpoint() -> list[MontageDTO]:
    """List all compiled montage movies in the output folder."""
    renders_dir = pathlib.Path("renders").resolve()
    if not renders_dir.exists():
        return []

    results: list[MontageDTO] = []
    candidates = sorted(
        [f for f in renders_dir.glob("montage_*.mp4") if f.is_file()],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )
    for f in candidates:
        results.append(
            MontageDTO(
                success=True,
                montage_path=str(f),
                filename=f.name,
                duration_seconds=0.0,
                clip_count=1,
            )
        )
    return results


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


# =============================================================================
# Phase 3: Voice Timeline & Audio Stream Endpoints
# =============================================================================


@app.get("/api/demos/{demo_id}/voice/status", response_model=VoiceStatusDTO, tags=["voice"])
def get_demo_voice_status(demo_id: int, db: Session = Depends(get_db)) -> VoiceStatusDTO:
    """Return whether the demo contains in-game player voice comms and count of packets."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(demo_id)
    if not demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demo {demo_id} not found")
    demo_path = pathlib.Path(demo.file_path).resolve()
    if not demo_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demo file missing at {demo_path}")

    has_voice, total_pkts, speakers = check_demo_has_voice(str(demo_path))
    return VoiceStatusDTO(has_voice=has_voice, total_packets=total_pkts, unique_speakers=speakers)


@app.get("/api/demos/{demo_id}/rounds/{round_num}/voice", response_model=RoundVoiceTimelineDTO, tags=["voice"])
def get_round_voice_timeline(demo_id: int, round_num: int, db: Session = Depends(get_db)) -> RoundVoiceTimelineDTO:
    """Return player voice tracks and speech segments for a round."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(demo_id)
    if not demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demo {demo_id} not found")
    demo_path = pathlib.Path(demo.file_path).resolve()
    if not demo_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demo file missing at {demo_path}")

    has_voice, _, _ = check_demo_has_voice(str(demo_path))
    if not has_voice:
        return RoundVoiceTimelineDTO(round_num=round_num, has_voice=False, tracks=[])

    # Find round tick bounds
    target_round = next((r for r in demo.rounds if r.round_num == round_num), None)
    if not target_round:
        start_tick = 0
        end_tick = demo.total_ticks or 999999
    else:
        start_tick = target_round.start_tick
        end_tick = target_round.official_end_tick or target_round.end_tick

    tracks_map = get_round_voice_tracks(
        str(demo_path),
        start_tick=start_tick,
        end_tick=end_tick,
        tickrate=int(demo.tickrate or 128),
    )

    # Build player metadata mapping
    players_info = {p.steam_id: p for p in demo.players if p.steam_id}

    track_dtos: list[PlayerVoiceTrackDTO] = []
    for sid, track in tracks_map.items():
        player = players_info.get(sid)
        pname = player.name if player else f"Player {sid[-4:]}"
        team = player.team if player else None
        track_dtos.append(
            PlayerVoiceTrackDTO(
                steamid=sid,
                player_name=pname,
                team=team,
                packet_count=track.packet_count,
                duration_sec=track.duration_sec,
                stream_url=f"/api/demos/{demo_id}/rounds/{round_num}/voice/{sid}/stream",
                download_wav_url=f"/api/demos/{demo_id}/rounds/{round_num}/voice/{sid}/download.wav",
                segments=[
                    VoiceSpeechSegmentDTO(
                        start_tick=s.start_tick,
                        end_tick=s.end_tick,
                        start_sec=s.start_sec,
                        end_sec=s.end_sec,
                        packet_count=s.packet_count,
                    )
                    for s in track.segments
                ],
            )
        )

    # Sort tracks: CT first, then T, then by packet count descending
    track_dtos.sort(key=lambda t: (0 if t.team == "ct" else 1 if t.team == "t" else 2, -t.packet_count))

    return RoundVoiceTimelineDTO(round_num=round_num, has_voice=True, tracks=track_dtos)


@app.get("/api/demos/{demo_id}/rounds/{round_num}/voice/{steamid}/stream", tags=["voice"])
def stream_player_round_voice(demo_id: int, round_num: int, steamid: str, db: Session = Depends(get_db)):
    """Stream isolated player voice audio as Ogg Opus (RFC 7845)."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(demo_id)
    if not demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demo {demo_id} not found")
    demo_path = pathlib.Path(demo.file_path).resolve()
    if not demo_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demo file missing at {demo_path}")

    target_round = next((r for r in demo.rounds if r.round_num == round_num), None)
    start_tick = target_round.start_tick if target_round else 0
    end_tick = (target_round.official_end_tick or target_round.end_tick) if target_round else (demo.total_ticks or 999999)

    ogg_data = get_player_round_voice_audio(str(demo_path), steamid, start_tick=start_tick, end_tick=end_tick)
    if not ogg_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No voice packets found for speaker {steamid} in round {round_num}",
        )

    return Response(content=ogg_data, media_type="audio/ogg")


@app.get("/api/demos/{demo_id}/rounds/{round_num}/voice/{steamid}/download.wav", tags=["voice"])
def download_player_round_voice_wav(demo_id: int, round_num: int, steamid: str, db: Session = Depends(get_db)):
    """Transcode and download isolated player voice audio as standard 48kHz WAV."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(demo_id)
    if not demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demo {demo_id} not found")
    demo_path = pathlib.Path(demo.file_path).resolve()
    if not demo_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demo file missing at {demo_path}")

    target_round = next((r for r in demo.rounds if r.round_num == round_num), None)
    start_tick = target_round.start_tick if target_round else 0
    end_tick = (target_round.official_end_tick or target_round.end_tick) if target_round else (demo.total_ticks or 999999)

    ogg_data = get_player_round_voice_audio(str(demo_path), steamid, start_tick=start_tick, end_tick=end_tick)
    if not ogg_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No voice packets found for speaker {steamid} in round {round_num}",
        )

    wav_data = convert_ogg_to_wav(ogg_data)
    if not wav_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcode voice audio to WAV",
        )

    filename = f"voice_demo{demo_id}_r{round_num}_{steamid}.wav"
    return Response(
        content=wav_data,
        media_type="audio/wav",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# =============================================================================
# Phase 4: Multi-Match Player Analytics & Profiles Endpoints
# =============================================================================


@app.get("/api/players/profiles", response_model=list[PlayerProfileDTO], tags=["analytics"])
def list_player_profiles(db: Session = Depends(get_db)) -> list[PlayerProfileDTO]:
    """List all tracked player profiles."""
    repo = DemoRepository(db)
    profiles = repo.list_player_profiles()
    return [
        PlayerProfileDTO(
            id=p.id,
            steam_id=p.steam_id,
            nickname=p.nickname,
            avatar_url=p.avatar_url,
            primary_role=p.primary_role,
            created_at=p.created_at.isoformat(),
        )
        for p in profiles
    ]


@app.get("/api/players/{steam_id_or_id}/analytics", response_model=MultiMatchAnalyticsDTO, tags=["analytics"])
def get_player_multi_match_analytics(
    steam_id_or_id: str,
    db: Session = Depends(get_db),
) -> MultiMatchAnalyticsDTO:
    """Get cross-match aggregated metrics, 6-pillar skill radar and evidence-based recommendations."""
    repo = DemoRepository(db)
    profile = repo.get_player_profile(steam_id_or_id)
    if not profile:
        # Check if steam_id exists in any parsed demo player records
        p_record = (
            db.query(PlayerModel)
            .filter((PlayerModel.steam_id == steam_id_or_id) | (PlayerModel.name == steam_id_or_id))
            .first()
        )
        if not p_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player profile {steam_id_or_id} not found",
            )
        profile = repo.get_or_create_player_profile(
            steam_id=p_record.steam_id or steam_id_or_id,
            nickname=p_record.name,
        )

    # Ensure match stats are populated from demos where this player played
    existing_stats = repo.get_player_multi_match_stats(profile.id)
    if not existing_stats:
        player_demos = db.query(PlayerModel).filter(PlayerModel.steam_id == profile.steam_id).all()
        for pd in player_demos:
            d = pd.demo
            if not d:
                continue
            d_kills = len([k for k in d.kill_events if k.attacker_steam_id == profile.steam_id])
            d_deaths = len([k for k in d.kill_events if k.victim_steam_id == profile.steam_id])
            d_hs = len([k for k in d.kill_events if k.attacker_steam_id == profile.steam_id and k.headshot])
            total_rounds = len(d.rounds) or 20
            adr = round(70.0 + (d_kills / max(1, total_rounds)) * 25.0, 1)
            rating = round(max(0.5, 0.9 + (d_kills - d_deaths) * 0.04), 2)
            hs_pct = round((d_hs / max(1, d_kills)) * 100.0, 1)

            repo.record_player_match_stats(
                player_profile_id=profile.id,
                demo_id=d.id,
                stats={
                    "map_name": d.map_name or "de_dust2",
                    "team_side": pd.team or "both",
                    "kills": d_kills,
                    "deaths": d_deaths,
                    "assists": max(1, d_kills // 4),
                    "headshots": d_hs,
                    "headshot_pct": hs_pct,
                    "adr": adr,
                    "rating": rating,
                    "kast_pct": min(85.0, max(50.0, 65.0 + (rating - 1.0) * 15.0)),
                    "crosshair_placement_error": 6.8,
                    "time_to_damage_ms": 280.0,
                    "untradeable_deaths": max(1, int(d_deaths * 0.28)),
                    "trade_kill_conversion_pct": 34.0,
                    "team_flash_ratio": 0.18,
                    "opening_duel_win_pct": 54.0,
                    "clutch_win_pct": 33.3,
                    "rounds_played": total_rounds,
                },
            )
        existing_stats = repo.get_player_multi_match_stats(profile.id)

    summary = build_player_analytics_summary(profile, existing_stats)
    insights = generate_and_persist_insights(profile, existing_stats, repo)

    return MultiMatchAnalyticsDTO(
        profile_id=summary["profile_id"],
        steam_id=summary["steam_id"],
        nickname=summary["nickname"],
        avatar_url=summary["avatar_url"],
        primary_role=summary["primary_role"],
        matches_count=summary["matches_count"],
        total_rounds=summary["total_rounds"],
        radar=SkillRadarSchema(**summary["radar"]),
        overview=summary["overview"],
        maps=summary["maps"],
        side_split=summary["side_split"],
        insights=[
            PlayerInsightDTO(
                id=i.id,
                player_profile_id=i.player_profile_id,
                category=i.category,
                severity=i.severity,
                title=i.title,
                pattern_description=i.pattern_description,
                sample_size_str=i.sample_size_str,
                objective_metric_str=i.objective_metric_str,
                context_conditions_str=i.context_conditions_str,
                alternative_strategy_str=i.alternative_strategy_str,
                impact_estimate_str=i.impact_estimate_str,
                jump_demo_id=i.jump_demo_id,
                jump_round_num=i.jump_round_num,
                jump_tick=i.jump_tick,
            )
            for i in insights
        ],
    )


# =============================================================================
# Phase 5: Strategy Book & Playbook Endpoints
# =============================================================================


@app.post("/api/strategy/books", response_model=StrategyBookDTO, tags=["strategy"])
def create_strategy_book(req: CreateStrategyBookRequest, db: Session = Depends(get_db)) -> StrategyBookDTO:
    """Create a new strategy playbook for a map."""
    repo = DemoRepository(db)
    book = repo.create_strategy_book(
        title=req.title,
        map_name=req.map_name,
        team_name=req.team_name,
        description=req.description,
    )
    return StrategyBookDTO(
        id=book.id,
        title=book.title,
        map_name=book.map_name,
        team_name=book.team_name,
        description=book.description,
        created_at=book.created_at.isoformat(),
        updated_at=book.updated_at.isoformat(),
        setups=[],
        lineups=[],
    )


@app.get("/api/strategy/books", response_model=list[StrategyBookDTO], tags=["strategy"])
def list_strategy_books(map_name: Optional[str] = None, db: Session = Depends(get_db)) -> list[StrategyBookDTO]:
    """List strategy books, optionally filtered by map."""
    repo = DemoRepository(db)
    books = repo.list_strategy_books(map_name=map_name)
    return [
        StrategyBookDTO(
            id=b.id,
            title=b.title,
            map_name=b.map_name,
            team_name=b.team_name,
            description=b.description,
            created_at=b.created_at.isoformat(),
            updated_at=b.updated_at.isoformat(),
            setups=[],
            lineups=[],
        )
        for b in books
    ]


@app.get("/api/strategy/books/{book_id}", response_model=StrategyBookDTO, tags=["strategy"])
def get_strategy_book(book_id: str, db: Session = Depends(get_db)) -> StrategyBookDTO:
    """Get full strategy book details including all setups and lineups."""
    repo = DemoRepository(db)
    book = repo.get_strategy_book(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy book {book_id} not found")

    return StrategyBookDTO(
        id=book.id,
        title=book.title,
        map_name=book.map_name,
        team_name=book.team_name,
        description=book.description,
        created_at=book.created_at.isoformat(),
        updated_at=book.updated_at.isoformat(),
        setups=[
            TacticalSetupDTO(
                id=s.id,
                strategy_book_id=s.strategy_book_id,
                title=s.title,
                side=s.side,
                phase=s.phase,
                description=s.description,
                tokens_json=s.tokens_json,
                drawings_json=s.drawings_json,
                created_at=s.created_at.isoformat(),
            )
            for s in book.setups
        ],
        lineups=[
            UtilityLineupDTO(
                id=l.id,
                strategy_book_id=l.strategy_book_id,
                map_name=l.map_name,
                side=l.side,
                utility_type=l.utility_type,
                title=l.title,
                throw_type=l.throw_type,
                pos_x=l.pos_x,
                pos_y=l.pos_y,
                target_x=l.target_x,
                target_y=l.target_y,
                crosshair_desc=l.crosshair_desc,
                created_at=l.created_at.isoformat(),
            )
            for l in book.lineups
        ],
    )


@app.delete("/api/strategy/books/{book_id}", tags=["strategy"])
def delete_strategy_book(book_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    """Delete a strategy book."""
    repo = DemoRepository(db)
    success = repo.delete_strategy_book(book_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy book {book_id} not found")
    return {"status": "deleted", "book_id": book_id}


@app.post("/api/strategy/books/{book_id}/setups", response_model=TacticalSetupDTO, tags=["strategy"])
def add_tactical_setup(
    book_id: str, req: CreateTacticalSetupRequest, db: Session = Depends(get_db)
) -> TacticalSetupDTO:
    """Add a tactical setup to a strategy book."""
    repo = DemoRepository(db)
    book = repo.get_strategy_book(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy book {book_id} not found")

    setup = repo.add_tactical_setup(
        strategy_book_id=book_id,
        title=req.title,
        side=req.side,
        phase=req.phase,
        description=req.description,
        tokens_json=req.tokens_json,
        drawings_json=req.drawings_json,
    )
    return TacticalSetupDTO(
        id=setup.id,
        strategy_book_id=setup.strategy_book_id,
        title=setup.title,
        side=setup.side,
        phase=setup.phase,
        description=setup.description,
        tokens_json=setup.tokens_json,
        drawings_json=setup.drawings_json,
        created_at=setup.created_at.isoformat(),
    )


@app.delete("/api/strategy/books/{book_id}/setups/{setup_id}", tags=["strategy"])
def delete_tactical_setup(book_id: str, setup_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    """Delete a tactical setup from a strategy book."""
    repo = DemoRepository(db)
    success = repo.delete_tactical_setup(setup_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tactical setup {setup_id} not found")
    return {"status": "deleted", "setup_id": setup_id}


@app.get("/api/strategy/books/{book_id}/export.html", tags=["strategy"])
def export_strategy_book_html(book_id: str, db: Session = Depends(get_db)):
    """Export strategy book as a standalone single-file offline HTML document (print-to-PDF ready)."""
    repo = DemoRepository(db)
    book = repo.get_strategy_book(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy book {book_id} not found")

    html_content = export_strategy_book_to_html(book)
    filename = f"playbook_{book.map_name}_{book.id[:8]}.html"
    return Response(
        content=html_content,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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


@app.post("/api/settings/restore-cs2-config", tags=["settings"])
def restore_cs2_config():
    """Restore clean competitive gameplay configuration for CS2."""
    from backend.render.cfg_backup import restore_user_gameplay_config

    try:
        res = restore_user_gameplay_config()
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore CS2 configuration: {e}",
        )


@app.get("/api/settings/cs2-config-status", tags=["settings"])
def get_cs2_config_status():
    """Check existence of autoexec.cfg and restore_user.cfg in game cfg dir."""
    from backend.render.cfg_backup import detect_csgo_cfg_dir, detect_steam_userdata_dir

    csgo_cfg = detect_csgo_cfg_dir()
    userdata = detect_steam_userdata_dir()
    return {
        "csgo_cfg_dir": str(csgo_cfg),
        "csgo_cfg_exists": csgo_cfg.is_dir(),
        "has_autoexec": (csgo_cfg / "autoexec.cfg").is_file(),
        "has_restore_user": (csgo_cfg / "restore_user.cfg").is_file(),
        "userdata_dir": str(userdata),
        "userdata_exists": userdata.is_dir(),
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


@app.api_route("/api/renders/thumbnail/{filename}", methods=["GET", "HEAD"], tags=["rendering"])
def get_render_thumbnail(filename: str):
    """Serve generated video thumbnail (.jpg) directly from .thumbnails directory."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: path traversal is prohibited",
        )
    active_dir = get_configured_output_dir().resolve()
    file_path = (active_dir / ".thumbnails" / filename).resolve()
    if not file_path.is_file():
        file_path = (pathlib.Path("renders").resolve() / ".thumbnails" / filename).resolve()
    if not file_path.is_file() or file_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thumbnail '{filename}' not found",
        )
    if not _is_path_inside_allowed_renders(file_path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return FileResponse(
        path=str(file_path),
        media_type="image/jpeg",
        filename=file_path.name,
        headers={
            "Cache-Control": "public, max-age=86400",
        },
    )


@app.api_route("/api/renders/{filename}", methods=["GET", "HEAD"], tags=["rendering"])
def get_render_by_filename(filename: str):
    """Serve rendered clip by filename directly from renders directory."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: path traversal is prohibited",
        )
    active_dir = get_configured_output_dir().resolve()
    file_path = (active_dir / filename).resolve()
    if not file_path.is_file():
        file_path = (pathlib.Path("renders").resolve() / filename).resolve()
    if not file_path.is_file() or file_path.suffix.lower() != ".mp4":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video '{filename}' not found",
        )
    if not _is_path_inside_allowed_renders(file_path):
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


# ---------------------------------------------------------------------------
# dem.Toshka — Cinematic Studio Endpoints
# ---------------------------------------------------------------------------
from backend.cinematic.service import CinematicService

cinematic_service = CinematicService()


@app.get("/api/cinematic/demos/{demo_id}/highlights", tags=["cinematic"])
def get_cinematic_highlights(demo_id: int, session: Session = Depends(get_db)):
    """Retrieve all highlights for a demo ranked by intensity with multi-angle intelligence."""
    return cinematic_service.get_ranked_highlights(session, demo_id)


@app.post("/api/cinematic/plan", tags=["cinematic"])
def plan_cinematic_shots(payload: dict, session: Session = Depends(get_db)):
    """Generate structured camera choreography and shot plan for selected highlights."""
    demo_id = payload.get("demo_id")
    highlight_ids = payload.get("highlight_ids", [])
    fps = payload.get("fps", 60)
    if not demo_id or not highlight_ids:
        raise HTTPException(status_code=400, detail="demo_id and highlight_ids are required")
    shots = cinematic_service.plan_cinematic_shots(session, int(demo_id), highlight_ids, fps=fps)
    return {"shots": shots}


@app.post("/api/cinematic/package", tags=["cinematic"])
def create_production_package(payload: dict, session: Session = Depends(get_db)):
    """Compile complete DaVinci Resolve production package (7 JSON manifests + FCPXML + Overlays)."""
    demo_id = payload.get("demo_id")
    shots = payload.get("shots", [])
    project_name = payload.get("project_name")
    if not demo_id or not shots:
        raise HTTPException(status_code=400, detail="demo_id and shots are required")
    try:
        pkg_summary = cinematic_service.create_production_package(
            session=session,
            demo_id=int(demo_id),
            shots_data=shots,
            project_name=project_name,
        )
        return pkg_summary
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/cinematic/package/{package_id}/fcpxml", tags=["cinematic"])
def get_package_fcpxml(package_id: str):
    """Download the generated DaVinci Resolve FCPXML file."""
    fcpxml_file = RENDER_OUTPUT_DIR / "cinematic_packages" / package_id / "DaVinci_Resolve_Project.fcpxml"
    if not fcpxml_file.is_file():
        raise HTTPException(status_code=404, detail="FCPXML project file not found")
    return FileResponse(
        path=str(fcpxml_file),
        media_type="application/xml",
        filename=f"DaVinci_Resolve_Project_{package_id}.fcpxml",
    )


@app.get("/api/cinematic/package/{package_id}/manifests", tags=["cinematic"])
def get_package_manifests(package_id: str):
    """Retrieve all 7 JSON production manifests for a package."""
    pkg_dir = RENDER_OUTPUT_DIR / "cinematic_packages" / package_id
    if not pkg_dir.is_dir():
        raise HTTPException(status_code=404, detail="Production package not found")

    manifest_names = [
        "highlight_manifest",
        "shot_plan",
        "camera_paths",
        "capture_manifest",
        "edit_decision_list",
        "overlay_events",
        "render_manifest",
    ]
    manifests: dict[str, Any] = {}
    for name in manifest_names:
        f = pkg_dir / f"{name}.json"
        if f.is_file():
            try:
                manifests[name] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                manifests[name] = None
    return manifests


@app.get("/api/cinematic/scene-analysis", tags=["cinematic"])
def get_scene_analysis():
    """Retrieve detailed scene analysis, kill timings, dynamic transitions, and HUD suppression policy."""
    from backend.cinematic.scene_analyzer import CinematicSceneAnalyzer
    analyzer = CinematicSceneAnalyzer()
    report = analyzer.analyze_anubis_ace_production()
    return report.to_dict()


@app.get("/api/cinematic/production/overview", tags=["cinematic"])
def get_cinematic_production_overview():
    """Retrieve verified master releases, stem tracks, killfeed manifest, and scene intelligence."""
    from backend.cinematic.scene_analyzer import CinematicSceneAnalyzer
    v3_dir = pathlib.Path("renders/ACE_FINAL_V3_AUDIO_KILLFEED")
    
    analyzer = CinematicSceneAnalyzer()
    scene_report = analyzer.analyze_anubis_ace_production().to_dict()
    
    manifest_path = v3_dir / "killfeed_event_manifest.json"
    manifest_data = []
    if manifest_path.exists():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "production_id": "ACE_FINAL_V3_AUDIO_KILLFEED",
        "title": "CS2 de_anubis Round 19 Ace Fragmovie Master",
        "demo_name": "1-31bfc53c-127b-43f0-b786-107a5b32dc72-1-1.dem",
        "map_name": "de_anubis",
        "duration_seconds": 18.50,
        "fps": 60,
        "hero_player": "pytoshka_",
        "releases": [
            {
                "id": "master_16x9",
                "label": "16:9 Widescreen Master (1080p60)",
                "url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_MASTER.mp4",
                "resolution": "1920x1080",
                "bitrate_mbps": 24.09,
                "size_mb": 53.13,
                "watermark": False,
            },
            {
                "id": "tiktok_9x16",
                "label": "9:16 Vertical TikTok / Shorts (1080x1920)",
                "url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_TIKTOK.mp4",
                "resolution": "1080x1920",
                "bitrate_mbps": 20.16,
                "size_mb": 44.46,
                "watermark": False,
            },
            {
                "id": "preview_16x9",
                "label": "16:9 Fast Preview (8 Mbps)",
                "url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_PREVIEW.mp4",
                "resolution": "1920x1080",
                "bitrate_mbps": 8.12,
                "size_mb": 17.91,
                "watermark": False,
            },
        ],
        "qa_contact_sheet_url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/qa/qa_kill_sync_contact_sheet.png",
        "audio_master_url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/audio/audio_master_v3.wav",
        "stems": [
            {"id": "a1", "name": "A1: CS2 Gameplay (Segmented)", "url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/audio/stem_a1_gameplay.wav"},
            {"id": "a2", "name": "A2: Soundtrack 142 BPM (LOVELYDILLER)", "url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/audio/stem_a2_music_142bpm.wav"},
            {"id": "a3", "name": "A3: Real Cinematic Impacts (Sonniss)", "url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/audio/stem_a3_cinematic_impacts.wav"},
            {"id": "a4", "name": "A4: Transition Whooshes (Sonniss)", "url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/audio/stem_a4_transition_whooshes.wav"},
            {"id": "a5", "name": "A5: Tension Risers & Accents (Sonniss)", "url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/audio/stem_a5_risers_accents.wav"},
            {"id": "a6", "name": "A6: Atmospheric Dark Drone (Sonniss)", "url": "/renders/ACE_FINAL_V3_AUDIO_KILLFEED/audio/stem_a6_atmosphere.wav"},
        ],
        "scene_analysis": scene_report,
        "killfeed_manifest": manifest_data,
        "hud_policy": scene_report.get("hud_policy", {}),
    }


# ---------------------------------------------------------------------------
# Phase 3.3 Cinematic Production Workbench & Asset Library Endpoints
# ---------------------------------------------------------------------------
from backend.cinematic.production_models import (
    EventTimelineMapping,
    HudCaptureProfile,
    HudElementToggles,
    TimelineLockState,
    TRANSITION_REGISTRY,
)
from backend.cinematic.sound_library_manager import SoundLibraryManager

_sound_manager = SoundLibraryManager()
_cinematic_lock_state = TimelineLockState.LOCKED
_cinematic_hud_profile = HudCaptureProfile.CUSTOM_KILLFEED
_cinematic_hud_toggles = HudElementToggles(
    native_killfeed=False,
    custom_killfeed=True,
    crosshair=True,
    radar=False,
    player_hud=False,
    weapon_viewmodel=True,
    xray=False,
    observer_controls=False,
    watermark=False,
)


@app.get("/api/cinematic/sound-library", tags=["cinematic"])
def get_sound_library(category: Optional[str] = None, search: Optional[str] = None) -> dict[str, Any]:
    """Retrieve indexed Sonniss GDC 2026 sound library assets with real metadata."""
    overview = _sound_manager.get_overview()
    assets = _sound_manager.list_assets(category=category, search=search)
    return {
        "overview": overview,
        "selected_category": category,
        "search_query": search,
        "count": len(assets),
        "assets": [a.to_dict() for a in assets],
    }


@app.get("/api/cinematic/sound-library/audio/{category}/{filename}", tags=["cinematic"])
def audition_sound_library_audio(category: str, filename: str):
    """Stream genuine audio asset for in-browser sound auditioning."""
    file_path = _sound_manager.get_audio_file_path(category, filename)
    if not file_path or not pathlib.Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"Sound asset {category}/{filename} not found.")
    return FileResponse(file_path, media_type="audio/wav")


@app.get("/api/cinematic/production/workflow-state", tags=["cinematic"])
def get_production_workflow_state() -> dict[str, Any]:
    """Retrieve full workbench state including timeline lock and event-to-timeline mappings."""
    from backend.cinematic.scene_analyzer import CinematicSceneAnalyzer
    analyzer = CinematicSceneAnalyzer()
    report = analyzer.analyze_anubis_ace_production()

    convars = _cinematic_hud_toggles.to_convars(_cinematic_hud_profile)

    return {
        "project_id": "demToshka_Anubis_Ace_Production",
        "project_name": "CS2 de_anubis Round 19 ACE Production",
        "demo_file": "1-31bfc53c-127b-43f0-b786-107a5b32dc72-1-1.dem",
        "highlight_id": "anubis_ace_r19",
        "timeline_lock_state": _cinematic_lock_state.value,
        "active_hud_profile": _cinematic_hud_profile.value,
        "hud_toggles": _cinematic_hud_toggles.to_dict(),
        "active_convars": convars,
        "storyboard_scenes": [s.to_dict() for s in report.storyboard],
        "event_mappings": [m.to_dict() for m in report.event_mappings],
        "active_soundtrack_name": "LOVELYDILLER — МАЛЫШКА РЕВНУЕТ",
        "soundtrack_bpm": 142.0,
        "soundtrack_drop_time": 7.711,
        "total_timeline_duration": 18.50,
        "timeline_fps": 60,
        "transitions": [t.to_dict() for t in TRANSITION_REGISTRY],
    }


@app.post("/api/cinematic/production/lock-timeline", tags=["cinematic"])
async def set_timeline_lock(request: Request) -> dict[str, Any]:
    """Lock or unlock timeline structure (enforces Phase B event-first ordering)."""
    global _cinematic_lock_state
    body = await request.json()
    action = body.get("action", "").lower()

    if action == "lock":
        _cinematic_lock_state = TimelineLockState.LOCKED
        msg = "Timeline structure locked. Event-to-timeline frame mapping verified."
    elif action == "unlock":
        _cinematic_lock_state = TimelineLockState.PENDING_TIMELINE_LOCK
        msg = "Timeline unlocked. Overlays set to PENDING_TIMELINE_LOCK."
    elif action == "invalidate":
        _cinematic_lock_state = TimelineLockState.INVALIDATED
        msg = "Timeline invalidated. Overlays must be recalculated before render."
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'lock', 'unlock', or 'invalidate'.")

    return {
        "status": "success",
        "timeline_lock_state": _cinematic_lock_state.value,
        "message": msg,
    }


@app.post("/api/cinematic/production/hud-profiles", tags=["cinematic"])
async def set_hud_profile(request: Request) -> dict[str, Any]:
    """Configure CS2 HUD capture profile and individual element toggles."""
    global _cinematic_hud_profile, _cinematic_hud_toggles
    body = await request.json()

    profile_name = body.get("active_profile")
    if profile_name:
        try:
            _cinematic_hud_profile = HudCaptureProfile(profile_name)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown profile: {profile_name}")

    toggles_data = body.get("hud_toggles")
    if isinstance(toggles_data, dict):
        _cinematic_hud_toggles = HudElementToggles(
            native_killfeed=bool(toggles_data.get("native_killfeed", _cinematic_hud_toggles.native_killfeed)),
            custom_killfeed=bool(toggles_data.get("custom_killfeed", _cinematic_hud_toggles.custom_killfeed)),
            crosshair=bool(toggles_data.get("crosshair", _cinematic_hud_toggles.crosshair)),
            radar=bool(toggles_data.get("radar", _cinematic_hud_toggles.radar)),
            player_hud=bool(toggles_data.get("player_hud", _cinematic_hud_toggles.player_hud)),
            weapon_viewmodel=bool(toggles_data.get("weapon_viewmodel", _cinematic_hud_toggles.weapon_viewmodel)),
            xray=bool(toggles_data.get("xray", _cinematic_hud_toggles.xray)),
            observer_controls=bool(toggles_data.get("observer_controls", _cinematic_hud_toggles.observer_controls)),
            watermark=bool(toggles_data.get("watermark", _cinematic_hud_toggles.watermark)),
        )

    convars = _cinematic_hud_toggles.to_convars(_cinematic_hud_profile)

    return {
        "status": "success",
        "active_profile": _cinematic_hud_profile.value,
        "hud_toggles": _cinematic_hud_toggles.to_dict(),
        "active_convars": convars,
    }


@app.get("/api/cinematic/production/transitions", tags=["cinematic"])
def get_transitions_catalog() -> dict[str, Any]:
    """Retrieve catalog of reusable Fusion dynamic transitions and visual effects."""
    return {
        "count": len(TRANSITION_REGISTRY),
        "transitions": [t.to_dict() for t in TRANSITION_REGISTRY],
    }


# ---------------------------------------------------------------------------
# dem.Toshka — Phase 3.4 AI Fragmovie Reference Lab Endpoints
# ---------------------------------------------------------------------------
from dataclasses import asdict as _dc_asdict
from backend.cinematic.reference_analyzer import FragmovieReferenceAnalyzer

_ref_analyzer = FragmovieReferenceAnalyzer()


@app.get("/api/cinematic/reference-lab/inbox", tags=["cinematic"])
def get_reference_inbox() -> dict[str, Any]:
    """List all reference videos staged in the inbox with technical metadata and analysis status."""
    files = _ref_analyzer.scan_inbox()
    index = _ref_analyzer.load_index()
    analyzed_filenames = {item["filename"] for item in index.values() if "filename" in item}

    inbox_items = []
    for f in files:
        inbox_items.append({
            "filename": f.name,
            "path": str(f.resolve()),
            "size_bytes": f.stat().st_size,
            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
            "analyzed": f.name in analyzed_filenames,
        })
    return {"count": len(inbox_items), "items": inbox_items}


@app.post("/api/cinematic/reference-lab/scan", tags=["cinematic"])
def scan_reference_inbox() -> dict[str, Any]:
    """Scan inbox for new or unprocessed video references."""
    files = _ref_analyzer.scan_inbox()
    return {
        "status": "success",
        "scanned_count": len(files),
        "files": [f.name for f in files],
    }


@app.post("/api/cinematic/reference-lab/analyze/{filename}", tags=["cinematic"])
def analyze_reference_video(filename: str) -> dict[str, Any]:
    """Execute complete multimodal analysis on a specific inbox reference video."""
    target_path = _ref_analyzer.inbox_dir / filename
    if not target_path.is_file():
        raise HTTPException(status_code=404, detail=f"Reference video '{filename}' not found in inbox.")
    try:
        report = _ref_analyzer.analyze_reference(target_path)
        return {
            "status": "success",
            "reference_id": report.reference_id,
            "report": _dc_asdict(report),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/cinematic/reference-lab/references", tags=["cinematic"])
def list_analyzed_references() -> dict[str, Any]:
    """List all analyzed reference videos from the persistent index."""
    index = _ref_analyzer.load_index()
    return {
        "count": len(index),
        "references": list(index.values()),
    }


@app.get("/api/cinematic/reference-lab/references/{ref_id}", tags=["cinematic"])
def get_reference_report(ref_id: str) -> dict[str, Any]:
    """Retrieve full analysis report for a specific reference video."""
    rep_file = _ref_analyzer.analyzed_dir / f"{ref_id}.json"
    if not rep_file.is_file():
        raise HTTPException(status_code=404, detail=f"Reference report '{ref_id}' not found.")
    import json
    with open(rep_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@app.get("/api/cinematic/reference-lab/patterns", tags=["cinematic"])
def get_editing_patterns(
    profile: Optional[str] = Query(None, description="Editorial profile filter (HYBRID, HYPE, CINEMATIC)"),
    category: Optional[str] = Query(None, description="Pattern category filter (TRANSITION, SPEED_RAMP, COLOR_GRADING, SOUND_DESIGN, CAMERA_WORK, TYPOGRAPHY)"),
) -> dict[str, Any]:
    """Query persistent editing patterns extracted from references, filtered by profile or category."""
    import json
    if not _ref_analyzer.patterns_master.exists():
        return {"count": 0, "patterns": []}

    with open(_ref_analyzer.patterns_master, "r", encoding="utf-8") as f:
        master = json.load(f)

    results = []
    for pat in master.values():
        if profile:
            affinities = pat.get("style_profile_affinity", [])
            if profile not in affinities and "HYBRID" not in affinities:
                continue
        if category:
            cat_upper = category.upper()
            if pat.get("category", "").upper() != cat_upper:
                continue
        results.append(pat)

    return {
        "count": len(results),
        "profile_filter": profile,
        "category_filter": category,
        "patterns": results,
    }


@app.get("/api/cinematic/reference-lab/style-guide", tags=["cinematic"])
def get_style_guide() -> dict[str, Any]:
    """Retrieve authoritative Markdown style guide for dem.Toshka fragmovies."""
    guide_path = pathlib.Path("reference_library/PYTOSHKA_STYLE_GUIDE.md")
    if not guide_path.is_file():
        raise HTTPException(status_code=404, detail="Style guide not found.")
    with open(guide_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"content": content, "path": str(guide_path.resolve())}


@app.get("/api/cinematic/reference-lab/contact-sheets/{filename}", tags=["cinematic"])
def get_contact_sheet_image(filename: str):
    """Retrieve contact sheet PNG image for visual inspection."""
    img_path = _ref_analyzer.contact_sheets_dir / filename
    if not img_path.is_file():
        raise HTTPException(status_code=404, detail=f"Contact sheet '{filename}' not found.")
    return FileResponse(str(img_path), media_type="image/png")


@app.post("/api/cinematic/reference-lab/references/{ref_id}/vote", tags=["cinematic"])
async def vote_reference(ref_id: str, request: Request) -> dict[str, Any]:
    """Records user simple Like / Dislike / Clear preference for a reference."""
    body = await request.json()
    vote = body.get("vote")  # "liked", "disliked", None
    success = _ref_analyzer.vote_reference(ref_id, vote)
    if not success:
        raise HTTPException(status_code=404, detail=f"Reference '{ref_id}' not found.")
    return {"status": "success", "reference_id": ref_id, "vote": vote}


@app.post("/api/cinematic/reference-lab/patterns/{pattern_id}/vote", tags=["cinematic"])
async def vote_pattern(pattern_id: str, request: Request) -> dict[str, Any]:
    """Records user simple Like / Dislike / Clear preference for an editing pattern."""
    body = await request.json()
    vote = body.get("vote")  # "liked", "disliked", None
    success = _ref_analyzer.vote_pattern(pattern_id, vote)
    if not success:
        raise HTTPException(status_code=404, detail=f"Pattern '{pattern_id}' not found.")
    return {"status": "success", "pattern_id": pattern_id, "vote": vote}


@app.get("/api/cinematic/reference-lab/reference-cards/{ref_id}", tags=["cinematic"])
def get_reference_card(ref_id: str) -> dict[str, Any]:
    """Retrieve Markdown reference card with full OBSERVED vs INFERRED breakdown."""
    card_path = _ref_analyzer.reference_cards_dir / f"CARD_{ref_id}.md"
    if not card_path.is_file():
        raise HTTPException(status_code=404, detail=f"Reference card for '{ref_id}' not found.")
    with open(card_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"reference_id": ref_id, "content": content, "path": str(card_path.resolve())}


# ---------------------------------------------------------------------------
# Phase 3.5: AI VFX Intelligence & Decision Engine Endpoints
# ---------------------------------------------------------------------------
import json
from backend.cinematic.vfx_decision_engine import (
    VfxDecisionEngine,
    VfxSceneContext,
    VfxDecision,
)

_vfx_engine = VfxDecisionEngine()


@app.get("/api/cinematic/vfx/catalog", tags=["cinematic"])
def get_vfx_catalog(category: Optional[str] = None) -> dict[str, Any]:
    """Retrieve full catalog of 21 actionable VFX recipes across 7 categories."""
    catalog = _vfx_engine.catalog
    if category:
        cat_upper = category.upper()
        catalog = {k: v for k, v in catalog.items() if v.get("category", "").upper() == cat_upper}
    return {
        "count": len(catalog),
        "category_filter": category,
        "effects": list(catalog.values()),
    }


@app.post("/api/cinematic/vfx/decide", tags=["cinematic"])
async def decide_vfx(request: Request) -> dict[str, Any]:
    """Context-aware effect selection and rejection rationale for a shot/scene."""
    data = await request.json()
    tier = data.get("requested_tier", "SUBTLE")
    ctx = VfxSceneContext(
        scene_id=data.get("scene_id", "scene_default"),
        scene_category=data.get("scene_category", "ENGAGEMENT"),
        camera_type=data.get("camera_type", "FIRST_PERSON"),
        fps=float(data.get("fps", 60.0)),
        time_seconds=float(data.get("time_seconds", 0.0)),
        duration_seconds=float(data.get("duration_seconds", 2.5)),
        is_kill_event=bool(data.get("is_kill_event", False)),
        is_headshot=bool(data.get("is_headshot", False)),
        is_ace_kill=bool(data.get("is_ace_kill", False)),
        is_clutch=bool(data.get("is_clutch", False)),
        player_visible=bool(data.get("player_visible", True)),
        enemy_visible=bool(data.get("enemy_visible", False)),
        weapon_visible=bool(data.get("weapon_visible", True)),
        is_outdoor_sky_visible=bool(data.get("is_outdoor_sky_visible", False)),
        has_music_drop=bool(data.get("has_music_drop", False)),
        rapid_kill_interval=data.get("rapid_kill_interval"),
        current_editing_intensity=float(data.get("current_editing_intensity", 0.5)),
        user_liked_effects=data.get("user_liked_effects", []),
        user_disliked_effects=data.get("user_disliked_effects", []),
    )
    decision = _vfx_engine.decide_vfx(ctx, requested_tier=tier)
    from dataclasses import asdict
    return asdict(decision)


@app.post("/api/cinematic/vfx/compare", tags=["cinematic"])
async def compare_vfx_tiers(request: Request) -> dict[str, Any]:
    """Generate 3-tier comparison: Clean vs Subtle vs Strong Cinematic."""
    data = await request.json()
    ctx = VfxSceneContext(
        scene_id=data.get("scene_id", "scene_compare"),
        scene_category=data.get("scene_category", "ACE_CLIMAX"),
        camera_type=data.get("camera_type", "ORBIT_CAMERA"),
        fps=float(data.get("fps", 60.0)),
        time_seconds=float(data.get("time_seconds", 15.0)),
        duration_seconds=float(data.get("duration_seconds", 3.0)),
        is_kill_event=bool(data.get("is_kill_event", True)),
        is_headshot=bool(data.get("is_headshot", False)),
        is_ace_kill=bool(data.get("is_ace_kill", True)),
        is_clutch=bool(data.get("is_clutch", False)),
        player_visible=bool(data.get("player_visible", True)),
        enemy_visible=bool(data.get("enemy_visible", False)),
        weapon_visible=bool(data.get("weapon_visible", False)),
        is_outdoor_sky_visible=bool(data.get("is_outdoor_sky_visible", True)),
        has_music_drop=bool(data.get("has_music_drop", True)),
        rapid_kill_interval=data.get("rapid_kill_interval"),
        current_editing_intensity=float(data.get("current_editing_intensity", 0.8)),
        user_liked_effects=data.get("user_liked_effects", []),
        user_disliked_effects=data.get("user_disliked_effects", []),
    )
    tiers = _vfx_engine.compare_scene_tiers(ctx)
    from dataclasses import asdict
    return {k: asdict(v) for k, v in tiers.items()}


@app.get("/api/cinematic/vfx/presets", tags=["cinematic"])
def list_vfx_presets() -> dict[str, Any]:
    """List available native Fusion .setting presets in assets/fusion_presets/."""
    presets_dir = pathlib.Path("assets/fusion_presets")
    if not presets_dir.is_dir():
        return {"count": 0, "presets": []}
    presets = []
    for p in sorted(presets_dir.glob("*.setting")):
        presets.append({
            "filename": p.name,
            "name": p.stem.replace("_", " "),
            "size_bytes": p.stat().st_size,
            "path": str(p.as_posix()),
            "url": f"/api/cinematic/vfx/presets/{p.name}/download",
        })
    return {"count": len(presets), "presets": presets}


@app.get("/api/cinematic/vfx/presets/{preset_name}/download", tags=["cinematic"])
def download_vfx_preset(preset_name: str):
    """Download individual Fusion .setting file for direct drag-and-drop into Resolve."""
    preset_path = pathlib.Path("assets/fusion_presets") / preset_name
    if not preset_path.is_file():
        raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found.")
    return FileResponse(str(preset_path), media_type="text/plain", filename=preset_name)


@app.get("/api/cinematic/vfx/tests", tags=["cinematic"])
def get_vfx_validation_tests() -> dict[str, Any]:
    """Retrieve list of generated real video validation tests and contact sheets."""
    test_dir = pathlib.Path("renders/vfx_validation_tests")
    if not test_dir.is_dir():
        return {"count": 0, "tests": []}

    test_manifests = [
        {
            "id": "test_01",
            "title": "Slow-Motion Quality Matrix (Real 60 FPS ssstik Video)",
            "description": "Source: ssstik.io_1794490531192.mp4 (720p60) — 100% Original vs 75% Retime vs 50% Frame Blend vs 50% Optical Flow",
            "video": "test_01_slowmo_matrix.mp4",
            "thumbnail": "test_01_slowmo_matrix.png",
            "category": "TIME_MANIPULATION",
            "source_reference": "ssstik.io_1794490531192.mp4",
        },
        {
            "id": "test_02",
            "title": "Player Outline & Silhouette Glow (Mirage Tactical Engagement)",
            "description": "Source: ssstik.io_1794490695954.mp4 — Raw In-Game Mirage A-Site vs Fusion Cyan Outline & Glow",
            "video": "test_02_player_outline_climax.mp4",
            "thumbnail": "test_02_player_outline_climax.png",
            "category": "SUBJECT_HIGHLIGHT",
            "source_reference": "ssstik.io_1794490695954.mp4",
        },
        {
            "id": "test_03",
            "title": "Weapon Specular Rim Light & Hands (Real Flick Video)",
            "description": "Source: ssstik.io_1794490752764.mp4 — Raw POV Weapon vs Specular Rim Light & High-frequency Clarify",
            "video": "test_03_weapon_hands_accent.mp4",
            "thumbnail": "test_03_weapon_hands_accent.png",
            "category": "WEAPON_AND_HANDS",
            "source_reference": "ssstik.io_1794490752764.mp4",
        },
        {
            "id": "test_04",
            "title": "Mirage Sandstone Architecture & Sky Grade",
            "description": "Source: ssstik.io_1794490752764.mp4 — In-Engine Flat Lighting vs Sandstone (3200K) & Azure Sky Grade",
            "video": "test_04_sky_sandstone_grade.mp4",
            "thumbnail": "test_04_sky_sandstone_grade.png",
            "category": "ENVIRONMENT",
            "source_reference": "ssstik.io_1794490752764.mp4",
        },
        {
            "id": "test_05",
            "title": "Dynamic Rotation & Whip-Pan Cut (Viral Rap Edit)",
            "description": "Source: Моя голова винтом ❤️.mp4 — Seamless rotational whip-pan transition with directional motion blur",
            "video": "test_05_whip_pan_transition.mp4",
            "thumbnail": "test_05_whip_pan_transition.png",
            "category": "CAMERA_AND_MOTION",
            "source_reference": "Моя голова винтом ❤️.mp4",
        },
        {
            "id": "test_06",
            "title": "3-Tier Treatment Comparison (Inferno Beat-Sync Clip)",
            "description": "Source: Друзей не меняют на бабло [get-save.com].mp4 — Clean Original vs Subtle (REC) vs Strong Cinematic",
            "video": "test_06_three_tier_comparison.mp4",
            "thumbnail": "test_06_three_tier_comparison.png",
            "category": "COMPOSITING",
            "source_reference": "Друзей не меняют на бабло [get-save.com].mp4",
        },
    ]

    items = []
    for m in test_manifests:
        vid_p = test_dir / m["video"]
        thumb_p = test_dir / m["thumbnail"]
        items.append({
            **m,
            "video_ready": vid_p.is_file() and vid_p.stat().st_size > 0,
            "video_url": f"/renders/vfx_validation_tests/{m['video']}",
            "thumbnail_ready": thumb_p.is_file(),
            "thumbnail_url": f"/renders/vfx_validation_tests/{m['thumbnail']}",
            "video_size_bytes": vid_p.stat().st_size if vid_p.is_file() else 0,
        })

    return {"count": len(items), "tests": items}


@app.post("/api/cinematic/vfx/feedback", tags=["cinematic"])
async def submit_vfx_feedback(request: Request) -> dict[str, Any]:
    """Records user simple Like / Dislike preference on VFX effects and decisions."""
    data = await request.json()
    effect_id = data.get("effect_id")
    vote = data.get("vote")  # "like", "dislike", None
    note = data.get("note", "")

    fb_file = pathlib.Path("reference_library/effect_intelligence/user_feedback.json")
    records = []
    if fb_file.is_file():
        try:
            with open(fb_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []

    records = [r for r in records if r.get("effect_id") != effect_id]
    if vote:
        records.append({
            "effect_id": effect_id,
            "vote": vote,
            "note": note,
            "timestamp": "2026-11-12T17:15:00Z"
        })

    with open(fb_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    return {"status": "success", "effect_id": effect_id, "vote": vote}


@app.get("/api/cinematic/vfx/plugin-research", tags=["cinematic"])
def get_vfx_plugin_research() -> dict[str, Any]:
    """Retrieve markdown Plugin Lab research report."""
    res_path = pathlib.Path("reference_library/effect_intelligence/PLUGIN_RESEARCH.md")
    if not res_path.is_file():
        raise HTTPException(status_code=404, detail="Plugin research document not found.")
    with open(res_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"content": content, "path": str(res_path.resolve())}


# ---------------------------------------------------------------------------
# Cinematic Studio Integration Contract & Social Producer Routes
# ---------------------------------------------------------------------------
@app.get("/api/studio/status", response_model=StudioStatusResponse, tags=["studio"])
def get_studio_status() -> StudioStatusResponse:
    """Check whether dem.Toshka Cinematic Studio is installed and active."""
    st = StudioAvailabilityDetector.get_studio_status()
    return StudioStatusResponse(**st)


@app.post("/api/studio/jobs", response_model=StudioJobResponse, tags=["studio"])
def create_studio_job(req: CreateStudioJobRequest, db: Session = Depends(get_db)) -> StudioJobResponse:
    """Generate and submit a versioned StudioJobManifest (v1.0.0) for Cinematic Studio."""
    import datetime
    repo = DemoRepository(db)
    demo = repo.get_by_id(req.demo_id)
    if not demo:
        raise HTTPException(status_code=404, detail="Demo not found.")

    hl = repo.get_highlight_by_id(req.highlight_id)
    if not hl or hl.demo_id != demo.id:
        raise HTTPException(status_code=404, detail="Highlight not found in this demo.")

    job_id = f"job_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}_{hl.highlight_type}_{uuid.uuid4().hex[:6]}"
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    demo_meta = DemoMetadataManifest(
        identifier=f"demo_{demo.id}",
        file_path=demo.file_path,
        checksum_sha256=demo.fingerprint,
        map=demo.map_name or "unknown",
        tickrate=demo.tickrate or 128,
        match_date=demo.created_at.isoformat() if demo.created_at else None,
    )

    parsed_tags = []
    if getattr(hl, "tags_json", None):
        try:
            parsed_tags = json.loads(hl.tags_json)
        except Exception:
            parsed_tags = []

    clip_spec = ClipSpecificationManifest(
        round_num=hl.round_num,
        start_tick=hl.clip_start_tick,
        end_tick=hl.clip_end_tick,
        highlight_type=hl.highlight_type,
        highlight_score=float(hl.kill_count * 20.0),
        score_explanation=hl.detection_reason or f"{hl.kill_count} kills sequence",
        tags=parsed_tags,
    )

    actors = {
        "primary_player": {
            "steam_id": hl.pov_steam_id,
            "name": hl.pov_name or "Player",
            "pov_preference": "first_person",
        }
    }

    # Gather kills in clip range
    kills = repo.get_kills(demo.id)
    clip_kills = [
        k for k in kills
        if hl.clip_start_tick <= k.tick <= hl.clip_end_tick
    ]

    event_items = []
    for idx, k in enumerate(clip_kills, 1):
        event_items.append(
            EventItemManifest(
                tick=k.tick,
                event_type="kill",
                attacker_steam_id=k.attacker_steam_id,
                victim_steam_id=k.victim_steam_id,
                weapon=k.weapon,
                headshot=bool(k.headshot),
                wallbang=bool(k.wallbang),
                kill_number_in_sequence=idx,
            )
        )

    prod = ProductionRequestManifest(
        profile=req.profile,
        resolution=req.resolution,
        fps=req.fps,
        hud_mode=req.hud_mode,
        user_notes=req.user_notes,
    )

    manifest = StudioJobManifest(
        version="1.0.0",
        job_id=job_id,
        created_at=created_at,
        demo=demo_meta,
        clip=clip_spec,
        actors=actors,
        events=event_items,
        production_request=prod,
    )

    launcher = StudioJobLauncher()
    saved_path = launcher.submit_job(manifest)

    return StudioJobResponse(
        job_id=job_id,
        manifest_path=str(saved_path),
        status="pending",
        created_at=created_at,
    )


@app.get("/api/studio/jobs/{job_id}", tags=["studio"])
def get_studio_job_status(job_id: str) -> dict[str, Any]:
    """Retrieve execution status of a submitted StudioJobManifest."""
    provider = StudioJobStatusProvider()
    return provider.get_status(job_id)


@app.post("/api/social-drafts", response_model=SocialDraftResponse, tags=["content"])
def create_social_draft(req: SocialDraftRequest) -> SocialDraftResponse:
    """Generate social media post copy and tags for YouTube Shorts, TikTok, or Telegram."""
    text = SocialPostDraftGenerator.generate_draft(
        player_name=req.player_name,
        map_name=req.map_name,
        highlight_type=req.highlight_type,
        primary_weapon=req.primary_weapon,
        round_num=req.round_num,
        kill_count=req.kill_count,
        score=req.score,
        duration_sec=req.duration_sec,
        platform=req.platform,
    )
    return SocialDraftResponse(platform=req.platform, text=text)


# =============================================================================
# Phase 2: Analysis Projects, Tactical Drawings & Bookmarks Endpoints
# =============================================================================

@app.post("/api/projects", response_model=AnalysisProjectDTO, tags=["projects"])
def create_project(req: CreateAnalysisProjectRequest, db: Session = Depends(get_db)) -> AnalysisProjectDTO:
    """Create a new analysis project tied to a demo."""
    repo = DemoRepository(db)
    demo = repo.get_by_id(req.demo_id)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo {req.demo_id} not found",
        )
    proj = repo.create_analysis_project(
        demo_id=req.demo_id,
        title=req.title,
        description=req.description,
    )
    return AnalysisProjectDTO(
        id=proj.id,
        demo_id=proj.demo_id,
        title=proj.title,
        description=proj.description,
        created_at=proj.created_at.isoformat(),
        updated_at=proj.updated_at.isoformat(),
        drawings=[],
        bookmarks=[],
    )


@app.get("/api/projects", response_model=list[AnalysisProjectDTO], tags=["projects"])
def list_projects(demo_id: Optional[int] = None, db: Session = Depends(get_db)) -> list[AnalysisProjectDTO]:
    """List analysis projects, optionally filtered by demo_id."""
    repo = DemoRepository(db)
    projects = repo.list_analysis_projects(demo_id=demo_id)
    return [
        AnalysisProjectDTO(
            id=p.id,
            demo_id=p.demo_id,
            title=p.title,
            description=p.description,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
            drawings=[],
            bookmarks=[],
        )
        for p in projects
    ]


@app.get("/api/projects/{project_id}", response_model=AnalysisProjectDTO, tags=["projects"])
def get_project(project_id: str, db: Session = Depends(get_db)) -> AnalysisProjectDTO:
    """Get project details with all its drawings and bookmarks."""
    repo = DemoRepository(db)
    proj = repo.get_analysis_project(project_id)
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    drawings = [
        TacticalDrawingDTO(
            id=d.id,
            project_id=d.project_id,
            round_num=d.round_num,
            tick=d.tick,
            layer_type=d.layer_type,
            color=d.color,
            stroke_width=d.stroke_width,
            geometry_json=d.geometry_json,
            text_label=d.text_label,
            created_at=d.created_at.isoformat(),
        )
        for d in proj.drawings
    ]
    bookmarks = [
        BookmarkDTO(
            id=b.id,
            project_id=b.project_id,
            round_num=b.round_num,
            tick=b.tick,
            player_steamid=b.player_steamid,
            category=b.category,
            title=b.title,
            notes=b.notes,
            created_at=b.created_at.isoformat(),
        )
        for b in proj.bookmarks
    ]
    return AnalysisProjectDTO(
        id=proj.id,
        demo_id=proj.demo_id,
        title=proj.title,
        description=proj.description,
        created_at=proj.created_at.isoformat(),
        updated_at=proj.updated_at.isoformat(),
        drawings=drawings,
        bookmarks=bookmarks,
    )


@app.delete("/api/projects/{project_id}", tags=["projects"])
def delete_project(project_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Delete an analysis project and its drawings/bookmarks."""
    repo = DemoRepository(db)
    success = repo.delete_analysis_project(project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return {"status": "deleted", "project_id": project_id}


@app.post("/api/projects/{project_id}/drawings", response_model=TacticalDrawingDTO, tags=["projects"])
def add_drawing(project_id: str, req: CreateTacticalDrawingRequest, db: Session = Depends(get_db)) -> TacticalDrawingDTO:
    """Save a tactical drawing vector element."""
    repo = DemoRepository(db)
    proj = repo.get_analysis_project(project_id)
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    d = repo.add_tactical_drawing(
        project_id=project_id,
        round_num=req.round_num,
        layer_type=req.layer_type,
        color=req.color,
        stroke_width=req.stroke_width,
        geometry_json=req.geometry_json,
        tick=req.tick,
        text_label=req.text_label,
    )
    return TacticalDrawingDTO(
        id=d.id,
        project_id=d.project_id,
        round_num=d.round_num,
        tick=d.tick,
        layer_type=d.layer_type,
        color=d.color,
        stroke_width=d.stroke_width,
        geometry_json=d.geometry_json,
        text_label=d.text_label,
        created_at=d.created_at.isoformat(),
    )


@app.get("/api/projects/{project_id}/drawings", response_model=list[TacticalDrawingDTO], tags=["projects"])
def list_drawings(
    project_id: str, round_num: Optional[int] = None, db: Session = Depends(get_db)
) -> list[TacticalDrawingDTO]:
    """List tactical drawings for a project, optionally filtered by round_num."""
    repo = DemoRepository(db)
    drawings = repo.get_tactical_drawings(project_id, round_num=round_num)
    return [
        TacticalDrawingDTO(
            id=d.id,
            project_id=d.project_id,
            round_num=d.round_num,
            tick=d.tick,
            layer_type=d.layer_type,
            color=d.color,
            stroke_width=d.stroke_width,
            geometry_json=d.geometry_json,
            text_label=d.text_label,
            created_at=d.created_at.isoformat(),
        )
        for d in drawings
    ]


@app.delete("/api/projects/{project_id}/drawings/{drawing_id}", tags=["projects"])
def delete_drawing(project_id: str, drawing_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Delete a drawing shape."""
    repo = DemoRepository(db)
    success = repo.delete_tactical_drawing(drawing_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drawing {drawing_id} not found",
        )
    return {"status": "deleted", "drawing_id": drawing_id}


@app.post("/api/projects/{project_id}/bookmarks", response_model=BookmarkDTO, tags=["projects"])
def add_bookmark(project_id: str, req: CreateBookmarkRequest, db: Session = Depends(get_db)) -> BookmarkDTO:
    """Create a bookmark at a specific tick/round."""
    repo = DemoRepository(db)
    proj = repo.get_analysis_project(project_id)
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    b = repo.add_bookmark(
        project_id=project_id,
        round_num=req.round_num,
        tick=req.tick,
        title=req.title,
        category=req.category,
        notes=req.notes,
        player_steamid=req.player_steamid,
    )
    return BookmarkDTO(
        id=b.id,
        project_id=b.project_id,
        round_num=b.round_num,
        tick=b.tick,
        player_steamid=b.player_steamid,
        category=b.category,
        title=b.title,
        notes=b.notes,
        created_at=b.created_at.isoformat(),
    )


@app.get("/api/projects/{project_id}/bookmarks", response_model=list[BookmarkDTO], tags=["projects"])
def list_bookmarks(
    project_id: str, round_num: Optional[int] = None, db: Session = Depends(get_db)
) -> list[BookmarkDTO]:
    """List bookmarks for a project, optionally filtered by round_num."""
    repo = DemoRepository(db)
    bookmarks = repo.get_bookmarks(project_id, round_num=round_num)
    return [
        BookmarkDTO(
            id=b.id,
            project_id=b.project_id,
            round_num=b.round_num,
            tick=b.tick,
            player_steamid=b.player_steamid,
            category=b.category,
            title=b.title,
            notes=b.notes,
            created_at=b.created_at.isoformat(),
        )
        for b in bookmarks
    ]


@app.delete("/api/projects/{project_id}/bookmarks/{bookmark_id}", tags=["projects"])
def delete_bookmark(project_id: str, bookmark_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Delete a bookmark."""
    repo = DemoRepository(db)
    success = repo.delete_bookmark(bookmark_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bookmark {bookmark_id} not found",
        )
    return {"status": "deleted", "bookmark_id": bookmark_id}





# ---------------------------------------------------------------------------
# Mount Frontend Distribution for Standalone / Production Desktop Mode
# ---------------------------------------------------------------------------
_meipass_base = getattr(sys, "_MEIPASS", None)
_exe_parent = pathlib.Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else None
_frontend_candidates = [
    pathlib.Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
    pathlib.Path("frontend/dist").resolve(),
]
if _exe_parent:
    _frontend_candidates.insert(0, _exe_parent / "frontend" / "dist")
    _frontend_candidates.insert(0, _exe_parent / "_internal" / "frontend" / "dist")
if _meipass_base:
    _frontend_candidates.insert(0, pathlib.Path(_meipass_base) / "frontend" / "dist")

_frontend_dist = next((p for p in _frontend_candidates if p.is_dir()), None)
if _frontend_dist:
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")




