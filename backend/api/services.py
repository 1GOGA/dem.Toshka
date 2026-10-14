"""Service layer orchestrating Ingestion, Parsing, Highlight Detection, Storage and Analytics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from backend.analytics.match_stats import compute_match_stats
from backend.analytics.player_analytics import compute_player_analytics
from backend.api.schemas import (
    DemoSummary,
    HighlightDTO,
    MatchScoreboardDTO,
    PlayerAnalyticsDTO,
    PlayerDTO,
    PlayerErrorDTO,
    PlayerStatsDTO,
    RoundDTO,
)
from backend.detector.highlight_detector import detect_highlights
from backend.parser.adapter import parse_demo
from backend.parser.ingestion import fingerprint, validate_demo_path
from backend.parser.models import SCHEMA_VERSION
from backend.storage.models import DemoModel
from backend.storage.repository import DemoRepository


class DemoService:
    @staticmethod
    def parse_or_get_demo(demo_path_str: str, repo: DemoRepository) -> DemoModel:
        """Validate, fingerprint, check cache, and parse/detect/save if not cached."""
        path = Path(demo_path_str)
        validate_demo_path(path)
        demo_fp = fingerprint(path)

        # Check existing cache
        cached = repo.get_by_fingerprint(demo_fp, schema_version=SCHEMA_VERSION)
        if cached is not None:
            return cached

        # Cache miss or stale version: parse fresh
        parsed = parse_demo(path)
        highlights = detect_highlights(parsed)
        saved = repo.save_demo(parsed, fingerprint=demo_fp, highlights=highlights)
        return saved

    @staticmethod
    def to_summary(demo: DemoModel) -> DemoSummary:
        return DemoSummary(
            id=demo.id,
            file_path=demo.file_path,
            fingerprint=demo.fingerprint,
            map_name=demo.map_name,
            tickrate=demo.tickrate,
            duration_seconds=demo.duration_seconds,
            schema_version=demo.schema_version,
            created_at=demo.created_at,
            rounds_count=len(demo.rounds) if demo.rounds else 0,
            players_count=len(demo.players) if demo.players else 0,
            highlights_count=len(demo.highlights) if demo.highlights else 0,
        )

    @staticmethod
    def get_highlights(
        demo_id: int,
        repo: DemoRepository,
        pov_steam_id: Optional[str] = None,
        highlight_type: Optional[str] = None,
        round_num: Optional[int] = None,
    ) -> list[HighlightDTO]:
        models = repo.get_highlights(demo_id, pov_steam_id=pov_steam_id, highlight_type=highlight_type)
        if round_num is not None:
            models = [m for m in models if m.round_num == round_num]

        coords_map = {}
        demo = repo.get_by_id(demo_id)
        if demo and demo.file_path:
            import pathlib
            from backend.parser.replay import get_highlights_radar_coords

            coords_map = get_highlights_radar_coords(
                pathlib.Path(demo.file_path),
                models,
                demo.map_name or "de_nuke",
            )

        dtos: list[HighlightDTO] = []
        for m in models:
            tags = []
            try:
                tags = json.loads(m.tags_json)
            except Exception:
                pass

            h_coords = coords_map.get(m.id, {})

            dtos.append(
                HighlightDTO(
                    id=m.id,
                    demo_id=m.demo_id,
                    highlight_type=m.highlight_type,
                    round_num=m.round_num,
                    pov_steam_id=m.pov_steam_id,
                    pov_name=m.pov_name,
                    kill_start_tick=m.kill_start_tick,
                    kill_end_tick=m.kill_end_tick,
                    clip_start_tick=m.clip_start_tick,
                    clip_end_tick=m.clip_end_tick,
                    kill_count=m.kill_count,
                    tags=tags,
                    is_heuristic=m.is_heuristic,
                    detection_reason=m.detection_reason,
                    radar_x=h_coords.get("radar_x"),
                    radar_y=h_coords.get("radar_y"),
                    victim_radar_x=h_coords.get("victim_radar_x"),
                    victim_radar_y=h_coords.get("victim_radar_y"),
                    radar_level=h_coords.get("radar_level", "upper"),
                )
            )
        return dtos

    @staticmethod
    def get_scoreboard(demo_id: int, repo: DemoRepository) -> Optional[MatchScoreboardDTO]:
        demo = repo.get_by_id(demo_id)
        if demo is None:
            return None

        players = repo.get_players(demo_id)
        rounds = repo.get_rounds(demo_id)
        kills = repo.get_kills(demo_id)

        stats = compute_match_stats(players=players, rounds=rounds, kills=kills)

        player_dtos = [
            PlayerStatsDTO(
                name=p.name,
                steam_id=p.steam_id,
                team=p.team,
                kills=p.kills,
                deaths=p.deaths,
                assists=p.assists,
                suicides=p.suicides,
                teamkills=p.teamkills,
                headshots=p.headshots,
                headshot_pct=p.headshot_pct,
                kd_ratio=p.kd_ratio,
                kpr=getattr(p, "kpr", 0.0),
                dpr=getattr(p, "dpr", 0.0),
                differential=getattr(p, "differential", 0),
                performance_rating=getattr(p, "performance_rating", 1.0),
                faceit_level=getattr(p, "faceit_level", 5),
                kast_pct=getattr(p, "kast_pct", 0.0),
                opening_kills=getattr(p, "opening_kills", 0),
                opening_deaths=getattr(p, "opening_deaths", 0),
                multikills=getattr(p, "multikills", {}),
                clutches_won=getattr(p, "clutches_won", 0),
                adr=p.adr,
                weapon_kills=p.weapon_kills,
                kills_by_round=p.kills_by_round,
            )
            for p in stats.players
        ]

        return MatchScoreboardDTO(
            total_rounds=stats.total_rounds,
            score=stats.score,
            players=player_dtos,
            weapon_summary=stats.weapon_summary,
        )

    @staticmethod
    def get_player_analytics(
        demo_id: int,
        player_identifier: str,
        repo: DemoRepository,
    ) -> Optional[PlayerAnalyticsDTO]:
        demo = repo.get_by_id(demo_id)
        if demo is None:
            return None

        players = repo.get_players(demo_id)
        rounds = repo.get_rounds(demo_id)
        kills = repo.get_kills(demo_id)

        analytics = compute_player_analytics(
            target_steam_id_or_name=player_identifier,
            players=players,
            rounds=rounds,
            kills=kills,
            tickrate=demo.tickrate or 64,
        )
        if analytics is None:
            return None

        error_dtos = [
            PlayerErrorDTO(
                round_num=e.round_num,
                tick=e.tick,
                error_type=e.error_type,
                title=e.title,
                description=e.description,
                severity=e.severity,
            )
            for e in analytics.errors
        ]

        return PlayerAnalyticsDTO(
            name=analytics.name,
            steam_id=analytics.steam_id,
            team=analytics.team,
            total_rounds=analytics.total_rounds,
            performance_rating=analytics.performance_rating,
            kills=analytics.kills,
            deaths=analytics.deaths,
            assists=analytics.assists,
            kd_ratio=analytics.kd_ratio,
            kpr=analytics.kpr,
            dpr=analytics.dpr,
            headshot_pct=analytics.headshot_pct,
            kast_pct=analytics.kast_pct,
            swing_winrate_pct=analytics.swing_winrate_pct,
            crosshair_placement_score=analytics.crosshair_placement_score,
            first_bullet_accuracy_pct=analytics.first_bullet_accuracy_pct,
            spray_control_pct=analytics.spray_control_pct,
            opening_duels_won=analytics.opening_duels_won,
            opening_duels_lost=analytics.opening_duels_lost,
            opening_winrate_pct=analytics.opening_winrate_pct,
            trade_kills=analytics.trade_kills,
            trade_kill_pct=analytics.trade_kill_pct,
            traded_deaths=analytics.traded_deaths,
            traded_death_pct=analytics.traded_death_pct,
            clutches_won=analytics.clutches_won,
            clutches_attempted=analytics.clutches_attempted,
            clutch_winrate_pct=analytics.clutch_winrate_pct,
            multikill_rounds=analytics.multikill_rounds,
            errors=error_dtos,
            strengths=analytics.strengths,
            advice=analytics.advice,
        )


