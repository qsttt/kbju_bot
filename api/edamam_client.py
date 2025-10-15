from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import httpx

from api.translate import ru_en_for_search

log = logging.getLogger("api.edamam_client")

_API_URL = "https://api.edamam.com/api/food-database/v2/parser"


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _has_creds() -> bool:
    return bool(_get("EDAMAM_APP_ID") and _get("EDAMAM_APP_KEY"))


async def lookup_food(session, query_ru: str, method: Optional[str] = None) -> List[Dict]:
    """Return variants from Edamam per 100g.

    We only try: base EN term and optionally one with cooking method appended, to avoid spam.
    """
    if not _has_creds():
        log.info("Edamam: no creds; skip")
        return []

    base_candidates = await ru_en_for_search(query_ru, method)
    # fallback: if no candidates from translator, try naive translit-like simple case by doing nothing
    if not base_candidates:
        base_candidates = []

    queries: List[str] = []
    for en in base_candidates[:2]:
        queries.append(en)
        if method:
            queries.append(f"{en} {method}")

    if not queries:
        log.info("Edamam queries: <none>")
        return []

    log.info("Edamam queries: %s", ", ".join(queries))

    results: List[Dict] = []
    async with httpx.AsyncClient(timeout=20) as client:
        for q in queries:
            try:
                r = await client.get(
                    _API_URL,
                    params={
                        "app_id": _get("EDAMAM_APP_ID"),
                        "app_key": _get("EDAMAM_APP_KEY"),
                        "ingr": q,
                    },
                )
                if r.status_code == 401:
                    log.warning("Edamam HTTP 401 for '%s'", q)
                    break
                r.raise_for_status()
                data = r.json()
                for h in data.get("hints", [])[:5]:
                    food = h.get("food") or {}
                    nutr = food.get("nutrients") or {}
                    title = food.get("label") or q
                    kcal100 = nutr.get("ENERC_KCAL")
                    p100 = nutr.get("PROCNT")
                    f100 = nutr.get("FAT")
                    c100 = nutr.get("CHOCDF")
                    if kcal100 is not None:
                        results.append({
                            "title": title,
                            "kcal100": float(kcal100),
                            "p100": float(p100 or 0),
                            "f100": float(f100 or 0),
                            "c100": float(c100 or 0),
                            "source": "edamam",
                        })
                if results:
                    break
            except Exception as e:
                log.warning("Edamam request failed for '%s': %s", q, e)
                continue

    return results