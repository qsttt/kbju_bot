from __future__ import annotations

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, text

from core.db import SessionLocal
from core.models import User
from bot.keyboards.profile import profile_kb, sex_kb, goal_kb, pal_kb, tz_kb
from bot.utils.calcs import calc_bmr, calc_tdee, calc_targets
from bot.keyboards.main_menu import main_menu_kb

try:
    from bot.handlers.manual_input import cancel_pending_for  # type: ignore
except Exception:
    def cancel_pending_for(user_id: int) -> None:  # type: ignore
        return

log = logging.getLogger(__name__)
router = Router()


class ProfileForm(StatesGroup):
    weight = State()
    height = State()
    age = State()
    sex = State()
    goal = State()
    pal = State()
    tz = State()


async def _get_tz(session, user: User) -> str | None:
    try:
        res = await session.execute(text("SELECT timezone FROM users WHERE id=:id"), {"id": user.id})
        row = res.first()
        return row[0] if row and row[0] else None
    except Exception:
        return None


async def _ensure_tz_column(session) -> None:
    try:
        await session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(64)"))
    except Exception:
        pass


def _profile_text(user: User, tz: str | None) -> str:
    lines = [
        "👤 <b>Профиль</b>",
        f"Вес: {user.weight_kg if user.weight_kg is not None else '-'} кг",
        f"Рост: {user.height_cm if user.height_cm is not None else '-'} см",
        f"Возраст: {user.age if user.age is not None else '-'}",
        f"Пол: {user.sex if user.sex else '-'}",
        f"Цель: {user.goal if user.goal else '-'}",
        f"PAL: {user.pal if user.pal is not None else '-'}",
        f"Часовой пояс: {tz or '-'}",
    ]
    try:
        if user.sex and user.age and user.height_cm and user.weight_kg and user.pal:
            bmr = calc_bmr(sex=user.sex, age=user.age, weight_kg=user.weight_kg, height_cm=user.height_cm)
            tdee = calc_tdee(bmr=bmr, pal=user.pal)
            targets = calc_targets(tdee=tdee, goal=user.goal or "maintain")
            lines.append("")
            lines.append("BMR — базовый обмен (ккал в покое)")
            lines.append("TDEE — дневная норма с учётом активности")
            lines.append("PAL — коэффициент активности (1.2..1.9)")
            lines.append("")
            lines.append(f"BMR: {round(bmr)} ккал")
            lines.append(f"TDEE: {round(tdee)} ккал")
            lines.append(
                "Целевые КБЖУ: "
                f"{round(targets['kcal'])} ккал, "
                f"Б {round(targets['p'], 1)} / Ж {round(targets['f'], 1)} / У {round(targets['c'], 1)}"
            )
    except Exception:
        pass
    return "\n".join(lines)


async def show_profile(msg: Message):
    cancel_pending_for(msg.from_user.id)
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one()
        await _ensure_tz_column(session)
        tz = await _get_tz(session, user)
        txt = _profile_text(user, tz)
    await msg.answer(txt, reply_markup=profile_kb(), parse_mode="HTML")


@router.callback_query(F.data == "prof:refresh")
async def prof_refresh(call: CallbackQuery):
    cancel_pending_for(call.from_user.id)
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
        await _ensure_tz_column(session)
        tz = await _get_tz(session, user)
        txt = _profile_text(user, tz)
    try:
        await call.message.edit_text(txt, reply_markup=profile_kb(), parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await call.answer()


@router.callback_query(F.data == "prof:back")
async def prof_back(call: CallbackQuery):
    await prof_refresh(call)


# --- Закрыть → заменено на «В главное меню» глобально через main:menu ---


# ===== Вес/Рост/Возраст =====

@router.callback_query(F.data == "prof:weight")
async def prof_weight(call: CallbackQuery, state: FSMContext):
    cancel_pending_for(call.from_user.id)
    await state.set_state(ProfileForm.weight)
    await call.message.edit_text("Введи вес (кг), например: 72.5", reply_markup=profile_kb())
    await call.answer()


@router.message(ProfileForm.weight)
async def prof_weight_save(msg: Message, state: FSMContext):
    try:
        w = float((msg.text or "").replace(",", "."))
    except Exception:
        await msg.answer("Не понял число. Повтори вес в кг, например 72.5")
        return
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one()
        user.weight_kg = w
        await session.commit()
    await state.clear()
    await msg.answer("Вес обновлён.")
    await show_profile(msg)


@router.callback_query(F.data == "prof:height")
async def prof_height(call: CallbackQuery, state: FSMContext):
    cancel_pending_for(call.from_user.id)
    await state.set_state(ProfileForm.height)
    await call.message.edit_text("Введи рост (см), например: 178", reply_markup=profile_kb())
    await call.answer()


@router.message(ProfileForm.height)
async def prof_height_save(msg: Message, state: FSMContext):
    try:
        h = float((msg.text or "").replace(",", "."))
    except Exception:
        await msg.answer("Не понял число. Повтори рост в сантиметрах, например 178")
        return
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one()
        user.height_cm = h
        await session.commit()
    await state.clear()
    await msg.answer("Рост обновлён.")
    await show_profile(msg)


@router.callback_query(F.data == "prof:age")
async def prof_age(call: CallbackQuery, state: FSMContext):
    cancel_pending_for(call.from_user.id)
    await state.set_state(ProfileForm.age)
    await call.message.edit_text("Введи возраст (полных лет), например: 28", reply_markup=profile_kb())
    await call.answer()


@router.message(ProfileForm.age)
async def prof_age_save(msg: Message, state: FSMContext):
    try:
        a = int(float((msg.text or "").replace(",", ".")))
    except Exception:
        await msg.answer("Не понял число. Повтори возраст, например 28")
        return
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one()
        user.age = a
        await session.commit()
    await state.clear()
    await msg.answer("Возраст обновлён.")
    await show_profile(msg)


# ===== Пол/Цель/PAL =====

@router.callback_query(F.data == "prof:sex")
async def prof_sex(call: CallbackQuery):
    cancel_pending_for(call.from_user.id)
    await call.message.edit_text("Выбери пол:", reply_markup=sex_kb())
    await call.answer()


@router.callback_query(F.data.regexp(r"^(sex[:_])?(male|female)$") | F.data.in_({"sex:male", "sex:female", "sex_male", "sex_female"}))
async def prof_sex_set(call: CallbackQuery):
    data = call.data
    if ":" in data:
        _, value = data.split(":", 1)
    elif "_" in data:
        _, value = data.split("_", 1)
    else:
        value = data
    if value not in {"male", "female"}:
        await call.answer("Неизвестное значение")
        return
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
        user.sex = value
        await session.commit()
    await call.answer("Пол сохранён")
    await prof_refresh(call)


@router.callback_query(F.data == "prof:goal")
async def prof_goal(call: CallbackQuery):
    cancel_pending_for(call.from_user.id)
    await call.message.edit_text("Выбери цель:", reply_markup=goal_kb())
    await call.answer()


@router.callback_query(F.data.regexp(r"^(goal[:_])?(lose|maintain|gain)$"))
async def prof_goal_set(call: CallbackQuery):
    data = call.data
    if ":" in data:
        _, value = data.split(":", 1)
    elif "_" in data:
        _, value = data.split("_", 1)
    else:
        value = data
    if value not in {"lose", "maintain", "gain"}:
        await call.answer("Неизвестная цель")
        return
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
        user.goal = value
        await session.commit()
    await call.answer("Цель сохранена")
    await prof_refresh(call)


@router.callback_query(F.data == "prof:pal")
async def prof_pal(call: CallbackQuery):
    cancel_pending_for(call.from_user.id)
    await call.message.edit_text("Выбери уровень активности (PAL):", reply_markup=pal_kb())
    await call.answer()


@router.callback_query(F.data.regexp(r"^(pal[:_])?(\d+(?:\.\d+)?)$"))
async def prof_pal_set(call: CallbackQuery):
    data = call.data
    if ":" in data:
        _, value = data.split(":", 1)
    elif "_" in data:
        _, value = data.split("_", 1)
    else:
        value = data
    try:
        pal_value = float(value)
    except Exception:
        await call.answer("Не понял PAL")
        return
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
        user.pal = pal_value
        await session.commit()
    await call.answer("PAL сохранён")
    await prof_refresh(call)


# ===== Часовой пояс =====

@router.callback_query(F.data == "prof:tz")
async def prof_tz(call: CallbackQuery, state: FSMContext):
    cancel_pending_for(call.from_user.id)
    await call.message.edit_text(
        "Выбери часовой пояс или укажи свой в формате Region/City (например, Asia/Novosibirsk)",
        reply_markup=tz_kb(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("tz:"))
async def prof_tz_pick(call: CallbackQuery, state: FSMContext):
    choice = call.data.split(":", 1)[1]
    if choice == "custom":
        await state.set_state(ProfileForm.tz)
        await call.message.edit_text("Напиши свой часовой пояс, например: Europe/Moscow или Asia/Novosibirsk")
        await call.answer()
        return
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
        await _ensure_tz_column(session)
        await session.execute(text("UPDATE users SET timezone=:tz WHERE id=:id"), {"tz": choice, "id": user.id})
        await session.commit()
    await call.answer("Часовой пояс сохранён")
    await prof_refresh(call)


@router.message(ProfileForm.tz)
async def prof_tz_save(msg: Message, state: FSMContext):
    tz = (msg.text or "").strip()
    if "/" not in tz or len(tz) < 3:
        await msg.answer("Формат должен быть таким: Region/City. Например: Asia/Novosibirsk")
        return
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one()
        await _ensure_tz_column(session)
        await session.execute(text("UPDATE users SET timezone=:tz WHERE id=:id"), {"tz": tz, "id": user.id})
        await session.commit()
    await state.clear()
    await msg.answer("Часовой пояс сохранён.")
    await show_profile(msg)


@router.callback_query(F.data == "prof:help")
async def prof_help(call: CallbackQuery):
    text = (
        "Коротко:\n\n"
        "• BMR — базовый обмен: сколько ккал тратит тело в покое.\n"
        "• PAL — коэффициент активности (1.2 — минимум, 1.9 — очень активно).\n"
        "• TDEE — суточная норма: BMR × PAL.\n\n"
        "Цель:\n"
        "• Похудение — TDEE − 10–20%.\n"
        "• Поддержание — ≈ TDEE.\n"
        "• Набор — TDEE + 10–15%."
    )
    try:
        await call.message.edit_text(text, reply_markup=profile_kb())
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await call.answer()