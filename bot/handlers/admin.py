from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.db import SessionLocal
from core.crud_grants import grant_premium_days

router = Router()
log = logging.getLogger(__name__)


@router.message(Command("grant_premium"))
async def cmd_grant_premium(message: Message):
    """
    Выдаёт премиум на N дней пользователю по его Telegram ID.
    Использование: /grant_premium <tg_id> <days>
    Пример: /grant_premium 123456789 10
    """
    parts = (message.text or "").strip().split()
    if len(parts) != 3:
        await message.answer("Формат: /grant_premium <tg_id> <days>")
        return

    try:
        tg_id = int(parts[1])
        days = int(parts[2])
    except ValueError:
        await message.answer("tg_id и days должны быть числами")
        return

    async with SessionLocal() as session:
        try:
            until = await grant_premium_days(session, user_key=tg_id, by="tg_id", days=days)
        except Exception as e:  # noqa: BLE001
            log.exception("grant_premium_days failed")
            await message.answer(f"Ошибка: {e}")
            return

    until_str = until.strftime("%Y-%m-%d %H:%M:%S") if isinstance(until, datetime) else str(until)
    await message.answer(f"Премиум выдан до: {until_str}")