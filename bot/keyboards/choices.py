from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def variants_kb(titles: list[str], with_cancel: bool = True) -> InlineKeyboardMarkup:
    rows = []
    for i, t in enumerate(titles[:10]):
        rows.append([InlineKeyboardButton(text=t, callback_data=f"pick:{i}")])
    rows.append([InlineKeyboardButton(text="Нет подходящего", callback_data="pick:none")])
    if with_cancel:
        rows.append([InlineKeyboardButton(text="🏠 В главное меню", callback_data="go:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ask_kcal_kb(with_cancel: bool = True) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Указать ккал", callback_data="ask:kcal")]]
    if with_cancel:
        rows.append([InlineKeyboardButton(text="🏠 В главное меню", callback_data="go:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 В главное меню", callback_data="go:main")]]
    )