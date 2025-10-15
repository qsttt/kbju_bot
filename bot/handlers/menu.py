from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold

from sqlalchemy import select

from core.db import SessionLocal
from core.models import User
from core.crud import get_daily_summary

from bot.keyboards.main_menu import main_menu_kb, hide_main_menu
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Для перехода в профиль переиспользуем show_profile
try:
    from bot.handlers.profile import show_profile  # type: ignore
except Exception:  # заглушка на случай циклических импортов на этапе запуска
    async def show_profile(msg: Message):
        await msg.answer("Профиль временно недоступен.")


router = Router()
log = logging.getLogger(__name__)


# ============ helpers ============

def _home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 В главное меню", callback_data="main:menu")]]
    )


def _summary_text(total: float | None, p: float | None, f: float | None, c: float | None) -> str:
    lines = ["📊 Сводка за сегодня"]
    if total is not None:
        lines.append(f"Калории: {round(total)} ккал")
    if any(v is not None for v in (p, f, c)):
        lines.append(f"БЖУ: Б {round((p or 0), 1)} / Ж {round((f or 0), 1)} / У {round((c or 0), 1)}")
    if len(lines) == 1:
        lines.append("Пока пусто. Добавь приём пищи через ‘➕ Добавить’.")
    return "\n".join(lines)


# ============ main menu ============

@router.message(CommandStart())
@router.message(Command("menu"))
async def cmd_start(message: Message):
    await message.answer("Что делаем?", reply_markup=main_menu_kb())


@router.callback_query(F.data == "main:menu")
async def cb_main_menu(call: CallbackQuery):
    try:
        await call.message.edit_text("Что делаем?")
    except Exception:
        pass
    await call.message.answer("Готово.", reply_markup=main_menu_kb())
    await call.answer()


# ============ summary ============

async def _show_summary(message: Message):
    # внутри экранов прячем реплай-меню
    await message.answer("Открываю сводку…", reply_markup=hide_main_menu())
    async with SessionLocal() as session:
        usr = (await session.execute(select(User).where(User.tg_id == message.from_user.id))).scalar_one()
        today_utc = datetime.utcnow().date()
        s = await get_daily_summary(session, usr.id, today_utc)
    txt = _summary_text(s.get("kcal"), s.get("p"), s.get("f"), s.get("c"))
    await message.answer(txt, reply_markup=_home_kb())


@router.message(F.text.in_({"📊 Сводка", "Сводка", "сводка"}))
async def msg_summary(message: Message):
    await _show_summary(message)


@router.callback_query(F.data == "menu:summary")
async def cb_summary(call: CallbackQuery):
    await call.answer()
    await _show_summary(call.message)


# ============ premium ============

_PREMIUM_TEXT = (
    "⭐️ Премиум\n\n"
    "• AI-подсказки и автоподбор блюд\n"
    "• Расширенная аналитика по дням и неделям\n"
    "• Экспорт/импорт дневника\n\n"
    "Доступен пробный период 10 дней."
)


def _premium_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🎁 Пробный период 10 дней", callback_data="premium:trial")],
        [InlineKeyboardButton(text="💳 Оформить премиум", callback_data="premium:buy")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _show_premium(message: Message):
    await message.answer("Открываю Премиум…", reply_markup=hide_main_menu())
    await message.answer(_PREMIUM_TEXT, reply_markup=_premium_kb())


@router.message(F.text.in_({"⭐️ Премиум", "Премиум", "премиум"}))
async def msg_premium(message: Message):
    await _show_premium(message)


@router.callback_query(F.data == "menu:premium")
async def cb_premium(call: CallbackQuery):
    await call.answer()
    await _show_premium(call.message)


@router.callback_query(F.data.in_({"premium:trial", "premium:buy"}))
async def cb_premium_actions(call: CallbackQuery):
    if call.data == "premium:trial":
        await call.answer("Пробный период активирован (демо)")
    else:
        await call.answer("Покупка пока недоступна (демо)")


# ============ profile (entry point) ============

@router.message(F.text.in_({"👤 Профиль", "Профиль", "профиль"}))
async def msg_profile(message: Message):
    # спрячем главное меню и откроем профильный экран
    await message.answer("Открываю профиль…", reply_markup=hide_main_menu())
    await show_profile(message)


@router.callback_query(F.data == "menu:profile")
async def cb_profile(call: CallbackQuery):
    await call.answer()
    await show_profile(call.message)