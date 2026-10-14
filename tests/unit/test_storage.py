"""Unit tests for SQLite storage layer (Stage E).

Uses in-memory SQLite database (`sqlite:///:memory:`) to verify
tables, CRUD operations, transactions, and cache invalidation.
"""

from __future__ import annotations

import json
import pytest

from backend.detector.models import HighlightCandidate, HighlightType
from backend.parser.models import KillEvent, ParsedDemo, PlayerInfo, RoundInfo, SCHEMA_VERSION
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.models import DemoModel, HighlightModel
from backend.storage.repository import DemoRepository


@pytest.fixture
def session():
    """Provides an isolated in-memory SQLite database session."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    with session_factory() as sess:
        yield sess


def make_test_demo() -> tuple[ParsedDemo, list[HighlightCandidate]]:
    player_1 = PlayerInfo(name="Alice", steam_id="76561198000000001", team="ct")
    player_2 = PlayerInfo(name="Bob", steam_id="76561198000000002", team="t")

    round_1 = RoundInfo(
        round_num=1,
        start_tick=1000,
        freeze_end_tick=1200,
        end_tick=5000,
        official_end_tick=5200,
        winner="ct",
        reason="ct_killed",
        bomb_plant_tick=None,
        bomb_site=None,
    )

    kill_1 = KillEvent(
        tick=2500,
        round_num=1,
        attacker_name="Alice",
        attacker_steam_id="76561198000000001",
        attacker_team="ct",
        victim_name="Bob",
        victim_steam_id="76561198000000002",
        victim_team="t",
        weapon="m4a1_silencer",
        headshot=True,
        hitgroup="head",
        noscope=False,
        thru_smoke=False,
        attacker_blind=False,
        wallbang=False,
        assister_name=None,
        assister_steam_id=None,
    )

    demo = ParsedDemo(
        schema_version=SCHEMA_VERSION,
        demo_path="match.dem",
        map_name="de_dust2",
        tickrate=128,
        rounds=[round_1],
        players=[player_1, player_2],
        kills=[kill_1],
    )

    highlight = HighlightCandidate(
        id="1_kill_76561198000000001_2500",
        highlight_type=HighlightType.KILL,
        round_num=1,
        pov_steam_id="76561198000000001",
        pov_name="Alice",
        kill_start_tick=2500,
        kill_end_tick=2500,
        clip_start_tick=2000,
        clip_end_tick=3000,
        kill_count=1,
        tags=["headshot"],
        is_heuristic=False,
        detection_reason="Single headshot kill",
    )

    return demo, [highlight]


class TestStorageBasics:
    def test_save_and_retrieve_demo(self, session):
        repo = DemoRepository(session)
        demo, highlights = make_test_demo()
        fp = "fingerprint_12345"

        saved = repo.save_demo(demo, fingerprint=fp, highlights=highlights)
        assert saved.id is not None
        assert saved.fingerprint == fp
        assert saved.map_name == "de_dust2"
        assert saved.tickrate == 128
        assert saved.duration_seconds is not None
        assert saved.duration_seconds > 0

        # Retrieve by fingerprint
        loaded = repo.get_by_fingerprint(fp)
        assert loaded is not None
        assert loaded.id == saved.id
        assert len(loaded.players) == 2
        assert len(loaded.rounds) == 1
        assert len(loaded.highlights) == 1

    def test_cache_miss_on_schema_version_mismatch(self, session):
        repo = DemoRepository(session)
        demo, highlights = make_test_demo()
        fp = "fingerprint_v1"

        repo.save_demo(demo, fingerprint=fp, highlights=highlights)

        # Matching version returns record
        assert repo.get_by_fingerprint(fp, schema_version=SCHEMA_VERSION) is not None

        # Different version returns None (cache miss, requires re-parse)
        assert repo.get_by_fingerprint(fp, schema_version="999.0") is None

    def test_overwrite_demo_with_same_fingerprint(self, session):
        repo = DemoRepository(session)
        demo, highlights = make_test_demo()
        fp = "fingerprint_dup"

        saved1 = repo.save_demo(demo, fingerprint=fp, highlights=highlights)
        id1 = saved1.id

        # Update map name and save again with same fingerprint
        demo.map_name = "de_inferno"
        saved2 = repo.save_demo(demo, fingerprint=fp, highlights=highlights)
        id2 = saved2.id

        # Record should be replaced cleanly
        demos = repo.list_demos()
        assert len(demos) == 1
        assert demos[0].map_name == "de_inferno"

    def test_get_highlights_filtered(self, session):
        repo = DemoRepository(session)
        demo, highlights = make_test_demo()
        fp = "fingerprint_hl"

        saved = repo.save_demo(demo, fingerprint=fp, highlights=highlights)

        # Filter by POV
        hl_alice = repo.get_highlights(saved.id, pov_steam_id="76561198000000001")
        assert len(hl_alice) == 1
        assert hl_alice[0].pov_name == "Alice"

        # Filter by nonexistent POV
        hl_none = repo.get_highlights(saved.id, pov_steam_id="nonexistent")
        assert len(hl_none) == 0

        # Filter by type
        hl_kill = repo.get_highlights(saved.id, highlight_type="kill")
        assert len(hl_kill) == 1

        hl_ace = repo.get_highlights(saved.id, highlight_type="ace")
        assert len(hl_ace) == 0

    def test_tags_json_serialization(self, session):
        repo = DemoRepository(session)
        demo, highlights = make_test_demo()
        saved = repo.save_demo(demo, fingerprint="fp_tags", highlights=highlights)

        h_list = repo.get_highlights(saved.id)
        assert len(h_list) == 1
        tags = json.loads(h_list[0].tags_json)
        assert tags == ["headshot"]

    def test_get_kills_and_rounds(self, session):
        repo = DemoRepository(session)
        demo, highlights = make_test_demo()
        saved = repo.save_demo(demo, fingerprint="fp_queries", highlights=highlights)

        kills = repo.get_kills(saved.id)
        assert len(kills) == 1
        assert kills[0].weapon == "m4a1_silencer"
        assert kills[0].headshot is True

        rounds = repo.get_rounds(saved.id)
        assert len(rounds) == 1
        assert rounds[0].round_num == 1
        assert rounds[0].winner == "ct"

