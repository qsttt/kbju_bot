from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from core.config import settings

log = logging.getLogger(__name__)

_METHOD_HINTS = {
    "boiled": ["boiled", "cooked"],
    "fried": ["fried", "pan fried"],
    "grilled": ["grilled"],
    "baked": ["baked", "roasted"],
}


def _hinted_query(query_ru: str, method: Optional[str]) -> str:
    base = query_ru.strip()
    if method and method in _METHOD_HINTS:
        return base + " " + " ".join(_METHOD_HINTS[method])
    return base


async def lookup_food(query_ru: str, method: Optional[str] = None, *, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Поиск по USDA FDC. Возвращает такой же формат, как edamam_client.lookup_food().
    При отсутствии API-ключа или ошибке возвращает пустой список.
    """
    api_key = settings.fdc_api_key
    if not api_key:
        log.info("FDC: no API key; skip")
        return []

    query = _hinted_query(query_ru, method)
    params = {
        "query": query,
        "pageSize": str(limit * 2),  # возьмём чуть больше и отфильтруем
        "api_key": api_key,
    }
    url = "https://api.nal.usda.gov/fdc/v1/foods/search?" + urlencode(params)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0)) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        log.warning("FDC request error: %s", e)
        return []

    foods = data.get("foods") or []
    out: List[Dict[str, Any]] = []
    for food in foods:
        label = food.get("description") or ""
        if not label:
            continue
        # FDC nutrients могут приходить в разных полях; попробуем из foodNutrients
        nutrients = {n.get("nutrientName"): n.get("value") for n in (food.get("foodNutrients") or [])}
        kcal = float(nutrients.get("Energy", 0) or 0)
        p = float(nutrients.get("Protein", 0) or 0)
        f = float(nutrients.get("Total lipid (fat)", 0) or 0)
        c = float(nutrients.get("Carbohydrate, by difference", 0) or 0)
        out.append({
            "title": label,
            "kcal100": round(kcal, 2),
            "p100": round(p, 2),
            "f100": round(f, 2),
            "c100": round(c, 2),
            "source": "api",
        })
        if len(out) >= limit:
            break

    return out