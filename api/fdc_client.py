from __future__ import annotations

import logging
import os
from typing import Dict, List

import httpx

log = logging.getLogger("api.fdc_client")

_API = "https://api.nal.usda.gov/fdc/v1/foods/search"


def _key() -> str:
    return os.getenv("FDC_API_KEY", "")


async def fdc_lookup(query_en: str) -> List[Dict]:
    key = _key()
    if not key:
        log.info("FDC: API key: <empty>; skip")
        return []

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(_API, params={"api_key": key, "query": query_en, "pageSize": 10})
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        log.warning("FDC request failed for '%s': %s", query_en, e)
        return []

    out: List[Dict] = []
    for it in data.get("foods", [])[:5]:
        nutr = {n.get("nutrientName"): n.get("value") for n in it.get("foodNutrients", [])}
        kcal100 = nutr.get("Energy") or nutr.get("Energy (Atwater General Factors)")
        p100 = nutr.get("Protein")
        f100 = nutr.get("Total lipid (fat)")
        c100 = nutr.get("Carbohydrate, by difference")
        if kcal100 is None:
            continue
        out.append({
            "title": it.get("description") or query_en,
            "kcal100": float(kcal100),
            "p100": float(p100 or 0),
            "f100": float(f100 or 0),
            "c100": float(c100 or 0),
            "source": "fdc",
        })
    return out