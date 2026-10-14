"""Database engine and session management for SQLite.

Enforces WAL journal mode and foreign key constraints on SQLite connections.
"""

from __future__ import annotations

import pathlib
from typing import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.storage.models import Base

DEFAULT_DB_FILE = pathlib.Path("demtoshka.db")


def create_db_engine(db_url: str | None = None) -> Engine:
    """Create a configured SQLAlchemy engine for SQLite.

    If db_url is None, defaults to sqlite:///demtoshka.db in current working directory.
    """
    if db_url is None:
        db_url = f"sqlite:///{DEFAULT_DB_FILE.resolve()}"

    # For SQLite, enforce foreign keys and WAL mode
    engine = create_engine(db_url, echo=False)

    if db_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            # WAL mode is not allowed for in-memory databases
            if ":memory:" not in db_url:
                cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


def init_db(engine: Engine) -> None:
    """Create all tables defined in Base metadata if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a sessionmaker configured for the given engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)

