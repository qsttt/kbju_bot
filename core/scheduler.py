import asyncio
from datetime import datetime
import pytz
from sqlalchemy import select
from core.db import SessionLocal
from core.models import User

async def scheduler_loop():
    while True:
        now_utc = datetime.utcnow()
        async with SessionLocal() as session:
            users = (await session.execute(select(User))).scalars().all()
            for u in users:
                try:
                    tz = pytz.timezone(u.tz or "Europe/Moscow")
                except Exception:
                    tz = pytz.timezone("Europe/Moscow")
                local = pytz.utc.localize(now_utc).astimezone(tz)
                if local.hour == 0 and local.minute < 5:
                    # сюда поместим отправку сводки и переход на новый день
                    pass
        await asyncio.sleep(60)

if u.premium_until:
    local = pytz.utc.localize(now_utc).astimezone(tz)
    # за 3 дня
    if 0 <= (u.premium_until - now_utc).days == 3 and local.hour == 10:
        # отправить мягкое напоминание через бот
        pass
    # за 1 день
    if 0 <= (u.premium_until - now_utc).days == 1 and local.hour == 10:
        pass