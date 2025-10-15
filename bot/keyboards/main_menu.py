from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


MAIN_BUTTONS = [
    [
        KeyboardButton(text="➕ Добавить"),
        KeyboardButton(text="📊 Сводка"),
    ],
    [
        KeyboardButton(text="⭐️ Премиум"),
        KeyboardButton(text="👤 Профиль"),
    ],
]


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное меню как ReplyKeyboard. Показываем вне внутренних экранов."""
    return ReplyKeyboardMarkup(keyboard=MAIN_BUTTONS, resize_keyboard=True, one_time_keyboard=False)


def hide_main_menu() -> ReplyKeyboardRemove:
    """Убрать главное меню в режимах/экранах."""
    return ReplyKeyboardRemove()