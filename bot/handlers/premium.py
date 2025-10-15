from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from bot.keyboards.main_menu import main_menu_kb

router = Router()
log = logging.getLogger(__name__)

# --- inline keyboard (внутри файла, чтобы не плодить ещё один модуль) ---
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def premium_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🎁 Активировать 10 дней", callback_data="premium:trial")],
        [InlineKeyboardButton(text="💳 Оплатить премиум", callback_data="premium:pay")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- open premium ---
@router.message(F.text == "⭐️ Премиум")
async def premium_open_msg(message: Message):
    text = (
        "<b>Премиум</b>\n\n"
        "• Распознавание блюд по фото\n"
        "• Расширенная база продуктов\n"
        "• Продвинутые отчёты и цели\n"
        "• Индивидуальные подсказки\n\n"
        "Доступна 10‑дневная проба."
    )
    await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    await message.answer("Выбери действие:", reply_markup=premium_kb())


@router.callback_query(F.data == "premium:open")
async def premium_open_cb(call: CallbackQuery):
    text = (
        "<b>Премиум</b>\n\n"
        "• Распознавание блюд по фото\n"
        "• Расширенная база продуктов\n"
        "• Продвинутые отчёты и цели\n"
        "• Индивидуальные подсказки\n\n"
        "Доступна 10‑дневная проба."
    )
    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=premium_kb())
    except Exception:
        await call.message.answer(text, parse_mode="HTML", reply_markup=premium_kb())
    await call.answer()


@router.callback_query(F.data == "premium:trial")
async def premium_trial(call: CallbackQuery):
    # Тут должна быть ваша логика активации пробного периода
    await call.answer("Пробный период активирован!", show_alert=False)
    await call.message.edit_text(
        "✅ Пробный период активирован на 10 дней.",
        reply_markup=premium_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "premium:pay")
async def premium_pay(call: CallbackQuery):
    # Плейсхолдер оплаты — замените на вашу платёжную ссылку/инвойс
    await call.answer()
    await call.message.edit_text(
        "Оплата премиума: свяжитесь с поддержкой или используйте команду /buy (плейсхолдер).",
        reply_markup=premium_kb(),
        parse_mode="HTML",
    )


# --- выход домой ---
@router.callback_query(F.data == "main:menu")
async def back_to_main_from_premium(call: CallbackQuery):
    try:
        await call.message.edit_text("Окей, выхожу в меню.")
    except Exception:
        pass
    await call.message.answer("Что дальше?", reply_markup=main_menu_kb())
    await call.answer()