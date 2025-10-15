from __future__ import annotations

import logging
import re
from typing import Optional

import httpx

from core.config import settings

log = logging.getLogger(__name__)


async def translate_ru_to_en(text: str) -> str:
    """Перевод RU->EN через Gemini API (если включено)."""
    text = text.strip()
    if not text:
        return text

    if not settings.use_gemini_translate or not settings.gemini_api_key:
        log.info("Gemini translation disabled or missing key; return input")
        return text

    try:
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"Translate into concise English: {text}"}],
                }
            ]
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0)) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        candidates = data.get("candidates") or []
        for c in candidates:
            parts = (((c or {}).get("content") or {}).get("parts")) or []
            for p in parts:
                if t := p.get("text"):
                    return t.strip()
    except Exception as e:
        log.warning("Gemini translate_ru_to_en error: %s", e)

    return text


async def translate_en_to_ru(text: str) -> str:
    """Перевод EN->RU через Gemini API с постобработкой результата."""
    text = text.strip()
    if not text:
        return text

    if not settings.use_gemini_translate or not settings.gemini_api_key:
        return text

    try:
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"Translate the following food name into Russian, concise form, no commentary: {text}"}],
                }
            ]
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0)) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        candidates = data.get("candidates") or []
        for c in candidates:
            parts = (((c or {}).get("content") or {}).get("parts")) or []
            for p in parts:
                if t := p.get("text"):
                    return _sanitize_ru(t)
    except Exception as e:
        log.warning("Gemini translate_en_to_ru error: %s", e)

    return text


def _sanitize_ru(raw: str) -> str:
    """Чистим от лишнего и форматируем под короткое RU-название."""
    t = raw.strip()
    t = re.sub(r"\*+", "", t)  # убираем **
    t = re.sub(r"Вот перевод.*?:", "", t, flags=re.I)
    t = re.sub(r"^[-: ]+", "", t)
    t = re.sub(r"\s+", " ", t)
    if len(t) > 80:
        t = t[:77] + "..."
    return t.strip().capitalize()


# Алиас для старого кода
translate_ru_en = translate_ru_to_en
ru_en_for_search = translate_ru_to_en