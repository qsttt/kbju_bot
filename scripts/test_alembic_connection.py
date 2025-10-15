# File: scripts/test_alembic_connection.py
"""
Проверка подключения к БД через SYNC SQLAlchemy (psycopg),
совпадающего с тем, что использует Alembic в migrations/env.py.

Запуск:
    python scripts/test_alembic_connection.py
"""
from __future__ import annotations
from sqlalchemy import create_engine, text
from core.config import settings

SYNC_DB_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")

def main():
    engine = create_engine(SYNC_DB_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        v = conn.execute(text("select version()"))
        print("✅ Connected via SQLAlchemy sync:", v.scalar())

if __name__ == "__main__":
    main()