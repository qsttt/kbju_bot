from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import User, Entry, Payment

# ----------------------------- helpers -----------------------------

# В текущей схеме enum: {"manual", "db", "api", "custom"}.
# До миграции (P0 шаг отдельный) безопасно маппим "preset" -> "manual",
# чтобы не падать на несовпадении enum.
_ALLOWED_SOURCES = {"manual", "api"}


def _normalize_source(value: Optional[str]) -> str:
    v = (value or "").strip().lower()
    if v in _ALLOWED_SOURCES:
        return v
    if v == "preset":
        # TODO: после обновления enum до {manual, api, preset} вернуть preset как есть
        return "manual"
    # дефолт — считаем ручным вводом
    return "manual"

# ----------------------------- users -----------------------------

async def get_or_create_user(session: AsyncSession, tg_id: int) -> User:
    """Вернуть пользователя по tg_id, при отсутствии — создать.
    Минимальная инициализация, остальные поля nullable.
    """
    res = await session.execute(select(User).where(User.tg_id == tg_id))
    user = res.scalar_one_or_none()
    if user:
        return user

    user = User(tg_id=tg_id, created_at=datetime.utcnow())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# ----------------------------- entries -----------------------------

async def add_entry(
    session: AsyncSession,
    user_id: int,
    *,
    on_date: date,
    title: str,
    amount_value: float | None,
    amount_unit: str | None,
    amount_grams: float | None,
    kcal: float | None,
    p: float | None,
    f: float | None,
    c: float | None,
    is_calories_only: bool,
    source: Optional[str] = None,
) -> Entry:
    """Создать запись дневника.
    Нормализуем source под допустимые значения.
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


async def get_daily_summary(session: AsyncSession, user_id: int, on_date: date) -> Dict[str, Any]:
    """Вернуть сумму КБЖУ за день. Пустые -> 0.
    Возвращаем float, совместимый с форматтерами.
    """
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


# ----------------------------- payments / premium -----------------------------

async def set_premium_until(session: AsyncSession, user_id: int, until: datetime) -> None:
    """Установить/продлить premium_until пользователю и зафиксировать в БД.
    Не создаёт пользователя — предполагается существующий user_id.
    """
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise ValueError(f"User id={user_id} not found")

    user.premium_until = until
    await session.commit()


async def log_payment(
    session: AsyncSession,
    user_id: int,
    provider: str,
    amount: float,
    currency: str,
    status: str,
    payment_id: str,
) -> Payment:
    """Записать платёж в таблицу payments.
    Возвращает созданную запись.
    """
    payment = Payment(
        user_id=user_id,
        provider=provider,
        amount=float(amount),
        currency=currency,
        status=status,
        payment_id=payment_id,
        created_at=datetime.utcnow(),
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment