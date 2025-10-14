from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from core.db import SessionLocal
from core.models import User
from core.crud import grant_premium_days
import os

router = Router()
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_TG_IDS", "").split(',') if x.strip().isdigit()}

@router.message(Command("admin"))
async def admin_help(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await msg.answer(
        "Админ: /grant <tg_id> <days> — выдать премиум на N дней, /revoke <tg_id> — убрать премиум"
    )

@router.message(Command("grant"))
async def grant_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        _, tg_id_str, days_str = msg.text.split()
        tg_id = int(tg_id_str); days = int(days_str)
    except Exception:
        await msg.answer("Формат: /grant <tg_id> <days>")
        return
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == tg_id))).scalar_one_or_none()
        if not u:
            await msg.answer("Пользователь не найден")
            return
        await grant_premium_days(session, u.id, days)
    await msg.answer(f"Выдан премиум {tg_id} на {days} дней")

@router.message(Command("revoke"))
async def revoke_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        _, tg_id_str = msg.text.split()
        tg_id = int(tg_id_str)
    except Exception:
        await msg.answer("Формат: /revoke <tg_id>")
        return
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == tg_id))).scalar_one_or_none()
        if not u:
            await msg.answer("Пользователь не найден")
            return
        u.premium_until = None
        await session.commit()
    await msg.answer(f"Премиум у {tg_id} отключён")