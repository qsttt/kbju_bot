from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.db import get_session
from core.models import User, Payment

router = APIRouter(prefix="/admin")

@router.get("/metrics", response_class=HTMLResponse)
async def metrics(session: AsyncSession = Depends(get_session)):
    users = (await session.execute(select(func.count(User.id)))).scalar() or 0
    active_premium = (await session.execute(select(func.count(User.id)).where(User.premium_until != None))).scalar() or 0
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

@router.get("/trials", response_class=HTMLResponse)
async def trials(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(User.tg_id, User.trial_activated_at).where(User.trial_used==True).order_by(User.trial_activated_at.desc()).limit(50))).all()
    items = ''.join(f"<li>{tg} — {dt}</li>" for tg, dt in rows)
    return HTMLResponse(f"<h2>Последние триалы</h2><ul>{items}</ul>")