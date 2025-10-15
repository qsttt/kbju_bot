from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from core.config import settings

log = logging.getLogger(__name__)

_METHOD_HINTS = {
    "boiled": ["boiled", "cooked"],
    "fried": ["fried", "pan-fried", "sauteed"],
    "grilled": ["grilled"],
    "baked": ["baked", "roasted"],
}

_NEGATIVE_TERMS = [
    "raw", "skin", "wings", "wing", "breaded", "smoked", "marinated"
]


def _hinted_query(query_en: str, method: Optional[str]) -> str:
    base = query_en.strip()
    if method and method in _METHOD_HINTS:
        return base + " " + " ".join(_METHOD_HINTS[method])
    return base


def _score_label(label: str, query_en: str, method: Optional[str]) -> int:
    """Эвристический скоринг под наш UX."""
    l = label.lower()
    q = (query_en or "").lower()
    score = 0
    # ближе к запросу — выше
    if q and q in l:
        score += 3
    # способ готовки
    if method:
        for w in _METHOD_HINTS.get(method, []):
            if w in l:
                score += 3
    # отрицательные термины — понижаем
    for bad in _NEGATIVE_TERMS:
        if bad in l:
            score -= 3
    return score


async def lookup_food(query_ru: str, method: Optional[str] = None, *, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Поиск вариантов продукта в Edamam Food Database.
    Возвращает список словарей c ключами: title, kcal100, p100, f100, c100, source="api".
    В случае отсутствия кредов/ошибки — [] без исключений.
    """
    app_id = settings.edamam_app_id
    app_key = settings.edamam_app_key
    if not app_id or not app_key:
        log.info("Edamam: no creds; skip")
        return []

    query = _hinted_query(query_ru, method)

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "ingr": query,
        "category": "generic-foods",
    }
    url = "https://api.edamam.com/api/food-database/v2/parser?" + urlencode(params)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0)) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        log.warning("Edamam request error: %s", e)
        return []

    hints = data.get("hints") or []
    rows: List[Dict[str, Any]] = []

    for h in hints:
        food = (h or {}).get("food") or {}
        label = food.get("label") or ""
        if not label:
            continue
        nutrients = food.get("nutrients") or {}
        kcal = float(nutrients.get("ENERC_KCAL") or 0)
        p = float(nutrients.get("PROCNT") or 0)
        f = float(nutrients.get("FAT") or 0)
        c = float(nutrients.get("CHOCDF") or 0)
        rows.append({
            "title": label,
            "kcal100": round(kcal, 2),
            "p100": round(p, 2),
            "f100": round(f, 2),
            "c100": round(c, 2),
            "source": "api",
            "_score": _score_label(label, query_ru, method),
        })

    # сортировка по убыванию score и обрезка
    rows.sort(key=lambda x: x.get("_score", 0), reverse=True)

    # Сильный фильтр по способу готовки: если указан и есть варианты с нужным словом — оставляем преимущественно их
    if method:
        req_words = set(_METHOD_HINTS.get(method, []))
        preferred = [r for r in rows if any(w in (r.get("title") or "").lower() for w in req_words)]
        others = [r for r in rows if r not in preferred]
        rows = preferred + others

    # финальный срез и удаление служебного поля
    out: List[Dict[str, Any]] = []
    for r in rows[:limit]:
        r.pop("_score", None)
        out.append(r)

    return out