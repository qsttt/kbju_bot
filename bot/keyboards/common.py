from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def confirm_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Повторить", callback_data="again")],
            [InlineKeyboardButton(text="Отменить последний", callback_data="undo")]
        ]
    )

def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="go:menu")]
        ]
    )