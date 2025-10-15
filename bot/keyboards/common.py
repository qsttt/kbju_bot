# File: bot/keyboards/common.py
from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def back_home_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для выхода/отмены внутри режимов.
    Показываем две кнопки: «❌ Отмена» и «🏠 В главное меню».
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена"), KeyboardButton(text="🏠 В главное меню")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Напиши сообщение или выбери кнопку…",
    )


__all__ = ["back_home_kb"]
