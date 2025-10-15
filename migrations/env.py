# File: migrations/env.py
from __future__ import annotations
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context

# ---- add project root to sys.path ----
import os, sys
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
# --------------------------------------
from core.models import Base
from core.config import settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Helper: build sync URL for Alembic even if app uses asyncpg
# e.g. postgresql+asyncpg://... -> postgresql+psycopg://...
def make_sync_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url

# We prefer running migrations with a SYNC engine on Windows to avoid asyncio/IO quirks
SYNC_DB_URL = make_sync_url(settings.database_url)

from sqlalchemy import create_engine


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=SYNC_DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True if SYNC_DB_URL.startswith("sqlite") else False,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a SYNC engine (psycopg on Postgres)."""
    connectable = create_engine(
        SYNC_DB_URL,
        poolclass=pool.NullPool,
        pool_pre_ping=True,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()