# kbju_bot — локальный запуск с PostgreSQL

## 1) Удалить старые локальные БД SQLite (чтобы не мешали)
Удалите файлы в корне проекта, если существуют:
- `db.sqlite3`
- `kbju.db`

*(Опционально)* проверьте `DATABASE_URL` в `.env` указывает на Postgres, а не на файл SQLite.

## 2) Установить зависимости
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## 3) Установить PostgreSQL и создать БД
- Поставьте PostgreSQL (Windows: "Install PostgreSQL"; macOS: brew; Linux: apt/yum).
- Убедитесь, что сервер запущен и доступен на `127.0.0.1:5432`.

Создание роли и БД:
```bash
python scripts/setup_postgres.py \
  --host 127.0.0.1 --port 5432 \
  --superuser postgres --superpass <SUPERPASS> \
  --db kbju --appuser kbju_user --apppass <APPUSERPASS>
```

## 4) Настроить `.env`
В `.env` пропишите:
```
DATABASE_URL=postgresql+asyncpg://kbju_user:<APPUSERPASS>@127.0.0.1:5432/kbju
BOT_TOKEN=<your_token>
EDAMAM_APP_ID=<id>
EDAMAM_APP_KEY=<key>
FDC_API_KEY=<key>
USE_RU_EN_DICTIONARY=true
```

## 5) Миграции и сидинг
```bash
alembic upgrade head
python -m scripts.seed_db
```

## 6) Запуск бота
```bash
python main.py
```

## Примечания
- Проект использует async SQLAlchemy и драйвер `asyncpg`.
- Alembic берёт URL БД из `core.config.Settings.database_url` (см. `migrations/env.py`).
- Если позже будете переносить на VPS, достаточно поставить PostgreSQL и перенести `.env` (+ выполнить миграции/сидинг).