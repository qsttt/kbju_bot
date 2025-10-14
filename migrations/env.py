from __future__ import annotations
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# ---- add project root to sys.path ----
import os, sys
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
# --------------------------------------
from core.models import Base
from core.config import settings

# наши модели
from core.models import Base
from core.config import settings

# Alembic Config объект
config = context.config

# Дадим Alembic видеть .ini-логгинг
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные целей для autogenerate
target_metadata = Base.metadata

# Для SQLite включим render_as_batch, чтобы ALTER-операции проходили
def include_object(object, name, type_, reflected, compare_to):
    return True


def run_migrations_offline() -> None:
    """Запуск оффлайн-миграций."""
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=url.startswith("sqlite"),
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=settings.database_url.startswith("sqlite"),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск онлайн-миграций (async)."""
    config_section = config.get_section(config.config_ini_section)
    connectable = async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=settings.database_url,  # берём URL из .env
    )

    async def run() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(run())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()