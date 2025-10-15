from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal, Optional

from sqlalchemy import select

from core.models import User


async def grant_premium_days(session, *, user_key: int, by: Literal["id", "tg_id"] = "id", days: int = 0):
    """
    Продлевает/выдаёт премиум на указанное количество дней.
    - user_key: значение user.id (by="id") или user.tg_id (by="tg_id").
    - days: на сколько дней выдать/продлить.

    Возвращает новое значение `user.premium_until` (если поле существует), иначе True.
    """
    if days <= 0:
        raise ValueError("days must be > 0")

    if by == "tg_id":
        stmt = select(User).where(User.tg_id == user_key)
    else:
        stmt = select(User).where(User.id == user_key)

    user: Optional[User] = (await session.execute(stmt)).scalar_one_or_none()
    if not user:
        raise ValueError("user not found")

    now = datetime.utcnow()

    # Если у модели есть поле premium_until — используем его как базу продления
    if hasattr(user, "premium_until"):
        base = getattr(user, "premium_until") or now
        if base < now:
            base = now
        new_until = base + timedelta(days=days)
        setattr(user, "premium_until", new_until)
        # Если есть булево поле is_premium — включим его
        if hasattr(user, "is_premium"):
            setattr(user, "is_premium", True)
        await session.commit()
        return new_until

    # Фолбэк: если premium_until нет, но есть is_premium — просто включим
    if hasattr(user, "is_premium"):
        setattr(user, "is_premium", True)
        await session.commit()
        return True

    # Если в схеме нет ни одного поля — сигнализируем о проблеме схемы
    raise AttributeError("User model has no premium fields (premium_until / is_premium)")