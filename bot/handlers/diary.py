from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime
from core.db import SessionLocal
from core.crud import get_daily_summary
from sqlalchemy import select
from core.models import User

router = Router()

@router.message(Command("summary"))
async def cmd_summary(message: Message):
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id==message.from_user.id))).scalar_one()
        today = datetime.utcnow().date()
        s = await get_daily_summary(session, user.id, today)
    await message.answer(f"Сводка за сегодня: {round(s['kcal'])} ккал, Б {round(s['p'],1)} / Ж {round(s['f'],1)} / У {round(s['c'],1)}")