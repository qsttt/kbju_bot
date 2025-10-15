from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict


def variants_kb(variants: List[Dict], include_ai: bool = True) -> InlineKeyboardMarkup:
    """Кнопки вариантов продукта + опционально «Посчитать с помощью ИИ»."""
    rows: List[List[InlineKeyboardButton]] = []
    for i, v in enumerate(variants[:5]):
        title = v.get("title") or "Без названия"
        kcal = v.get("kcal100") or 0
        p = v.get("p100") or 0
        f = v.get("f100") or 0
        c = v.get("c100") or 0
        text = f"{title} — {kcal:.0f} ккал/100г · Б/Ж/У {p:.1f}/{f:.1f}/{c:.1f}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"pick:{i}")])

    if include_ai:
        rows.append([InlineKeyboardButton(text="🤖 Посчитать с помощью ИИ", callback_data="variant:ai")])

    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_add_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Добавить в отчёт", callback_data="confirm:add")],
            [InlineKeyboardButton(text="🔁 Выбрать другой вариант", callback_data="confirm:other")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )