"""SQLite engine singleton for TrajectoryLab."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return (and lazily create) the global engine, creating tables on first call."""
    global _engine
    if _engine is None:
        db_path = os.environ.get("TLAB_DB", str(Path.home() / ".tlab" / "tlab.db"))
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{db_path}", echo=False)
        # Import models so SQLModel.metadata knows all tables
        from tlab.storage import models as _  # noqa: F401
        SQLModel.metadata.create_all(_engine)
    return _engine


def reset_engine() -> None:
    """Set engine to None — used by tests to force a fresh DB per test."""
    global _engine
    _engine = None


def get_session() -> Generator[Session, None, None]:
    """FastAPI Depends-compatible session generator."""
    with Session(get_engine()) as session:
        yield session
