from __future__ import annotations
from datetime import datetime, date
from typing import Iterable, Optional
from sqlalchemy import select, insert, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import User, Entry, FoodDictionary, UserCustomFood, FoodCache, UnitConversion, Payment
from datetime import datetime, timedelta

# USERS
async def get_or_create_user(session: AsyncSession, tg_id: int, default_tz: str) -> User:
    res = await session.execute(select(User).where(User.tg_id == tg_id))
    user = res.scalar_one_or_none()
    if user:
        return user
    user = User(tg_id=tg_id, tz=default_tz, created_at=datetime.utcnow())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def update_user_profile(session: AsyncSession, user_id: int, **fields) -> None:
    await session.execute(update(User).where(User.id == user_id).values(**fields))
    await session.commit()

# ENTRIES
async def add_entry(session: AsyncSession, user_id: int, *,
                    on_date: date, title: str, amount_value: float, amount_unit: str,
                    amount_grams: float | None, kcal: float | None, p: float | None,
                    f: float | None, c: float | None, is_calories_only: bool, source: str = "manual") -> Entry:
    entry = Entry(
        user_id=user_id, date=on_date, title=title,
        amount_value=amount_value, amount_unit=amount_unit, amount_grams=amount_grams,
        kcal=kcal, protein=p, fat=f, carbs=c, is_calories_only=is_calories_only,
        source=source, created_at=datetime.utcnow()
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry

async def get_daily_summary(session: AsyncSession, user_id: int, on_date: date) -> dict:
    res = await session.execute(
        select(
            func.coalesce(func.sum(Entry.kcal), 0),
            func.coalesce(func.sum(Entry.protein), 0),
            func.coalesce(func.sum(Entry.fat), 0),
            func.coalesce(func.sum(Entry.carbs), 0),
        ).where(and_(Entry.user_id == user_id, Entry.date == on_date))
    )
    kcal, p, f, c = res.one()
    return {"kcal": float(kcal or 0), "p": float(p or 0), "f": float(f or 0), "c": float(c or 0)}

async def delete_last_entry(session: AsyncSession, user_id: int, within_minutes: int = 10) -> bool:
    # Удаляет последнюю запись пользователя за последние N минут
    threshold = datetime.utcnow() - timedelta(minutes=within_minutes)
    res = await session.execute(
        select(Entry).where(Entry.user_id == user_id, Entry.created_at >= threshold)
        .order_by(Entry.created_at.desc()).limit(1)
    )
    last = res.scalar_one_or_none()
    if not last:
        return False
    await session.delete(last)
    await session.commit()
    return True

# FOOD DICTIONARY & CACHE
async def get_food_by_key(session: AsyncSession, food_key: str) -> FoodDictionary | None:
    res = await session.execute(select(FoodDictionary).where(FoodDictionary.food_key == food_key))
    return res.scalar_one_or_none()

async def upsert_food_cache(session: AsyncSession, food_key: str, json_payload: str, ttl_until: datetime) -> None:
    existing = await session.get(FoodCache, food_key)
    if existing:
        existing.json_payload = json_payload
        existing.ttl_until = ttl_until
    else:
        session.add(FoodCache(food_key=food_key, json_payload=json_payload, ttl_until=ttl_until))
    await session.commit()

async def cleanup_expired_cache(session: AsyncSession) -> int:
    res = await session.execute(delete(FoodCache).where(FoodCache.ttl_until < datetime.utcnow()))
    await session.commit()
    return res.rowcount or 0

# PAYMENTS
async def log_payment(session: AsyncSession, user_id: int, *, amount: float, currency: str, status: str, payment_id: str) -> Payment:
    payment = Payment(user_id=user_id, amount=amount, currency=currency, status=status, payment_id=payment_id)
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment

async def set_premium_until(session: AsyncSession, user_id: int, until: datetime | None) -> None:
    await session.execute(update(User).where(User.id == user_id).values(premium_until=until))
    await session.commit()

async def activate_trial(session: AsyncSession, user_id: int, days: int = 10) -> None:
    until = datetime.utcnow() + timedelta(days=days)
    await session.execute(update(User).where(User.id == user_id).values(
        premium_until=until, trial_used=True, trial_activated_at=datetime.utcnow()))
    await session.commit()

async def grant_premium_days(session: AsyncSession, user_id: int, days: int) -> None:
    # продлеваем от текущего premium_until, если он активен; иначе от сейчас
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one()
    base = user.premium_until if (user.premium_until and user.premium_until > datetime.utcnow()) else datetime.utcnow()
    until = base + timedelta(days=days)
    await session.execute(update(User).where(User.id == user_id).values(premium_until=until))
    await session.commit()