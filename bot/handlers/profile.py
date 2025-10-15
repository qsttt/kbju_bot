# File: bot/handlers/profile.py
from __future__ import annotations

import logging
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, update

from core.db import async_session_maker
from core.models import User

# Пытаемся использовать готовые клавиатуры профиля
try:
    from bot.keyboards.profile import profile_kb  # type: ignore
except Exception:  # запасной вариант: пустая клавиатура
    from aiogram.types import InlineKeyboardMarkup

    def profile_kb(_: Optional[User] = None) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[])

router = Router()
log = logging.getLogger(__name__)


class ProfileStates(StatesGroup):
    waiting_weight = State()
    waiting_height = State()
    waiting_age = State()


async def _get_user(tg_id: int) -> Optional[User]:
    async with async_session_maker() as session:
        res = await session.execute(select(User).where(User.tg_id == tg_id))
        return res.scalars().first()


def _profile_text(u: User) -> str:
    parts = ["<b>Профиль</b>"]
    parts.append(f"Вес: <b>{u.weight_kg or '—'}</b> кг")
    parts.append(f"Рост: <b>{u.height_cm or '—'}</b> см")
    parts.append(f"Возраст: <b>{u.age or '—'}</b>")
    parts.append(f"Пол: <b>{(u.sex or '—').upper()}</b>")
    parts.append(f"Цель: <b>{u.goal or '—'}</b>")
    parts.append(f"PAL: <b>{u.pal or '—'}</b>")
    parts.append(f"Часовой пояс: <b>{u.timezone or '—'}</b>")
    return "\n".join(parts)


async def _render_profile(message: Message, u: User):
    try:
        kb = profile_kb(u)
    except Exception:
        kb = profile_kb(None)
    await message.answer(_profile_text(u), reply_markup=kb, parse_mode="HTML")


@router.message(Command("profile"))
@router.message(F.text == "👤 Профиль")
async def open_profile(message: Message, state: FSMContext):
    await state.clear()
    u = await _get_user(message.from_user.id)
    if not u:
        await message.answer("Профиль не найден. Попробуйте позже.")
        return
    await _render_profile(message, u)


# ===== Кнопки профиля =====
@router.callback_query(F.data.startswith("prof:"))
async def prof_router(call: CallbackQuery, state: FSMContext):
    data = call.data.split(":")  # варианты: prof:weight / prof:sex:male / prof:goal:loss / prof:pal:1.55 / prof:tz:Europe/Moscow
    action = data[1] if len(data) > 1 else None
    value = ":".join(data[2:]) if len(data) > 2 else None

    u = await _get_user(call.from_user.id)
    if not u:
        await call.answer("Профиль не найден")
        return

    # Числовые поля: вес/рост/возраст — запросим значение сообщением
    if action in {"weight", "height", "age"} and value is None:
        prompts = {
            "weight": "Введите текущий вес (кг), например: 68",
            "height": "Введите рост (см), например: 172",
            "age": "Введите возраст (полных лет), например: 29",
        }
        await call.message.answer(prompts[action])
        await state.set_state(getattr(ProfileStates, f"waiting_{action}"))
        await call.answer()
        return

    # Предвыбранные значения из инлайн-кнопок
    if action == "sex" and value:
        new_val = value.lower()[:10]
        async with async_session_maker() as session:
            await session.execute(update(User).where(User.id == u.id).values(sex=new_val))
            await session.commit()
        await call.answer("Пол обновлён")
    elif action == "goal" and value:
        new_val = value.lower()[:20]
        async with async_session_maker() as session:
            await session.execute(update(User).where(User.id == u.id).values(goal=new_val))
            await session.commit()
        await call.answer("Цель обновлена")
    elif action == "pal" and value:
        try:
            pal = float(value)
        except Exception:
            pal = None
        if pal:
            async with async_session_maker() as session:
                await session.execute(update(User).where(User.id == u.id).values(pal=pal))
                await session.commit()
            await call.answer("PAL обновлён")
        else:
            await call.answer("Некорректное значение PAL")
    elif action == "tz" and value:
        new_tz = value[:64]
        async with async_session_maker() as session:
            await session.execute(update(User).where(User.id == u.id).values(timezone=new_tz))
            await session.commit()
        await call.answer("Часовой пояс обновлён")

    # Перерисуем профиль
    u = await _get_user(call.from_user.id)
    try:
        kb = profile_kb(u)
    except Exception:
        kb = profile_kb(None)
    await call.message.edit_text(_profile_text(u), reply_markup=kb, parse_mode="HTML")


# ===== Обработка числовых ответов =====
@router.message(ProfileStates.waiting_weight)
async def set_weight(message: Message, state: FSMContext):
    try:
        val = float(message.text.replace(",", "."))
    except Exception:
        await message.answer("Пожалуйста, число. Например: 68")
        return
    async with async_session_maker() as session:
        res = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        u = res.scalars().first()
        if not u:
            await message.answer("Профиль не найден")
            return
        u.weight_kg = val
        await session.commit()
    await state.clear()
    await message.answer("Вес обновлён.")
    await open_profile(message, state)


@router.message(ProfileStates.waiting_height)
async def set_height(message: Message, state: FSMContext):
    try:
        val = float(message.text.replace(",", "."))
    except Exception:
        await message.answer("Пожалуйста, число. Например: 172")
        return
    async with async_session_maker() as session:
        res = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        u = res.scalars().first()
        if not u:
            await message.answer("Профиль не найден")
            return
        u.height_cm = val
        await session.commit()
    await state.clear()
    await message.answer("Рост обновлён.")
    await open_profile(message, state)


@router.message(ProfileStates.waiting_age)
async def set_age(message: Message, state: FSMContext):
    try:
        val = int(float(message.text.replace(",", ".")))
    except Exception:
        await message.answer("Пожалуйста, целое число. Например: 29")
        return
    async with async_session_maker() as session:
        res = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        u = res.scalars().first()
        if not u:
            await message.answer("Профиль не найден")
            return
        u.age = val
        await session.commit()
    await state.clear()
    await message.answer("Возраст обновлён.")
    await open_profile(message, state)
