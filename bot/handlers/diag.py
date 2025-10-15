from __future__ import annotations

import os
from datetime import datetime
from typing import List

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func

from core.db import SessionLocal
from core.models import User, FoodDictionary, FoodCache, Entry
from api.translate import ru_en_for_search
from api.edamam_client import lookup_food

router = Router()


def _mask(value: str | None, keep: int = 4) -> str:
    if not value:
        return "<empty>"
    v = str(value)
    if len(v) <= keep:
        return "*" * len(v)
    return v[:keep] + "…" + "*" * max(0, len(v) - keep - 1)


@router.message(Command("diag"))
async def cmd_diag(message: Message):
    """
    Диагностика окружения и базовых зависимостей.
    """
    # ENV/ключи
    env_names = [
        "BOT_TOKEN",
        "EDAMAM_APP_ID",
        "EDAMAM_APP_KEY",
        "FDC_API_KEY",
        "DATABASE_URL",
        "USE_RU_EN_DICTIONARY",
        "USE_GEMINI_TRANSLATION",
        "ONLY_EN_FOR_PROVIDERS",
        "GEMINI_API_KEY",
    ]
    env_report: List[str] = []
    for name in env_names:
        val = os.getenv(name)
        if name in ("USE_RU_EN_DICTIONARY", "USE_GEMINI_TRANSLATION", "ONLY_EN_FOR_PROVIDERS"):
            masked = val or "<empty>"
        else:
            masked = _mask(val)
        env_report.append(f"{name}: {masked}")

    # БД метрики
    async with SessionLocal() as session:
        total_users = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
        dict_count = (await session.execute(select(func.count()).select_from(FoodDictionary))).scalar() or 0
        cache_total = (await session.execute(select(func.count()).select_from(FoodCache))).scalar() or 0
        cache_valid = (
            await session.execute(
                select(func.count()).select_from(FoodCache).where(FoodCache.ttl_until > datetime.utcnow())
            )
        ).scalar() or 0

        usr = (
            await session.execute(select(User).where(User.tg_id == message.from_user.id))
        ).scalar_one_or_none()
        today = datetime.utcnow().date()
        today_entries = 0
        if usr:
            today_entries = (
                await session.execute(
                    select(func.count()).select_from(Entry).where(Entry.user_id == usr.id, Entry.date == today)
                )
            ).scalar() or 0

        # Тест перевода и поиска
        try:
            en_variants = await ru_en_for_search("куриная грудка", method="boiled")
        except Exception as e:
            en_variants = [f"<error: {e}>"]
        try:
            items = await lookup_food(session, "куриная грудка", method="boiled")
            items_info = f"ok, {len(items)} items"
        except Exception as e:
            items_info = f"error: {e}"

    text = (
        "<b>DIAG</b>\n\n"
        "<b>ENV</b>:\n" + "\n".join(f"• {row}" for row in env_report) + "\n\n"
        f"<b>DB</b>: users={total_users}, dict={dict_count}, cache={cache_total} (valid {cache_valid}), today_entries={today_entries}\n\n"
        f"<b>Translate</b>: candidates={', '.join(en_variants) if en_variants else '<none>'}\n"
        f"<b>Lookup</b>: {items_info}\n"
    )
    await message.answer(text)