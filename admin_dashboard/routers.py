from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.config import settings
from core.db import get_session
from core.models import User, Payment

router = APIRouter(prefix="/admin")

# -------------------- security --------------------

async def _require_admin(x_admin_token: str | None = Header(None)) -> None:
    if not settings.admin_dashboard_token:
        raise HTTPException(status_code=500, detail="Admin token is not configured")
    if x_admin_token != settings.admin_dashboard_token:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/metrics", response_class=HTMLResponse, dependencies=[Depends(_require_admin)])
async def metrics(session: AsyncSession = Depends(get_session)):
    users = (await session.execute(select(func.count(User.id)))).scalar() or 0
    active_premium = (
        await session.execute(select(func.count(User.id)).where(User.premium_until != None))
    ).scalar() or 0
    payments_count = (await session.execute(select(func.count(Payment.id)))).scalar() or 0

    html = f"""
    <h2>Метрики</h2>
    <ul>
      <li>Пользователи: {users}</li>
      <li>Активные премиум: {active_premium}</li>
      <li>Платежей всего: {payments_count}</li>
    </ul>
    """
    return HTMLResponse(html)


@router.get("/trials", response_class=HTMLResponse, dependencies=[Depends(_require_admin)])
async def trials(session: AsyncSession = Depends(get_session)):
    """Показываем последние 50 премиум-активаций по дате premium_until.
    Т.к. полей trial_* в модели пока нет, используем доступные данные.
    """
    rows = (
        await session.execute(
            select(User.tg_id, User.premium_until)
            .where(User.premium_until != None)
            .order_by(User.premium_until.desc())
            .limit(50)
        )
    ).all()

    if not rows:
        return HTMLResponse("<h2>Последние премиум-активации</h2><p>Нет данных</p>")

    items = "".join(
        f"<li>{tg_id} — {dt.strftime('%Y-%m-%d %H:%M:%S') if dt else ''}</li>" for tg_id, dt in rows
    )
    return HTMLResponse(f"<h2>Последние премиум-активации</h2><ul>{items}</ul>")