from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Dict, Any

from sqlalchemy import select, func

from core.models import User, Entry

# ----------------------------- helpers -----------------------------

_ALLOWED_SOURCES = {"manual", "api"}


def _normalize_source(value: Optional[str]) -> str:
    v = (value or "").strip().lower()
    # БД не знает про 'preset' и прочие — приводим к 'api'
    if v not in _ALLOWED_SOURCES:
        return "api"
    return v


# ----------------------------- CRUD -----------------------------

async def get_or_create_user(session, tg_id: int) -> User:
    """Вернуть пользователя по tg_id, при отсутствии — создать.
    Минимальная инициализация, остальные поля nullable.
    """
    res = await session.execute(select(User).where(User.tg_id == tg_id))
    user = res.scalar_one_or_none()
    if user:
        return user

    user = User(tg_id=tg_id, created_at=datetime.utcnow())  # type: ignore[arg-type]
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def add_entry(
    session,
    user_id: int,
    *,
    on_date: date,
    title: str,
    amount_value: Optional[float],
    amount_unit: Optional[str],
    amount_grams: Optional[float],
    kcal: Optional[float],
    p: Optional[float],
    f: Optional[float],
    c: Optional[float],
    is_calories_only: bool,
    source: Optional[str] = None,
) -> Entry:
    """Создать запись дневника.
    Нормализуем source под enum ('manual' | 'api').
    Коммитим внутри, как ожидает вызывающая сторона.
    """
    entry = Entry(
        user_id=user_id,
        date=on_date,
        title=title,
        amount_value=amount_value,
        amount_unit=amount_unit,
        amount_grams=amount_grams,
        kcal=kcal,
        protein=p,
        fat=f,
        carbs=c,
        is_calories_only=is_calories_only,
        source=_normalize_source(source),
        created_at=datetime.utcnow(),
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def get_daily_summary(session, user_id: int, on_date: date) -> Dict[str, Any]:
    """Вернуть сумму КБЖУ за день. Пустые -> 0."""
    res = await session.execute(
        select(
            func.coalesce(func.sum(Entry.kcal), 0),
            func.coalesce(func.sum(Entry.protein), 0),
            func.coalesce(func.sum(Entry.fat), 0),
            func.coalesce(func.sum(Entry.carbs), 0),
        ).where((Entry.user_id == user_id) & (Entry.date == on_date))
    )
    kcal, p, f, c = res.one()
    return {"kcal": float(kcal or 0), "p": float(p or 0), "f": float(f or 0), "c": float(c or 0)}