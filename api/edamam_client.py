from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import FoodCache, FoodDictionary
from api.translate import ru_en_for_search

log = logging.getLogger(__name__)

EDAMAM_URL = "https://api.edamam.com/api/food-database/v2/parser"


def _normalize_key(title: str) -> str:
    t = (title or "").strip().lower()
    for ch in ",()[];:":
        t = t.replace(ch, " ")
    t = " ".join(t.split())
    return t.replace(" ", "_")


async def _cache_get(session: AsyncSession, key: str) -> Optional[dict]:
    if os.getenv("DISABLE_FOOD_CACHE", "false").lower() == "true":
        return None
    row = await session.get(FoodCache, key)
    if row and row.ttl_until and row.ttl_until > datetime.utcnow():
        try:
            return json.loads(row.json_payload)
        except Exception:
            return None
    return None


async def _cache_set(session: AsyncSession, key: str, payload: dict, ttl_hours: int = 48) -> None:
    if os.getenv("DISABLE_FOOD_CACHE", "false").lower() == "true":
        return
    expires = datetime.utcnow() + timedelta(hours=ttl_hours)
    data = json.dumps(payload, ensure_ascii=False)
    row = await session.get(FoodCache, key)
    if row:
        row.json_payload = data
        row.ttl_until = expires
    else:
        session.add(FoodCache(food_key=key, json_payload=data, ttl_until=expires))
    await session.commit()


def _cook_score(title: str) -> int:
    t = (title or "").lower()
    return sum(tag in t for tag in ["cooked", "boiled", "baked", "fried", "grilled"])


async def _edamam_query(q: str, app_id: str, app_key: str) -> List[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(
                EDAMAM_URL,
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "ingr": q,
                    "nutrition-type": "cooking",
                },
            )
            if r.status_code != 200:
                log.warning("Edamam HTTP %s for '%s': %s", r.status_code, q, r.text[:200])
                return []
            data = r.json()
            out: List[Dict[str, Any]] = []
            for it in (data.get("parsed", []) + data.get("hints", []))[:5]:
                food = it.get("food", {}) or {}
                n = food.get("nutrients", {}) or {}
                title = food.get("label") or q
                out.append({
                    "title": title,
                    "kcal100": n.get("ENERC_KCAL"),
                    "p100": n.get("PROCNT"),
                    "f100": n.get("FAT"),
                    "c100": n.get("CHOCDF"),
                    "source": "api",
                })
            return out
    except Exception as e:
        log.warning("Edamam request failed for '%s': %s", q, e)
        return []


async def lookup_food(session: AsyncSession, query_ru: str, method: Optional[str] = None) -> List[Dict[str, Any]]:
    if not (query_ru or "").strip():
        return []

    norm_key = _normalize_key(query_ru)

    # 1) локальный словарь
    local = await session.execute(select(FoodDictionary).where(FoodDictionary.food_key == norm_key))
    row = local.scalar_one_or_none()
    if row:
        return [{
            "title": row.title_ru,
            "kcal100": row.per_100g_kcal,
            "p100": row.per_100g_p,
            "f100": row.per_100g_f,
            "c100": row.per_100g_c,
            "source": "seed",
        }]

    # 2) кэш
    cached = await _cache_get(session, norm_key)
    if cached:
        return cached.get("items", [])

    # 3) формируем EN-кандидаты
    base_candidates = await ru_en_for_search(query_ru, method)
    if not base_candidates:
        log.info("Edamam queries: <none>")
        return []

    # 4) расширяем кандидатами способа готовки
    COOK_ALTS = [
        " cooked",
        " cooked, boiled",
        " boiled",
        " grilled",
        " baked",
        " fried",
    ]
    queries: List[str] = []
    for b in base_candidates:
        queries.append(b)
        for suff in COOK_ALTS:
            queries.append(b + suff)

    # уникализация с сохранением порядка
    seen = set(); qlist: List[str] = []
    for q in queries:
        q = q.strip()
        if q and q not in seen:
            seen.add(q); qlist.append(q)

    log.info("Edamam queries: %s", ", ".join(qlist)[:500])

    app_id = os.getenv("EDAMAM_APP_ID")
    app_key = os.getenv("EDAMAM_APP_KEY")

    items: List[Dict[str, Any]] = []
    for q in qlist:
        chunk = await _edamam_query(q, app_id, app_key)
        if chunk:
            chunk.sort(key=lambda x: _cook_score(x["title"]), reverse=True)
            items = chunk
            break

    if items:
        await _cache_set(session, norm_key, {"items": items}, ttl_hours=48)
    return items