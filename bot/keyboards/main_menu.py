from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить")],
            [KeyboardButton(text="📊 Сводка"), KeyboardButton(text="⭐️ Премиум")],
            [KeyboardButton(text="⚙️ Профиль")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Напиши продукт или выбери действие…",
        one_time_keyboard=False,
        selective=False,
    )