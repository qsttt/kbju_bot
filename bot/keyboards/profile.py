from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def profile_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить вес", callback_data="prof:weight")],
        [InlineKeyboardButton(text="Изменить рост", callback_data="prof:height")],
        [InlineKeyboardButton(text="Изменить возраст", callback_data="prof:age")],
        [InlineKeyboardButton(text="Пол: Муж / Жен", callback_data="prof:sex")],
        [InlineKeyboardButton(text="Цель", callback_data="prof:goal")],
        [InlineKeyboardButton(text="Активность (PAL)", callback_data="prof:pal")],
        [InlineKeyboardButton(text="Пересчитать нормы", callback_data="prof:recalc")],
        [InlineKeyboardButton(text="Закрыть", callback_data="prof:close")],
    ])

def sex_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Муж", callback_data="sex:M")],
        [InlineKeyboardButton(text="Жен", callback_data="sex:F")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="prof:back")],
    ])

def goal_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Похудение", callback_data="goal:loss")],
        [InlineKeyboardButton(text="Поддержание", callback_data="goal:maintain")],
        [InlineKeyboardButton(text="Набор", callback_data="goal:gain")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="prof:back")],
    ])

def pal_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1.2 (сидячий)", callback_data="pal:1.2")],
        [InlineKeyboardButton(text="1.375 (лёгкая актив.)", callback_data="pal:1.375")],
        [InlineKeyboardButton(text="1.55 (умеренная)", callback_data="pal:1.55")],
        [InlineKeyboardButton(text="1.725 (высокая)", callback_data="pal:1.725")],
        [InlineKeyboardButton(text="1.9 (очень высокая)", callback_data="pal:1.9")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="prof:back")],
    ])
