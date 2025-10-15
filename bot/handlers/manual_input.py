from __future__ import annotations

import logging
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from sqlalchemy import select

from core.db import SessionLocal
from core.models import User
from core.crud import add_entry, get_daily_summary

from bot.utils.parser import parse_line  # Parsed(..., method)
from bot.keyboards.choices import variants_kb, ask_kcal_kb, cancel_kb
from bot.keyboards.main_menu import main_menu_kb

from api.edamam_client import lookup_food
from api.fdc_client import fdc_lookup
from api.translate import ru_en_for_search

# ✅ Надёжный импорт констант с запасным значением,
# чтобы проект не падал, даже если core/constants.py отсутствует
try:
    from core.constants import MENU_BUTTON_TEXTS as _MENU_BTNS
except Exception:  # файл не найден или иная проблема — используем дефолт
    _MENU_BTNS = {
        "➕ Добавить",
        "📊 Сводка",
        "⭐️ Премиум",
        "👤 Профиль",
        "🏠 В главное меню",
    }

router = Router()
log = logging.getLogger(__name__)

# Временное хранилище контекста (MVP). Для продакшена лучше FSM Storage или БД.
# Структура:
# _pending[user_id] = {
#   "parsed": Parsed,
#   "variants": List[variant],
#   "await_kcal": bool,
#   "await_grams": bool,
# }
_pending: Dict[int, Dict[str, Any]] = {}


# ----------------------- helpers -----------------------

# Встроенные минимальные пресеты на случай отсутствия файла
_EMBEDDED_PRESETS: Dict[str, Dict[str, float]] = {
    # значения на 100 г (приближённо)
    "куриная грудка вареная": {"kcal": 165, "p": 31, "f": 3.6, "c": 0},
    "куриная грудка": {"kcal": 165, "p": 31, "f": 3.6, "c": 0},
    "лосось стейк": {"kcal": 208, "p": 20, "f": 13, "c": 0},
}


def _number_from_text(text: str) -> Optional[float]:
    """Достаёт первое число из текста (180 / 180.5)."""
    m = re.search(r"(\d+[.,]?\d*)", text or "")
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except Exception:
        return None


def _load_presets() -> Dict[str, Dict[str, float]]:
    """Загружает страховочные пресеты (пер 100 г)."""
    base = Path(__file__).resolve().parents[3] / "static" / "cooked_presets.json"
    if base.exists():
        try:
            data = json.loads(base.read_text(encoding="utf-8"))
            # дополним встроенными, не перетирая файл
            for k, v in _EMBEDDED_PRESETS.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(_EMBEDDED_PRESETS)


async def _variants_chain(session, title_ru: str, method: Optional[str]) -> List[Dict[str, Any]]:
    """
    Цепочка поиска: Edamam (через EN-варианты) -> FDC -> Presets.
    Возвращает список вариантов с ключами:
      title, kcal100, p100, f100, c100, source
    """
    log.info("Lookup variants for '%s' (method=%s)...", title_ru, method)

    # 1) Edamam (через принудительный перевод RU→EN внутри edamam_client)
    items = await lookup_food(session, title_ru, method=method)
    log.info("Edamam variants: %d", len(items))
    if items:
        return items

    # 2) FDC (пытаемся теми же EN-вариантами)
    qalts = await ru_en_for_search(title_ru, method)
    log.info("FDC queries (EN-only): %s", ", ".join(qalts) or "<none>")
    found: List[Dict[str, Any]] = []
    for q in qalts:
        f = await fdc_lookup(q)
        if f:
            found = f
            break

    if found:
        return found

    # 3) Presets
    presets = _load_presets()
    key = title_ru.strip().lower()
    # Небольшая эвристика под куриную грудку и метод готовки
    if method in ("boiled", "fried", "baked", "grilled") and "куриная грудка" in key:
        if method == "boiled":
            key = "куриная грудка вареная"
    p = presets.get(key)
    if p:
        log.info("Preset used: %s", key)
        return [{
            "title": key,
            "kcal100": p.get("kcal"),
            "p100": p.get("p"),
            "f100": p.get("f"),
            "c100": p.get("c"),
            "source": "preset",
        }]

    log.info("No variants found for '%s'", title_ru)
    return []


def _format_added_reply(title: str,
                        amount_value: Optional[float],
                        amount_unit: Optional[str],
                        kcal: Optional[float],
                        p: Optional[float],
                        f: Optional[float],
                        c: Optional[float],
                        total_kcal: Optional[float]) -> str:
    parts = [f"✅ <b>{title}</b>"]
    if amount_value:
        parts[0] += f" — {amount_value:g} {amount_unit or ''}".rstrip()
    if kcal is not None:
        parts.append(f"≈ <b>{round(kcal)}</b> ккал")
    if p is not None or f is not None or c is not None:
        parts.append(f"Б {round(p or 0, 1)} / Ж {round(f or 0, 1)} / У {round(c or 0, 1)}")
    if total_kcal is not None:
        parts.append("")
        parts.append(f"Итого сегодня: {round(total_kcal)} ккал")
    return "\n".join(parts)


def cancel_pending_for(user_id: int) -> None:
    try:
        _pending.pop(user_id, None)  # type: ignore[name-defined]
    except Exception:
        pass


# ----------------------- cancel helpers -----------------------

_CANCEL_WORDS = {"отмена", "/cancel", "в меню", "меню", "назад", "выход", "в главное меню"}

async def _cancel_and_back_to_menu(message: Message | CallbackQuery):
    _pending.pop(message.from_user.id, None)
    # Прячем главное меню внутри режимов и показываем при выходе
    if isinstance(message, CallbackQuery):
        try:
            await message.message.edit_text("Окей, выхожу в меню.")
        except Exception:
            pass
        await message.message.answer("Что дальше?", reply_markup=main_menu_kb())
    else:
        await message.answer("Окей, выхожу в меню.", reply_markup=main_menu_kb())


# ----------------------- handlers -----------------------

@router.message(Command("add"))
async def add_prompt(message: Message):
    # Прячем клавиатуру главного меню, чтобы не было ложных нажатий во время ввода
    await message.answer(
        "Введи блюдо и порцию одной строкой: например, \n"
        "<code>куриная грудка варёная 140 г</code> или <code>батончик 180 ккал</code>.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML",
    )


@router.message(F.text.func(lambda t: (t or "").strip().lower() in _CANCEL_WORDS))
async def cancel_add(message: Message):
    await _cancel_and_back_to_menu(message)


@router.callback_query(F.data == "cancel:add")
async def cancel_add_cb(call: CallbackQuery):
    await _cancel_and_back_to_menu(call)


@router.message()
async def catch_manual(message: Message):
    """
    Универсальный ловец — либо создаёт запись сразу (если есть КБЖУ/ккал),
    либо предлагает варианты из баз (Edamam/FDC/Presets), либо просит ввести граммы/ккал.
    Также сюда прилетает ответ пользователя с числом граммов (await_grams) или ккал (await_kcal).
    """
    text = message.text or ""

    # ❗ Никогда не перехватываем клики по кнопкам главного меню
    if text.strip() in _MENU_BTNS:
        return

    if text.strip().lower() in _CANCEL_WORDS:
        await _cancel_and_back_to_menu(message)
        return

    # Проверка отложенного ввода (граммы → ккал)
    ctx = _pending.get(message.from_user.id)

    # --- ждём граммы для порции (когда был ввод в штуках/без единиц) ---
    if ctx and ctx.get("await_grams"):
        grams = _number_from_text(text)
        if grams is None or grams <= 0:
            await message.answer("Пожалуйста, число в граммах, например: 140", reply_markup=cancel_kb())
            return
        parsed = ctx["parsed"]
        parsed.grams = grams
        _pending.pop(message.from_user.id, None)
        # продолжаем обычную обработку ниже с обновлённым parsed
        log.info("User supplied grams: %s", grams)
    # --- ждём ккал для порции ---
    elif ctx and ctx.get("await_kcal"):
        kcal = _number_from_text(text)
        if kcal is None or kcal <= 0:
            await message.answer("Пожалуйста, отправь число, например: 180", reply_markup=ask_kcal_kb(with_cancel=True))
            return

        parsed = ctx["parsed"]
        async with SessionLocal() as session:
            usr = (await session.execute(
                select(User).where(User.tg_id == message.from_user.id)
            )).scalar_one()

            today_utc = datetime.utcnow().date()

            # amount_value: если количество не было задано — используем граммы как количество
            amount_value = parsed.amount_value or (parsed.grams or 1)
            amount_unit = parsed.amount_unit or "г"

            _ = await add_entry(
                session, usr.id,
                on_date=today_utc,
                title=parsed.title,
                amount_value=amount_value,
                amount_unit=amount_unit,
                amount_grams=parsed.grams,
                kcal=kcal, p=None, f=None, c=None,
                is_calories_only=True,
                source="manual",  # фикс ENUM
            )
            summary = await get_daily_summary(session, usr.id, today_utc)

        reply = _format_added_reply(
            parsed.title, amount_value, amount_unit,
            kcal, None, None, None,
            summary.get("kcal")
        )
        await message.answer(reply, reply_markup=main_menu_kb(), parse_mode="HTML")
        log.info("Added calories-only entry: title=%s grams=%s kcal=%s", parsed.title, parsed.grams, kcal)
        _pending.pop(message.from_user.id, None)
        return

    else:
        # Новый ввод — парсим строку
        parsed = parse_line(text)
        log.info(
            "Parsed input: %s -> title=%s grams=%s kcal=%s method=%s",
            text, parsed.title, parsed.grams, parsed.kcal, parsed.method
        )

    # Показать индикатор поиска (и спрятать главную клавиатуру)
    waiting_msg: Optional[Message] = None
    try:
        waiting_msg = await message.answer("Ищу информацию для расчёта КБЖУ…", reply_markup=ReplyKeyboardRemove())
    except Exception:
        pass

    async with SessionLocal() as session:
        usr = (await session.execute(
            select(User).where(User.tg_id == message.from_user.id)
        )).scalar_one()

        today_utc = datetime.utcnow().date()

        # Если пользователь ввёл ккал явно (батончик 180 ккал) — сохраняем сразу
        if parsed.is_cal_only and parsed.kcal is not None and parsed.kcal > 0:
            amount_value = parsed.amount_value or (parsed.grams or 1)
            amount_unit = parsed.amount_unit or "г"

            _ = await add_entry(
                session, usr.id,
                on_date=today_utc,
                title=parsed.title,
                amount_value=amount_value,
                amount_unit=amount_unit,
                amount_grams=parsed.grams,
                kcal=parsed.kcal, p=None, f=None, c=None,
                is_calories_only=True,
                source="manual",  # фикс ENUM
            )
            summary = await get_daily_summary(session, usr.id, today_utc)

            reply = _format_added_reply(
                parsed.title, amount_value, amount_unit,
                parsed.kcal, None, None, None,
                summary.get("kcal")
            )
            if waiting_msg:
                try:
                    await message.bot.delete_message(message.chat.id, waiting_msg.message_id)
                except Exception:
                    pass
            await message.answer(reply, reply_markup=main_menu_kb(), parse_mode="HTML")
            log.info("Added calories-only (inline) entry: title=%s grams=%s kcal=%s", parsed.title, parsed.grams, parsed.kcal)
            return

        # Если граммов нет (например, "7 шт") — спросим массу порции и вернёмся сюда
        if parsed.grams is None:
            if waiting_msg:
                try:
                    await message.bot.delete_message(message.chat.id, waiting_msg.message_id)
                except Exception:
                    pass
            _pending[message.from_user.id] = {
                "parsed": parsed,
                "await_grams": True
            }
            await message.answer("Сколько граммов в этой порции? Напиши число, например: 140", reply_markup=cancel_kb())
            return

        # Нужны варианты (нет явных БЖУ)
        need_variants = (parsed.p is None or parsed.f is None or parsed.c is None)

        if need_variants:
            variants = await _variants_chain(session, parsed.title, parsed.method)

            if variants:
                if waiting_msg:
                    try:
                        await message.bot.delete_message(message.chat.id, waiting_msg.message_id)
                    except Exception:
                        pass
                titles = [v["title"] for v in variants]
                _pending[message.from_user.id] = {
                    "parsed": parsed,
                    "variants": variants,
                    "await_kcal": False,
                }
                await message.answer(
                    "Нашёл несколько вариантов. Выбери подходящий:",
                    reply_markup=variants_kb(titles, with_cancel=True)
                )
                return

            # Вариантов нет — попросим ккал
            if waiting_msg:
                try:
                    await message.bot.delete_message(message.chat.id, waiting_msg.message_id)
                except Exception:
                    pass
            _pending[message.from_user.id] = {
                "parsed": parsed,
                "variants": [],
                "await_kcal": True,
            }
            await message.answer(
                "Не нашёл в базе. Укажи, пожалуйста, сколько ккал в порции?",
                reply_markup=ask_kcal_kb(with_cancel=True)
            )
            return

        # Если всё уже известно — сохраняем как есть
        amount_value = parsed.amount_value or (parsed.grams or 1)
        amount_unit = parsed.amount_unit or "г"

        _ = await add_entry(
            session, usr.id,
            on_date=today_utc,
            title=parsed.title,
            amount_value=amount_value,
            amount_unit=amount_unit,
            amount_grams=parsed.grams,
            kcal=parsed.kcal, p=parsed.p, f=parsed.f, c=parsed.c,
            is_calories_only=parsed.is_cal_only,
            source="manual",
        )
        summary = await get_daily_summary(session, usr.id, today_utc)

    if waiting_msg:
        try:
            await message.bot.delete_message(message.chat.id, waiting_msg.message_id)
        except Exception:
            pass

    reply = _format_added_reply(
        parsed.title, amount_value, amount_unit,
        parsed.kcal, parsed.p, parsed.f, parsed.c,
        summary.get("kcal")
    )
    await message.answer(reply, reply_markup=main_menu_kb(), parse_mode="HTML")
    log.info("Added entry: title=%s grams=%s kcal=%s p=%s f=%s c=%s", parsed.title, parsed.grams, parsed.kcal, parsed.p, parsed.f, parsed.c)


@router.callback_query(F.data.startswith("pick:"))
async def pick_variant(call: CallbackQuery):
    """
    Пользователь выбрал вариант из списка (или 'none').
    Рассчитываем ккал/БЖУ по граммам пользователя на основе данных per 100 г.
    """
    ctx = _pending.get(call.from_user.id)
    if not ctx:
        await call.answer("Сессия устарела")
        return

    idx = call.data.split(":", 1)[1]
    if idx == "none":
        # Просим ккал
        ctx["await_kcal"] = True
        await call.message.edit_text("Хорошо. Тогда укажи, пожалуйста, ккал для порции:", reply_markup=ask_kcal_kb(with_cancel=True))
        await call.answer()
        return

    try:
        i = int(idx)
    except ValueError:
        await call.answer("Ошибка выбора")
        return

    parsed = ctx["parsed"]
    variants = ctx.get("variants", [])
    if i < 0 or i >= len(variants):
        await call.answer("Нет такого варианта")
        return

    variant = variants[i]
    grams = parsed.grams or 0
    ratio = grams / 100.0 if grams else 0

    kcal = (variant.get("kcal100") or 0) * ratio
    p = (variant.get("p100") or 0) * ratio
    f = (variant.get("f100") or 0) * ratio
    c = (variant.get("c100") or 0) * ratio

    async with SessionLocal() as session:
        usr = (await session.execute(
            select(User).where(User.tg_id == call.from_user.id)
        )).scalar_one()
        today_utc = datetime.utcnow().date()

        amount_value = parsed.amount_value or (parsed.grams or 1)
        amount_unit = parsed.amount_unit or "г"

        _ = await add_entry(
            session, usr.id,
            on_date=today_utc,
            title=parsed.title,
            amount_value=amount_value,
            amount_unit=amount_unit,
            amount_grams=parsed.grams,
            kcal=kcal, p=p, f=f, c=c,
            is_calories_only=False,
            source=variant.get("source") or "api",
        )
        summary = await get_daily_summary(session, usr.id, today_utc)

    text = _format_added_reply(
        parsed.title, amount_value, amount_unit,
        kcal, p, f, c,
        summary.get("kcal")
    )
    await call.message.edit_text(text, parse_mode="HTML")
    await call.message.answer("Готово!", reply_markup=main_menu_kb())
    log.info("Added entry from variant: title=%s grams=%s kcal=%s source=%s", parsed.title, parsed.grams, kcal, variant.get("source"))
    _pending.pop(call.from_user.id, None)


@router.callback_query(F.data == "ask:kcal")
async def ask_kcal(call: CallbackQuery):
    """Кнопка 'Указать ккал' → просим число ккал и ждём обычное сообщение."""
    ctx = _pending.get(call.from_user.id)
    if not ctx:
        await call.answer("Сессия устарела")
        return
    ctx["await_kcal"] = True
    await call.message.edit_text("Введи число ккал для этой порции (например, 180):", reply_markup=ask_kcal_kb(with_cancel=True))
    await call.answer()