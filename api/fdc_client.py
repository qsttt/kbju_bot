from __future__ import annotations
from typing import Any, Dict, List
import os
import httpx
import logging

log = logging.getLogger(__name__)

FDC_SEARCH = "https://api.nal.usda.gov/fdc/v1/foods/search"


async def fdc_lookup(query_en: str) -> List[Dict[str, Any]]:
    key = os.getenv("FDC_API_KEY")
    if not key:
        log.info("FDC: no API key; skip")
        return []
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(FDC_SEARCH, params={
                "api_key": key,
                "query": query_en,
                "pageSize": 5,
                "dataType": "Survey (FNDDS), SR Legacy, Branded",
            })
            if r.status_code != 200:
                log.warning("FDC HTTP %s for '%s': %s", r.status_code, query_en, r.text[:200])
                return []
            data = r.json()
            items = []
            for it in data.get("foods", [])[:5]:
                # nutrients — список словарей с nutrientName/value
                nmap = {x.get("nutrientName"): x.get("value") for x in it.get("foodNutrients", [])}
                title = it.get("description")
                kcal = nmap.get("Energy") or nmap.get("Energy (Atwater General Factors)")
                p = nmap.get("Protein")
                f = nmap.get("Total lipid (fat)")
                c = nmap.get("Carbohydrate, by difference")
                items.append({
                    "title": title,
                    "kcal100": kcal,
                    "p100": p,
                    "f100": f,
                    "c100": c,
                    "source": "fdc",
                })
            log.info("FDC '%s' -> %d items", query_en, len(items))
            return items
    except Exception as e:
        log.warning("FDC request failed for '%s': %s", query_en, e)
        return []