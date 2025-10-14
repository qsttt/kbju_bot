from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from core.db import SessionLocal
from core.models import User
from bot.keyboards.profile import profile_kb, sex_kb, goal_kb, pal_kb
from bot.utils.calcs import calc_bmr, calc_tdee, calc_targets

router = Router()

class ProfileForm(StatesGroup):
    weight = State()
    height = State()
    age = State()

def _profile_text(u: User) -> str:
    return (
        f"Ваш профиль:\n"
        f"Пол: {u.sex or '-'}\n"
        f"Возраст: {u.age or '-'}\n"
        f"Рост: {u.height_cm or '-'} см\n"
        f"Вес: {u.weight_kg or '-'} кг\n\n"
        f"Цель: {u.goal or '-'}\n"
        f"PAL: {u.pal or '-'}\n"
    )

@router.message(F.text == "⚙️ Профиль")
async def show_profile(msg: Message):
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one_or_none()
    if not u:
        await msg.answer("Профиль не найден. Используйте /start.")
        return
    await msg.answer(_profile_text(u), reply_markup=profile_kb())

# ---- numeric editors ----

@router.callback_query(F.data == "prof:weight")
async def edit_weight(call: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileForm.weight)
    await call.message.edit_text("Введите новый вес (кг), например: 72.5")

@router.message(ProfileForm.weight)
async def save_weight(msg: Message, state: FSMContext):
    try:
        val = float(msg.text.replace(",", "."))
    except Exception:
        await msg.answer("Пожалуйста, число, например 72.5")
        return
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one()
        u.weight_kg = val
        await session.commit()
    await state.clear()
    await show_profile(msg)

@router.callback_query(F.data == "prof:height")
async def edit_height(call: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileForm.height)
    await call.message.edit_text("Введите рост (см), например: 180")

@router.message(ProfileForm.height)
async def save_height(msg: Message, state: FSMContext):
    try:
        val = float(msg.text.replace(",", "."))
    except Exception:
        await msg.answer("Пожалуйста, число, например 180")
        return
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one()
        u.height_cm = val
        await session.commit()
    await state.clear()
    await show_profile(msg)

@router.callback_query(F.data == "prof:age")
async def edit_age(call: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileForm.age)
    await call.message.edit_text("Введите возраст (полных лет), например: 28")

@router.message(ProfileForm.age)
async def save_age(msg: Message, state: FSMContext):
    try:
        val = int(float(msg.text.replace(",", ".")))
    except Exception:
        await msg.answer("Пожалуйста, целое число, например 28")
        return
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one()
        u.age = val
        await session.commit()
    await state.clear()
    await show_profile(msg)

# ---- toggles ----

@router.callback_query(F.data == "prof:sex")
async def pick_sex(call: CallbackQuery):
    await call.message.edit_text("Выберите пол:", reply_markup=sex_kb())

@router.callback_query(F.data.startswith("sex:"))
async def set_sex(call: CallbackQuery):
    sex = call.data.split(":", 1)[1]
    if sex not in ("M", "F"):
        await call.answer("Некорректное значение")
        return
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
        u.sex = sex
        await session.commit()
    await call.message.edit_text("Пол обновлён.")
    await show_profile(call.message)

@router.callback_query(F.data == "prof:goal")
async def pick_goal(call: CallbackQuery):
    await call.message.edit_text("Выберите цель:", reply_markup=goal_kb())

@router.callback_query(F.data.startswith("goal:"))
async def set_goal(call: CallbackQuery):
    goal = call.data.split(":", 1)[1]
    if goal not in ("loss", "maintain", "gain"):
        await call.answer("Некорректное значение")
        return
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
        u.goal = goal
        await session.commit()
    await call.message.edit_text("Цель обновлена.")
    await show_profile(call.message)

@router.callback_query(F.data == "prof:pal")
async def pick_pal(call: CallbackQuery):
    await call.message.edit_text("Выберите активность (PAL):", reply_markup=pal_kb())

@router.callback_query(F.data.startswith("pal:"))
async def set_pal(call: CallbackQuery):
    try:
        pal = float(call.data.split(":", 1)[1])
    except Exception:
        await call.answer("Некорректное значение")
        return
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
        u.pal = pal
        await session.commit()
    await call.message.edit_text("PAL обновлён.")
    await show_profile(call.message)

# ---- recalc ----

@router.callback_query(F.data == "prof:recalc")
async def recalc_norms(call: CallbackQuery):
    async with SessionLocal() as session:
        u = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
        # базовый расчёт
        bmr = calc_bmr(sex=u.sex, weight=u.weight_kg, height=u.height_cm, age=u.age)
        tdee = calc_tdee(bmr, pal=u.pal or 1.2)
        targets = calc_targets(tdee, goal=u.goal or "maintain")
    txt = (
        "Пересчёт норм:\n"
        f"BMR: {round(bmr)} ккал\n"
        f"TDEE: {round(tdee)} ккал\n"
        f"Целевые КБЖУ: {round(targets['kcal'])} ккал, "
        f"Б {round(targets['p'],1)} / Ж {round(targets['f'],1)} / У {round(targets['c'],1)}\n"
    )
    await call.message.edit_text(txt, reply_markup=profile_kb())

@router.callback_query(F.data == "prof:back")
async def prof_back(call: CallbackQuery):
    await show_profile(call.message)

@router.callback_query(F.data == "prof:close")
async def prof_close(call: CallbackQuery):
    await call.message.edit_text("Настройки профиля закрыты.")
