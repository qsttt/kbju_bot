from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from core.db import SessionLocal
from core.crud import get_or_create_user
from core.config import settings
from bot.keyboards.main_menu import main_menu_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    async with SessionLocal() as session:
        _ = await get_or_create_user(session, message.from_user.id, settings.default_tz)
    await message.answer(
        "Привет! Я помогу считать КБЖУ.\nНажми кнопку «Добавить», чтобы внести продукт.",
        reply_markup=main_menu_kb(),
    )