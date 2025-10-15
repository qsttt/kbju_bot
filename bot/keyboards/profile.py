from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def profile_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="⚖️ Вес", callback_data="prof:weight"),
            InlineKeyboardButton(text="📏 Рост", callback_data="prof:height"),
        ],
        [
            InlineKeyboardButton(text="🎂 Возраст", callback_data="prof:age"),
            InlineKeyboardButton(text="⚧ Пол", callback_data="prof:sex"),
        ],
        [
            InlineKeyboardButton(text="🎯 Цель", callback_data="prof:goal"),
            InlineKeyboardButton(text="🏃 PAL", callback_data="prof:pal"),
        ],
        [
            InlineKeyboardButton(text="🕒 Часовой пояс", callback_data="prof:tz"),
            InlineKeyboardButton(text="ℹ️ Что это?", callback_data="prof:help"),
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="prof:refresh"),
        ],
        [
            InlineKeyboardButton(text="🏠 В главное меню", callback_data="main:menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sex_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Муж", callback_data="sex:male"), InlineKeyboardButton(text="Жен", callback_data="sex:female")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="prof:back")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def goal_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Похудение", callback_data="goal:lose")],
        [InlineKeyboardButton(text="Поддержание", callback_data="goal:maintain")],
        [InlineKeyboardButton(text="Набор", callback_data="goal:gain")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="prof:back")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pal_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="1.2 — минимум", callback_data="pal:1.2")],
        [InlineKeyboardButton(text="1.375 — лёгкая активность", callback_data="pal:1.375")],
        [InlineKeyboardButton(text="1.55 — средняя активность", callback_data="pal:1.55")],
        [InlineKeyboardButton(text="1.725 — высокая активность", callback_data="pal:1.725")],
        [InlineKeyboardButton(text="1.9 — экстремальная", callback_data="pal:1.9")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="prof:back")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tz_kb() -> InlineKeyboardMarkup:
    # Список поясов РФ + ручной ввод (можно расширять)
    rows = [
        [InlineKeyboardButton(text="Калининград (Europe/Kaliningrad)", callback_data="tz:Europe/Kaliningrad")],
        [InlineKeyboardButton(text="Москва (Europe/Moscow)", callback_data="tz:Europe/Moscow")],
        [InlineKeyboardButton(text="Самара (Europe/Samara)", callback_data="tz:Europe/Samara")],
        [InlineKeyboardButton(text="Екатеринбург (Asia/Yekaterinburg)", callback_data="tz:Asia/Yekaterinburg")],
        [InlineKeyboardButton(text="Омск (Asia/Omsk)", callback_data="tz:Asia/Omsk")],
        [InlineKeyboardButton(text="Новосибирск (Asia/Novosibirsk)", callback_data="tz:Asia/Novosibirsk")],
        [InlineKeyboardButton(text="Красноярск (Asia/Krasnoyarsk)", callback_data="tz:Asia/Krasnoyarsk")],
        [InlineKeyboardButton(text="Иркутск (Asia/Irkutsk)", callback_data="tz:Asia/Irkutsk")],
        [InlineKeyboardButton(text="Якутск (Asia/Yakutsk)", callback_data="tz:Asia/Yakutsk")],
        [InlineKeyboardButton(text="Владивосток (Asia/Vladivostok)", callback_data="tz:Asia/Vladivostok")],
        [InlineKeyboardButton(text="Магадан (Asia/Magadan)", callback_data="tz:Asia/Magadan")],
        [InlineKeyboardButton(text="Сахалин (Asia/Sakhalin)", callback_data="tz:Asia/Sakhalin")],
        [InlineKeyboardButton(text="Камчатка (Asia/Kamchatka)", callback_data="tz:Asia/Kamchatka")],
        [InlineKeyboardButton(text="Другой…", callback_data="tz:custom")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="prof:back")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)