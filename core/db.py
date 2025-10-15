# File: core/db.py
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings

# --- Engine ---
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    future=True,
    echo=False,
    pool_pre_ping=True,
)

# --- Session factory ---
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)

# Backward compatibility alias (старый код импортировал SessionLocal)
SessionLocal = async_session_maker


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Async session context manager (BEGIN ... COMMIT/ROLLBACK)."""
    session: AsyncSession = async_session_maker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


__all__ = [
    "engine",
    "async_session_maker",
    "SessionLocal",
    "session_scope",
]
# --- Declarative Base (for models) ---
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


__all__ = [
    "engine",
    "async_session_maker",
    "SessionLocal",
    "session_scope",
    "Base",
]

