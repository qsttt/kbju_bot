from __future__ import annotations

from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from core.db import SessionLocal
from core.models import User
from core.crud import get_daily_summary
from sqlalchemy import select

router = Router()


def summary_kb():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="summary:refresh")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main:menu")],
    ])


async def _summary_text(user: User) -> str:
    today = datetime.utcnow().date()
    async with SessionLocal() as session:
        summary = await get_daily_summary(session, user.id, today)
    kcal = round(summary.get("kcal") or 0)
    p = round(summary.get("p") or 0)
    f = round(summary.get("f") or 0)
    c = round(summary.get("c") or 0)
    lines = [
        "<b>Сводка за сегодня</b>",
        f"Калории: {kcal}",
        f"Б: {p} / Ж: {f} / У: {c}",
    ]
    return "\n".join(lines)


@router.message(F.text.regexp(r"^📊\s*Сводка$"))
async def open_summary(msg: Message):
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == msg.from_user.id))).scalar_one()
    txt = await _summary_text(user)
    await msg.answer(txt, reply_markup=summary_kb(), parse_mode="HTML")


@router.callback_query(F.data == "summary:refresh")
async def summary_refresh(call: CallbackQuery):
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.tg_id == call.from_user.id))).scalar_one()
    txt = await _summary_text(user)
    try:
        await call.message.edit_text(txt, reply_markup=summary_kb(), parse_mode="HTML")
    except Exception:
        await call.message.answer(txt, reply_markup=summary_kb(), parse_mode="HTML")
    await call.answer()