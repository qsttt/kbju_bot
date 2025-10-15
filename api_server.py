from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.db import get_session
from core.crud import set_premium_until, log_payment
from core.models import User

app = FastAPI()

# -------------------- security --------------------

async def require_admin_token(x_admin_token: Optional[str] = Header(None)) -> None:
    """Простейшая защита админ-хендлеров/вебхуков по токену в заголовке.
    Используем тот же токен, что и для admin dashboard, чтобы не плодить секреты.
    """
    if not settings.admin_dashboard_token:
        raise HTTPException(status_code=500, detail="Admin token is not configured")
    if x_admin_token != settings.admin_dashboard_token:
        raise HTTPException(status_code=403, detail="Forbidden")


# -------------------- helpers --------------------

def _extract_tg_id_from_description(description: str | None) -> Optional[int]:
    """Пытаемся извлечь tg_id из произвольного description.
    Поддерживаем форматы: 'tg:123', 'user:123', просто число '123'.
    """
    if not description:
        return None
    import re
    m = re.search(r"(?:tg|user)[:=]\s*(\d+)", description)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    # если description — просто число
    if description.strip().isdigit():
        try:
            return int(description.strip())
        except ValueError:
            return None
    return None


# -------------------- webhook --------------------

@app.post("/payment/callback")
async def yookassa_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _auth: None = Depends(require_admin_token),
):
    """Вебхук YooKassa.
    Минимальная обработка: логируем платёж и, при успехе, продлеваем премиум.
    Безопасность: защищено заголовком X-Admin-Token.
    """
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = payload.get("event")
    obj: Dict[str, Any] = payload.get("object") or {}
    payment_id: str = obj.get("id") or ""

    amount_raw = obj.get("amount") or {}
    amount_value = amount_raw.get("value")
    currency = amount_raw.get("currency") or "RUB"

    status = obj.get("status") or payload.get("status") or "unknown"
    description = obj.get("description")

    # Найти пользователя
    tg_id = _extract_tg_id_from_description(description)
    if tg_id is None:
        raise HTTPException(status_code=400, detail="Cannot resolve user from description")

    user = (await session.execute(select(User).where(User.tg_id == tg_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Лог платежа
    try:
        value_float = float(str(amount_value)) if amount_value is not None else 0.0
    except ValueError:
        value_float = 0.0

    await log_payment(
        session=session,
        user_id=user.id,
        provider="yookassa",
        amount=value_float,
        currency=currency,
        status=status,
        payment_id=payment_id or "",
    )

    # Простая модель: при успешной оплате продлеваем на 30 дней.
    # Если уже есть premium_until в будущем — прибавляем от него, иначе — от текущего момента.
    if event == "payment.succeeded" or status == "succeeded":
        start_from = user.premium_until if user.premium_until and user.premium_until > datetime.utcnow() else datetime.utcnow()
        await set_premium_until(session, user.id, start_from + timedelta(days=30))

    return {"ok": True}