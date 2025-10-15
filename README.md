# File: `README.md`

````markdown
# kbju_bot

Телеграм-бот для учёта питания (КБЖУ). Aiogram 3 + SQLAlchemy async + Alembic. Есть вспомогательный FastAPI-сервис для вебхуков/админки.

## 1) Установка зависимостей

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
````

## 2) Настройки окружения

Скопируйте `.env.example` → `.env` и заполните значения.

Ключевые параметры:

* `BOT_TOKEN` — токен телеграм-бота
* `DATABASE_URL` — SQLite (dev) или PostgreSQL (prod)
* `ADMIN_DASHBOARD_TOKEN` — токен для админки и защиты вебхука
* (опц.) Edamam/FDC/Gemini/YooKassa — для расширенного функционала

Примеры `DATABASE_URL`:

* SQLite (по умолчанию в dev): `sqlite+aiosqlite:///./kbju.db`
* PostgreSQL: `postgresql+asyncpg://kbju_user:password@127.0.0.1:5432/kbju`

## 3) Инициализация БД

Схема управляется Alembic. Убедитесь, что `DATABASE_URL` корректен.

```bash
alembic upgrade head
```

> Alembic запускается в **SYNC-режиме** (psycopg) — это уже настроено в `migrations/env.py`.

## 4) Запуск бота

```bash
python main.py
```

Основные команды:

* `/start` — приветствие и главное меню
* `/summary` — сводка за сегодня
* `/diag` — диагностика окружения

## 5) Запуск вспомогательного API-сервера (вебхуки/админка)

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8080
```

### 5.1 Вебхук YooKassa

* Эндпоинт: `POST /payment/callback`
* Защита: требуется заголовок `X-Admin-Token: <ADMIN_DASHBOARD_TOKEN>`
* Логика по умолчанию: при `payment.succeeded` продление премиума на 30 дней; в БД пишется запись о платеже.

> Для продакшена добавьте верификацию подписи запроса YooKassa и обработку идемпотентности (сейчас базовая модель).

### 5.2 Admin Dashboard (минимальный)

* Метрики: `GET /admin/metrics`
* Последние премиум-активации: `GET /admin/trials`
* Доступ: тот же заголовок `X-Admin-Token`.

## 6) Заметки по архитектуре

* `core/models.py` — модели (в том числе `SourceEnum = manual|api|preset`)
* `core/crud.py` — CRUD (+ `set_premium_until`, `log_payment`)
* `bot/handlers/*` — хендлеры aiogram (Reply/Inline клавиатуры в `bot/keyboards/*`)
* `api/*` — клиенты внешних API (Edamam/FDC/Translate/YooKassa)
* `admin_dashboard/*` — простые HTML-эндпоинты для мониторинга

## 7) Профиль/Сводка/Премиум — UX

* Внутри разделов Reply-меню скрывается, везде есть кнопка «🏠 В главное меню»
* Ввод блюда: цепочка `Edamam → FDC → Presets → ручной ввод ккал`

## 8) Разработка и тестирование

* Рекомендуется SQLite в dev, PostgreSQL в prod
* Добавьте автотесты для `bot/utils/parser.py`, CRUD и цепочки поиска (моки)

## 9) Частые проблемы

* **Падает импорт констант** — проверьте `core/constants.py` (или используйте дефолт в хендлерах)
* **Миграции** — убедитесь, что выполнена последняя миграция `update source_enum`

---

© 2025 kbju_bot

```
```