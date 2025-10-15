"""
Локальная инициализация PostgreSQL для проекта.
- Создаёт роль и БД, если их нет.
- Безопасно повторяется (idempotent).

Требования:
    pip install asyncpg
Запуск:
    python scripts/setup_postgres.py \
        --host 127.0.0.1 --port 5432 \
        --superuser postgres --superpass <PASSWORD> \
        --db kbju --appuser kbju_user --apppass <PASSWORD>
После запуска обновите DATABASE_URL в .env:
    DATABASE_URL=postgresql+asyncpg://kbju_user:<PASSWORD>@127.0.0.1:5432/kbju
"""
from __future__ import annotations
import argparse
import asyncio
import asyncpg


async def ensure_role_and_db(
    host: str,
    port: int,
    superuser: str,
    superpass: str,
    db: str,
    appuser: str,
    apppass: str,
):
    conn = await asyncpg.connect(host=host, port=port, user=superuser, password=superpass, database="postgres")
    try:
        # user
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_roles WHERE rolname = $1", appuser
        )
        if not exists:
            await conn.execute(f"CREATE ROLE {appuser} WITH LOGIN PASSWORD $1", apppass)
        else:
            # обновим пароль на случай, если поменяли
            await conn.execute(f"ALTER ROLE {appuser} WITH PASSWORD $1", apppass)

        # db
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db
        )
        if not exists:
            await conn.execute(f"CREATE DATABASE {db} OWNER {appuser}")
        # права на существующей БД
        await conn.execute(
            f"GRANT ALL PRIVILEGES ON DATABASE {db} TO {appuser}"
        )
    finally:
        await conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5432)
    ap.add_argument("--superuser", default="postgres")
    ap.add_argument("--superpass", required=True)
    ap.add_argument("--db", default="kbju")
    ap.add_argument("--appuser", default="kbju_user")
    ap.add_argument("--apppass", required=True)
    args = ap.parse_args()

    asyncio.run(
        ensure_role_and_db(
            host=args.host,
            port=args.port,
            superuser=args.superuser,
            superpass=args.superpass,
            db=args.db,
            appuser=args.appuser,
            apppass=args.apppass,
        )
    )


if __name__ == "__main__":
    main()