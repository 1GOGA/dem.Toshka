"""
tests/unit/test_strategy_exporter.py — Unit tests for Phase 5 Strategy Book & Standalone HTML Exporter.
"""

from __future__ import annotations

import json
from backend.services.strategy_exporter import export_strategy_book_to_html
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.repository import DemoRepository
from backend.api.schemas import CreateStrategyBookRequest, CreateTacticalSetupRequest
from backend.api.main import (
    create_strategy_book,
    get_strategy_book,
    add_tactical_setup,
    export_strategy_book_html,
)


def test_strategy_book_and_setup_crud():
    """Verify strategy book and tactical setup database creation and retrieval."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()
    repo = DemoRepository(session)

    try:
        book = repo.create_strategy_book(
            title="Mirage A Default Protocols",
            map_name="de_mirage",
            team_name="demToshka Squad",
            description="Official tactical protocols for Mirage A site takes.",
        )
        assert book.id is not None
        assert book.title == "Mirage A Default Protocols"

        tokens = [
            {"x": 450, "y": 700, "side": "t", "role": "Entry", "callout": "Ramp", "yaw": 45},
            {"x": 380, "y": 750, "side": "t", "role": "Support", "callout": "T-Roof", "yaw": 60},
        ]
        drawings = [
            {"layer_type": "arrow", "color": "#00f2fe", "geometry_json": json.dumps({"x1": 450, "y1": 700, "x2": 680, "y2": 320})},
        ]
        setup = repo.add_tactical_setup(
            strategy_book_id=book.id,
            title="Fast A Ramp Execute",
            side="t",
            phase="execute",
            description="2 smokes (CT & Jungle), 2 flashes over ramp, fast 3-man entry.",
            tokens_json=json.dumps(tokens),
            drawings_json=json.dumps(drawings),
        )
        assert setup.id is not None
        assert setup.phase == "execute"

        # Fetch book with setups
        fetched = repo.get_strategy_book(book.id)
        assert fetched is not None
        assert len(fetched.setups) == 1
        assert fetched.setups[0].title == "Fast A Ramp Execute"
    finally:
        session.close()


def test_utility_lineups_crud():
    """Verify grenade lineups repository methods."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()
    repo = DemoRepository(session)

    try:
        lineup = repo.add_utility_lineup(
            map_name="de_mirage",
            side="t",
            utility_type="smoke",
            title="Window Smoke from T-Spawn (Trash Can)",
            pos_x=320.0,
            pos_y=880.0,
            target_x=510.0,
            target_y=450.0,
            throw_type="jump",
            crosshair_desc="Aim at top corner of antenna, press D + jumpthrow.",
        )
        assert lineup.id is not None

        lineups = repo.get_utility_lineups(map_name="de_mirage", utility_type="smoke")
        assert len(lineups) == 1
        assert lineups[0].title == "Window Smoke from T-Spawn (Trash Can)"
    finally:
        session.close()


def test_standalone_offline_html_exporter():
    """Verify single-file offline HTML generation containing embedded CSS, SVG radars, and 11 chapters."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()
    repo = DemoRepository(session)

    try:
        book = repo.create_strategy_book(
            title="Anubis B Split Playbook",
            map_name="de_anubis",
            team_name="CyberToshka",
            description="B split and canal control setups.",
        )
        tokens = [
            {"x": 250, "y": 300, "side": "ct", "role": "Anchor", "callout": "Site B", "yaw": 180},
        ]
        repo.add_tactical_setup(
            strategy_book_id=book.id,
            title="Default B Hold",
            side="ct",
            phase="default",
            tokens_json=json.dumps(tokens),
        )

        fetched = repo.get_strategy_book(book.id)
        html_out = export_strategy_book_to_html(fetched)

        # Integrity checks
        assert "<!DOCTYPE html>" in html_out
        assert "<html lang=\"ru\">" in html_out
        assert "Anubis B Split Playbook" in html_out
        assert "<style>" in html_out
        assert "@media print" in html_out  # print stylesheet for PDF
        assert "<svg viewBox=\"0 0 1000 1000\"" in html_out  # inline SVG radar
        assert "window.print()" in html_out  # print button script
        assert "11 Протоколов команды" in html_out
        # Zero external CDN script/link tags
        assert "https://" not in html_out
        assert "http://" not in html_out
    finally:
        session.close()


def test_strategy_api_endpoints():
    """Verify FastAPI Strategy Book REST endpoints."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    try:
        # 1. Create Book
        req = CreateStrategyBookRequest(
            title="Inferno Banana Protocol",
            map_name="de_inferno",
            team_name="Infernal Beasts",
        )
        dto = create_strategy_book(req=req, db=session)
        assert dto.id is not None
        assert dto.map_name == "de_inferno"

        # 2. Add Setup
        setup_req = CreateTacticalSetupRequest(
            title="Car Deep Banana Molotov",
            side="ct",
            phase="default",
        )
        s_dto = add_tactical_setup(book_id=dto.id, req=setup_req, db=session)
        assert s_dto.title == "Car Deep Banana Molotov"

        # 3. Get Book Details
        book_dto = get_strategy_book(book_id=dto.id, db=session)
        assert len(book_dto.setups) == 1

        # 4. Export HTML
        res = export_strategy_book_html(book_id=dto.id, db=session)
        assert res.media_type.startswith("text/html")
        assert "Inferno Banana Protocol" in res.body.decode("utf-8")
    finally:
        session.close()
