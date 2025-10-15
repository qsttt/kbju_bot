from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.main_menu import main_menu_kb

router = Router()
log = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Показываем главное меню без автоперехода в режим ввода."""
    await message.answer(
        "Привет! Я помогу посчитать КБЖУ.\nВыбери интересующее тебя меню.",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )


# Явная команда на показ главного меню
@router.message(F.text.in_({"🏠 В главное меню", "Главное меню", "меню"}))
async def back_to_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu_kb())


# Кнопки, за которые отвечает именно меню (профиль/сводка/премиум/добавить обрабатываются своими модулями)
# Здесь из меню НЕ перехватываем «👤 Профиль», чтобы профиль отработал в своём хендлере
# Аналогично «➕ Добавить» обрабатывается в manual_input, «📊 Сводка» — в diary, «⭐️ Премиум» — в premium

# Никаких заглушек «Профиль временно недоступен» — убрано намеренно