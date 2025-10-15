from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главная клавиатура профиля

def profile_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="⚖️ Вес", callback_data="prof:weight"),
            InlineKeyboardButton(text="📏 Рост", callback_data="prof:height"),
        ],
        [
            InlineKeyboardButton(text="🎂 Возраст", callback_data="prof:age"),
            InlineKeyboardButton(text="🚻 Пол", callback_data="prof:sex"),
        ],
        [
            InlineKeyboardButton(text="🎯 Цель", callback_data="prof:goal"),
            InlineKeyboardButton(text="🏃 PAL", callback_data="prof:pal"),
        ],
        [
            InlineKeyboardButton(text="🕒 Часовой пояс", callback_data="prof:tz"),
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="prof:refresh"),
            InlineKeyboardButton(text="🏠 В главное меню", callback_data="main:menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# Подклавиатуры выбора значений

def sex_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="♂️ Мужской", callback_data="prof:sex:male"),
            InlineKeyboardButton(text="♀️ Женский", callback_data="prof:sex:female"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="prof:refresh")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def goal_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="📉 Похудение", callback_data="prof:goal:lose"),
            InlineKeyboardButton(text="⚖️ Поддержание", callback_data="prof:goal:maintain"),
            InlineKeyboardButton(text="📈 Набор", callback_data="prof:goal:gain"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="prof:refresh")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pal_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="1.2", callback_data="prof:pal:1.2"),
            InlineKeyboardButton(text="1.375", callback_data="prof:pal:1.375"),
            InlineKeyboardButton(text="1.55", callback_data="prof:pal:1.55"),
        ],
        [
            InlineKeyboardButton(text="1.725", callback_data="prof:pal:1.725"),
            InlineKeyboardButton(text="1.9", callback_data="prof:pal:1.9"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="prof:refresh")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tz_kb() -> InlineKeyboardMarkup:
    # Сокращённый список; при необходимости расширить/сделать пагинацию
    zones = [
        "Europe/Kaliningrad",
        "Europe/Moscow",
        "Europe/Samara",
        "Asia/Yekaterinburg",
        "Asia/Omsk",
        "Asia/Novosibirsk",
        "Asia/Irkutsk",
        "Asia/Yakutsk",
        "Asia/Vladivostok",
        "Asia/Magadan",
        "Asia/Kamchatka",
    ]
    rows = [[InlineKeyboardButton(text=z, callback_data=f"prof:tz:{z}")] for z in zones[:10]]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="prof:refresh")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
