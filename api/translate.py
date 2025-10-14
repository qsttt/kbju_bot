from __future__ import annotations
import os
import re
import json
import httpx
from typing import Optional, List, Tuple
import logging

log = logging.getLogger(__name__)

# Мини-словарь — выключается/включается ENV-флагом USE_RU_EN_DICTIONARY
RU_EN = {
    "куриная грудка": "chicken breast",
    "грудка куриная": "chicken breast",
    "куриная грудка филе": "chicken breast fillet",
    "стейк говяжий": "beef steak",
    "говяжий стейк": "beef steak",
    "стейк": "beef steak",
    "фарш говяжий": "ground beef",
    "фарш куриный": "ground chicken",
    "наггетсы": "chicken nuggets",
    "нагетсы": "chicken nuggets",
    "гречка": "buckwheat",
    "гречка вареная": "buckwheat, cooked",
    "творог": "cottage cheese",
    "рис": "rice",
    "рис вареный": "rice, cooked",
}

METHOD_EN = {
    None: "",
    "raw": "raw",
    "boiled": "cooked, boiled",
    "fried": "cooked, fried",
    "baked": "cooked, baked",
    "grilled": "grilled",
}

MODEL = "gemini-2.5-flash-lite"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def _clean_json_block(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    s = text.find("{"); e = text.rfind("}")
    if s != -1 and e != -1 and e > s:
        return text[s:e+1]
    return text


def _safe_json_loads(maybe_json: str):
    try:
        return json.loads(maybe_json)
    except Exception:
        return None


async def _gemini_translate(text_ru: str, method: str | None) -> Optional[str]:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        log.warning("Gemini: no API key in env")
        return None

    method_hint = METHOD_EN.get(method, "").strip()
    instruction = (
        "You are a translator for nutrition database queries.\n"
        "Task: Translate the Russian food phrase into a concise English food name suitable for nutrition lookup.\n"
        "Rules:\n"
        "1) Return STRICT JSON ONLY with a single key 'en'.\n"
        "2) No commentary, no extra keys, no trailing text.\n"
        "3) Lowercase, concise, generic food name (e.g., 'chicken breast', 'beef steak').\n"
        "4) If a cooking method is implied, append a short qualifier (e.g., 'cooked, boiled').\n"
        "5) Do not include quantities or units.\n"
        "Examples:\n"
        "Input: \"куриная грудка 160 г\" -> {\"en\":\"chicken breast\"}\n"
        "Input: \"куриная грудка варёная\" -> {\"en\":\"chicken breast cooked, boiled\"}\n"
        "Input: \"стейк говяжий\" -> {\"en\":\"beef steak\"}\n"
    )

    text_line = (text_ru or "").strip().lower()
    if method_hint:
        text_line = f"{text_line} ({method_hint})"

    prompt = instruction + f"\nInput: \"{text_line}\""

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "topP": 0.8},
    }

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.post(GEMINI_URL, params={"key": key}, json=body)
            if r.status_code != 200:
                log.warning("Gemini HTTP %s: %s", r.status_code, r.text[:200])
                return None
            data = r.json()
    except Exception as e:
        log.warning("Gemini request failed: %s", e)
        return None

    text = ((data.get("candidates") or [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip())
    if not text:
        log.warning("Gemini empty text for '%s'", text_ru)
        return None

    cleaned = _clean_json_block(text)
    j = _safe_json_loads(cleaned)
    if j and isinstance(j, dict) and isinstance(j.get("en"), str):
        val = j["en"].strip()
        log.info("Gemini OK: %s -> %s", text_ru, val)
        return val or None

    # иногда модель шлёт просто строку
    s = text.strip().strip('"').strip("'")
    if s:
        log.info("Gemini (raw str): %s -> %s", text_ru, s)
        return s

    log.warning("Gemini parse failed for '%s': %s", text_ru, text[:120])
    return None


async def ru_en_for_search(text_ru: str, method: str | None = None) -> List[str]:
    """Возвращает список EN-кандидатов (1–5) в порядке приоритета.
    Источники: Gemini → (опционально) словарь → эвристика. RU добавляется только если ONLY_EN_FOR_PROVIDERS=false.
    В логах: флаги, наличие ключа и источники.
    """
    base_ru = (text_ru or "").strip().lower()

    use_gemini = os.getenv("USE_GEMINI_TRANSLATION", "false").lower() == "true"
    use_dict = os.getenv("USE_RU_EN_DICTIONARY", "false").lower() == "true"
    only_en = os.getenv("ONLY_EN_FOR_PROVIDERS", "true").lower() in ("true", "1", "yes")
    key_set = bool(os.getenv("GEMINI_API_KEY"))

    log.info(
        "Translate flags: USE_GEMINI_TRANSLATION=%s, USE_RU_EN_DICTIONARY=%s, ONLY_EN_FOR_PROVIDERS=%s, GEMINI_API_KEY=%s",
        use_gemini, use_dict, only_en, "set" if key_set else "missing",
    )

    out: List[Tuple[str, str]] = []  # (query, origin)

    if use_gemini:
        t = await _gemini_translate(base_ru, method)
        if t:
            out.append((t, "gemini"))

    if use_dict and base_ru in RU_EN:
        out.append((RU_EN[base_ru], "dict"))

    m = METHOD_EN.get(method, "").strip()
    if m:
        out.append((f"{base_ru} {m}", "heuristic"))

    if not only_en:
        out.append((base_ru, "ru"))

    # уникализация
    seen, uniq, labeled = set(), [], []
    for q, origin in out:
        q = (q or "").strip()
        if q and q not in seen:
            seen.add(q); uniq.append(q); labeled.append(f"{q} [{origin}]")

    log.info("Translate '%s' -> candidates: %s", base_ru, "; ".join(labeled) or "<none>")
    return uniq[:5]