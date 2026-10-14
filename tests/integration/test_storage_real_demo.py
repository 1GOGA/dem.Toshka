"""Integration tests — SQLite Storage & Analytics on real CS2 demo (de_nuke).

Requires tests/integration/fixtures/test.dem to be present.
Run with:
    .venv\\Scripts\\pytest tests/integration/test_storage_real_demo.py -v -s
"""

from __future__ import annotations

import pathlib
import pytest

from backend.analytics.match_stats import compute_match_stats
from backend.detector.highlight_detector import detect_highlights
from backend.parser.adapter import parse_demo
from backend.parser.ingestion import fingerprint
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.repository import DemoRepository


FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "test.dem"


def skip_if_no_fixture():
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Fixture demo not found: {FIXTURE_PATH}")


@pytest.fixture(scope="module")
def parsed_demo():
    skip_if_no_fixture()
    return parse_demo(FIXTURE_PATH)


@pytest.fixture(scope="module")
def detected_highlights(parsed_demo):
    return detect_highlights(parsed_demo)


@pytest.fixture(scope="module")
def demo_fingerprint():
    skip_if_no_fixture()
    return fingerprint(FIXTURE_PATH)


@pytest.fixture(scope="module")
def db_session():
    """Provides an isolated in-memory SQLite database for integration test."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    with session_factory() as sess:
        yield sess


class TestStorageRealDemo:
    def test_save_and_reload_full_demo(
        self, db_session, parsed_demo, detected_highlights, demo_fingerprint
    ):
        repo = DemoRepository(db_session)

        # 1. Save demo + highlights
        saved = repo.save_demo(
            parsed_demo,
            fingerprint=demo_fingerprint,
            highlights=detected_highlights,
        )

        assert saved.id is not None
        assert saved.fingerprint == demo_fingerprint
        assert saved.map_name == "de_nuke"
        assert saved.tickrate == 128
        assert saved.duration_seconds is not None
        assert saved.duration_seconds > 0

        # 2. Cache retrieval by fingerprint
        loaded = repo.get_by_fingerprint(demo_fingerprint)
        assert loaded is not None
        assert loaded.id == saved.id
        assert len(loaded.rounds) == 21
        assert len(loaded.players) == 10
        assert len(loaded.highlights) == 133

        # 3. Verify kill events
        kills = repo.get_kills(saved.id)
        assert len(kills) == 160

    def test_compute_analytics_from_db(
        self, db_session, demo_fingerprint
    ):
        repo = DemoRepository(db_session)
        loaded = repo.get_by_fingerprint(demo_fingerprint)
        assert loaded is not None

        kills = repo.get_kills(loaded.id)
        players = repo.get_players(loaded.id)
        rounds = repo.get_rounds(loaded.id)

        # Compute match statistics directly from database records
        stats = compute_match_stats(players=players, rounds=rounds, kills=kills)

        assert stats.total_rounds == 21
        assert len(stats.players) == 10
        assert sum(stats.score.values()) == 21

        # Print scoreboard
        print(f"\n=== MATCH SCOREBOARD ({loaded.map_name}) ===")
        print(f"Final Score: CT {stats.score.get('ct', 0)} : {stats.score.get('t', 0)} T")
        print(f"{'Player':<20} | {'Team':<4} | {'K':<3} | {'D':<3} | {'A':<3} | {'K/D':<5} | {'HS%':<6}")
        print("-" * 60)
        for p in stats.players:
            print(
                f"{p.name:<20} | {p.team or '-':<4} | {p.kills:<3} | {p.deaths:<3} | "
                f"{p.assists:<3} | {p.kd_ratio:<5.2f} | {p.headshot_pct:<5.1f}%"
            )

        # Basic integrity
        top_player = stats.players[0]
        assert top_player.kills >= 15  # In a 21-round game, top fragger has >= 15 kills
        assert top_player.kd_ratio > 0

        # Weapon summary should contain common weapons
        assert "ak47" in stats.weapon_summary or "m4a1" in stats.weapon_summary or "m4a1_silencer" in stats.weapon_summary

