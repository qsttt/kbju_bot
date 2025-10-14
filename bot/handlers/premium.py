from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from core.db import SessionLocal
from core.models import User

router = Router()


# ---------- helpers ----------

def _remaining_str(until: Optional[datetime]) -> str:
    if not until:
        return "нет активной подписки"
    now = datetime.utcnow()
    if until <= now:
        return "истекла"
    delta = until - now
    days = delta.days
    hours = delta.seconds // 3600
    if days >= 1:
        return f"{days} дн. {hours} ч."
    mins = (delta.seconds % 3600) // 60
    return f"{hours} ч. {mins} мин."


def _premium_kb(show_trial: bool) -> InlineKeyboardMarkup:
    buttons = []
    if show_trial:
        buttons.append([InlineKeyboardButton(text="🎁 10 дней бесплатно", callback_data="prem:trial")])
    buttons.append([InlineKeyboardButton(text="Оформить премиум — 249 ₽", callback_data="prem:buy")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _trial_available(u: User) -> bool:
    # Триал доступен, если ещё не активировали ранее.
    # Поле может называться по-разному — подстрахуемся через getattr.
    return not bool(getattr(u, "trial_activated", False))


# ---------- handlers ----------

@router.message(Command("premium"))
async def premium_menu(msg: Message):
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one()

    left = _remaining_str(u.premium_until)
    show_trial = await _trial_available(u)

    text = (
        "Премиум: история 90 дней, weekly recap, избранное/частые, фото-распознавание, аналитика.\n\n"
        f"Статус: {left}\n"
    )
    await msg.answer(text, reply_markup=_premium_kb(show_trial))


# совместимость со старым импортом из menu.py (если там вызывается cmd_premium)
async def cmd_premium(message: Message):
    return await premium_menu(message)


# --- заглушки под коллбеки оформления (если их ещё нет в твоём файле, можно оставить так) ---

@router.callback_query(F.data == "prem:trial")
async def activate_trial(call):
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
        # если уже активирован — просто обновим экран
        if getattr(u, "trial_activated", False):
            await call.answer("Пробный уже активирован раньше", show_alert=True)
        else:
            # 10 дней триала
            u.premium_until = datetime.utcnow() + timedelta(days=10)
            # отметим, что триал был использован
            if hasattr(u, "trial_activated"):
                setattr(u, "trial_activated", True)
            await session.commit()
            await call.answer("Пробный активирован на 10 дней!")
    # перерисуем экран
    await premium_menu(call.message)


@router.callback_query(F.data == "prem:buy")
async def buy_premium(call):
    # тут должна быть логика создания платежа (ссылка ЮKassa) — оставляю краткую заглушку
    await call.answer()
    await call.message.edit_text(
        "Оформляем премиум за 249 ₽\nПерейди по ссылке для оплаты:",
    )
    # если у тебя уже есть готовая функция create_payment_link(...) — просто вызови её и подставь URL
