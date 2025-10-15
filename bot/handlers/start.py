from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from core.db import SessionLocal
from core.crud import get_or_create_user
from bot.keyboards.main_menu import main_menu_kb

router = Router()


@router.message(CommandStart())
async def on_start(message: Message):
    # Гарантируем наличие пользователя
    async with SessionLocal() as session:
        _ = await get_or_create_user(session, message.from_user.id)

    text = (
        "Привет! Я помогу посчитать КБЖУ.\n\n"
        "Введи блюдо и порцию одной строкой, например:\n"
        "<code>куриная грудка варёная 140 г</code> или <code>батончик 180 ккал</code>."
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")