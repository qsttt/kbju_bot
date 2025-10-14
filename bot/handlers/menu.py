from aiogram import Router, F
from aiogram.types import Message
from bot.keyboards.main_menu import main_menu_kb
from .manual_input import add_prompt
from .diary import cmd_summary
from .premium import premium_menu  # <-- было: cmd_premium

router = Router()

@router.message(F.text == "➕ Добавить")
async def on_add(msg: Message):
    await add_prompt(msg)

@router.message(F.text == "📊 Сводка")
async def on_summary(msg: Message):
    await cmd_summary(msg)

@router.message(F.text == "⭐️ Премиум")
async def on_premium(msg: Message):
    await premium_menu(msg)  # <-- было: cmd_premium(msg)

@router.message(F.text == "⚙️ Профиль")
async def on_profile(msg: Message):
    await msg.answer("Профиль скоро будет доступен. Пока можно продолжать добавлять продукты.", reply_markup=main_menu_kb())
