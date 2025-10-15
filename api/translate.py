from __future__ import annotations

import json
import logging
import os
import re
from typing import List, Optional

import httpx

try:
    from core.config import settings  # type: ignore
except Exception:
    class _S: ...
    settings = _S()  # type: ignore

log = logging.getLogger("api.translate")

# ---------------- helpers -----------------

def _is_latin(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9\W_]+", s or ""))


def _normalize_candidates(cands: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for c in cands:
        if not c:
            continue
        c = c.strip().lower()
        if len(c) < 2:
            continue
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return out[:5]


def _get_bool(name_attr: str, name_env: str, default: bool = False) -> bool:
    val = getattr(settings, name_attr, None)
    if isinstance(val, bool):
        return val
    raw = os.getenv(name_env)
    if raw is not None:
        return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _get_str(name_attr: str, name_env: str, default: str = "") -> str:
    val = getattr(settings, name_attr, None)
    if isinstance(val, str) and val:
        return val
    return os.getenv(name_env, default)


# ---------------- Gemini client -----------------

_DEFAULT_MODEL_CHAIN = [
    _get_str("gemini_model", "GEMINI_MODEL", "gemini-2.5-flash-lite"),
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
]

async def _gemini_candidates(text_ru: str, method: Optional[str]) -> List[str]:
    api_key = _get_str("gemini_api_key", "GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is empty")

    last_err: Optional[Exception] = None

    for model in _DEFAULT_MODEL_CHAIN:
        if not model:
            continue
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                + model
                + ":generateContent?key="
                + api_key
            )
            prompt = {
                "instruction": (
                    "Translate the following Russian food name into English search keywords for nutrition APIs. "
                    "Return strict JSON with the key 'en' containing an array of up to 5 concise options."
                ),
                "text": text_ru,
                "method": method or "",
                "format": {
                    "type": "object",
                    "properties": {"en": {"type": "array", "items": {"type": "string"}}},
                    "required": ["en"],
                },
            }
            payload = {"contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}]}
            async with httpx.AsyncClient(timeout=25) as client:
                r = await client.post(url, json=payload)
                if r.status_code == 404:
                    log.warning("Gemini model '%s' not found (404). Trying next...", model)
                    last_err = RuntimeError(f"404 for model {model}")
                    continue
                r.raise_for_status()
                data = r.json()
            try:
                txt = data["candidates"][0]["content"]["parts"][0]["text"]
                obj = json.loads(txt)
                cands = obj.get("en", [])
            except Exception as parse_err:
                log.error("Gemini parse error on %s: %s", model, parse_err)
                cands = []
            if cands:
                log.info("Gemini model used: %s", model)
                return _normalize_candidates(cands)
        except Exception as e:
            last_err = e
            log.error("Gemini error on %s: %s", model, e)
            continue

    if last_err:
        raise last_err
    return []


# ---------------- Public API -----------------

async def ru_en_for_search(text_ru: str, method: Optional[str] = None) -> List[str]:
    """Return EN candidates for providers.

    Robust to missing core.config settings; uses ENV fallbacks.
    """
    only_en = _get_bool("only_en_for_providers", "ONLY_EN_FOR_PROVIDERS", True)
    use_dict = _get_bool("use_ru_en_dictionary", "USE_RU_EN_DICTIONARY", False)
    use_gem = _get_bool("use_gemini_translation", "USE_GEMINI_TRANSLATION", True)
    gem_key = _get_str("gemini_api_key", "GEMINI_API_KEY")

    log.info(
        "Translate flags: USE_GEMINI_TRANSLATION=%s, USE_RU_EN_DICTIONARY=%s, ONLY_EN_FOR_PROVIDERS=%s, GEMINI_API_KEY=%s",
        use_gem, use_dict, only_en, "set" if gem_key else "<empty>",
    )

    if _is_latin(text_ru):
        return _normalize_candidates([text_ru])

    if only_en and not use_dict and not use_gem:
        log.warning("Both translators disabled while ONLY_EN_FOR_PROVIDERS=true — forcing Gemini once")
        use_gem = True

    # dictionary translation can be added here later

    if use_gem:
        try:
            cands = await _gemini_candidates(text_ru, method)
            if cands:
                return cands
        except Exception as e:
            log.error("Gemini error: %s", e)

    return []