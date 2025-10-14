from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

def variants_kb(titles: List[str], with_cancel: bool = False) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=t, callback_data=f"pick:{i}")] for i, t in enumerate(titles)]
    rows.append([InlineKeyboardButton(text="Ничего из этого", callback_data="pick:none")])
    if with_cancel:
        rows.append([InlineKeyboardButton(text="Отмена", callback_data="cancel:add")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def ask_kcal_kb(with_cancel: bool = False) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Указать ккал", callback_data="ask:kcal")]]
    if with_cancel:
        rows.append([InlineKeyboardButton(text="Отмена", callback_data="cancel:add")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# Для /add и любых вопросов в процессе ввода

def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel:add")]
    ])