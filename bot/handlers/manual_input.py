# File: bot/handlers/manual_input.py
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards.choices import variants_kb, confirm_add_kb
from bot.keyboards.common import back_home_kb
from core.crud import add_entry
from core.db import async_session_maker
from api.edamam_client import lookup_food
from api.translate import translate_ru_to_en, translate_en_to_ru
from bot.utils.parser import parse_line

router = Router()
log = logging.getLogger(__name__)


@router.message(Command("add"))
@router.message(F.text == "➕ Добавить")
async def start_manual_input(message: Message):
    await message.answer(
        "Введи блюдо и порцию одной строкой: например,\n"
        "куриная грудка варёная 140 г или батончик 180 ккал.",
        reply_markup=back_home_kb(),
    )


@router.message(F.text & ~F.text.in_({"🏠 В главное меню", "❌ Отмена"}))
async def catch_manual(message: Message):
    text = message.text.strip()
    parsed = parse_line(text)
    log.info("Parsed input: %s -> %s", text, parsed)

    await message.answer("🔍 Ищу варианты, подожди...", reply_markup=back_home_kb())

    query_ru = parsed.title
    method = parsed.method

    # Перевод RU→EN для Edamam
    query_en = await translate_ru_to_en(query_ru)
    log.info("Provider queries: RU='%s' -> EN='%s' (only_en=True)", query_ru, query_en)

    # Поиск в Edamam (ограничено до top-5)
    variants = await lookup_food(query_en, method=method, limit=5)
    log.info("Edamam variants: %d", len(variants))

    if not variants:
        await message.answer(
            "Не нашёл в базе. Укажи, сколько ккал в порции (например, 180)",
            reply_markup=back_home_kb(),
        )
        return

    # Перевод EN→RU названий для отображения
    translated_variants: List[Dict[str, Any]] = []
    for v in variants:
        ru_title = await translate_en_to_ru(v.get("title", ""))
        v["title"] = ru_title or v.get("title")
        translated_variants.append(v)

    await message.answer(
        "Нашёл варианты, выбери один:",
        reply_markup=variants_kb(translated_variants, include_ai=True),
    )


@router.callback_query(F.data.startswith("pick:"))
async def pick_variant(call: CallbackQuery):
    await call.answer("Считаю КБЖУ для твоей порции…")

    index = int(call.data.split(":", 1)[1])
    message = call.message
    text = message.reply_to_message.text if message.reply_to_message else None

    parsed = parse_line(text or "")

    # Поиск снова (или можно кэшировать)
    query_en = await translate_ru_to_en(parsed.title)
    variants = await lookup_food(query_en, method=parsed.method, limit=5)
    if not variants or index >= len(variants):
        await call.message.answer("Ошибка: вариант не найден.")
        return

    chosen = variants[index]

    grams = parsed.grams or 100
    kcal = round((chosen["kcal100"] * grams) / 100, 1)
    p = round((chosen["p100"] * grams) / 100, 1)
    f = round((chosen["f100"] * grams) / 100, 1)
    c = round((chosen["c100"] * grams) / 100, 1)

    msg = (
        f"✅ <b>{chosen['title']}</b> — {grams:.0f} г\n"
        f"≈ {kcal} ккал\n"
        f"Б/Ж/У: {p}/{f}/{c}\n\nДобавить в отчёт?"
    )

    await call.message.answer(msg, reply_markup=confirm_add_kb(), parse_mode="HTML")


@router.callback_query(F.data == "variant:ai")
async def pick_ai_variant(call: CallbackQuery):
    await call.answer()
    message = call.message.reply_to_message
    text = message.text if message else None
    if not text:
        await call.message.answer("Не удалось определить запрос.")
        return

    await call.message.answer("🤖 Считаю с помощью ИИ…")

    # Импортируем здесь, чтобы не тянуть лишнее при обычной работе
    from api.translate import translate_ru_to_en, translate_en_to_ru
    import httpx

    query_ru = parse_line(text).title
    query_en = await translate_ru_to_en(query_ru)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            f"Estimate nutrition (kcal, proteins, fats, carbs per 100g) "
                            f"for: {query_en}. Return JSON: {{'title': name, 'kcal100':, 'p100':, 'f100':, 'c100':}}"
                        )
                    }
                ],
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.gemini_api_key,
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            text_out = str(data)
    except Exception as e:
        await call.message.answer(f"Ошибка Gemini: {e}")
        return

    # Парсинг JSON из текста Gemini
    import json, re

    try:
        match = re.search(r"\{.*?\}", text_out, re.S)
        parsed = json.loads(match.group(0)) if match else {}
    except Exception:
        parsed = {}

    if not parsed:
        await call.message.answer("Не удалось получить данные от ИИ.")
        return

    ru_title = await translate_en_to_ru(parsed.get("title", query_en))
    grams = parse_line(text).grams or 100
    kcal = round((parsed.get("kcal100", 0) * grams) / 100, 1)
    p = round((parsed.get("p100", 0) * grams) / 100, 1)
    f = round((parsed.get("f100", 0) * grams) / 100, 1)
    c = round((parsed.get("c100", 0) * grams) / 100, 1)

    msg = (
        f"🤖 <b>{ru_title}</b> — {grams:.0f} г\n"
        f"≈ {kcal} ккал\n"
        f"Б/Ж/У: {p}/{f}/{c}\n\nДобавить в отчёт?"
    )
    await call.message.answer(msg, reply_markup=confirm_add_kb(), parse_mode="HTML")


@router.callback_query(F.data == "confirm:add")
async def confirm_add(call: CallbackQuery):
    message = call.message.reply_to_message
    text = message.text if message else None
    if not text:
        await call.message.answer("Не удалось определить, что добавлять.")
        return

    parsed = parse_line(text)

    async with async_session_maker() as session:
        await add_entry(
            session,
            user_id=call.from_user.id,
            title=parsed.title,
            grams=parsed.grams,
            kcal=parsed.kcal,
            source="manual",
        )

    await call.message.answer("✅ Добавлено в отчёт!", reply_markup=back_home_kb())


@router.callback_query(F.data == "confirm:other")
async def confirm_other(call: CallbackQuery):
    await call.answer("Хорошо, покажу другие варианты…")
    message = call.message.reply_to_message
    if not message:
        await call.message.answer("Не найден предыдущий запрос.")
        return

    parsed = parse_line(message.text)
    query_en = await translate_ru_to_en(parsed.title)
    variants = await lookup_food(query_en, method=parsed.method, limit=5)

    translated_variants: List[Dict[str, Any]] = []
    for v in variants:
        ru_title = await translate_en_to_ru(v.get("title", ""))
        v["title"] = ru_title or v.get("title")
        translated_variants.append(v)

    await call.message.answer(
        "Вот другие варианты:",
        reply_markup=variants_kb(translated_variants, include_ai=True),
    )
