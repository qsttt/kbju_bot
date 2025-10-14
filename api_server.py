from fastapi import FastAPI, Request, HTTPException
from core.db import SessionLocal
from core.crud import set_premium_until, log_payment
from core.models import User
from sqlalchemy import select
from datetime import datetime, timedelta

app = FastAPI()

@app.post("/payment/callback")
async def yookassa_webhook(request: Request):
    payload = await request.json()
    event = payload.get("event")
    obj = payload.get("object", {})
    payment_id = obj.get("id")
    status = obj.get("status")
    description = obj.get("description", "")

    if event == "payment.succeeded" and status == "succeeded":
        tg_id = None
        if description.startswith("Premium for "):
            tg_id = int(description.split(" ")[-1])
        async with SessionLocal() as session:
            user = (await session.execute(select(User).where(User.tg_id == tg_id))).scalar_one_or_none()
            if not user:
                raise HTTPException(404, "User not found")
            await set_premium_until(session, user.id, datetime.utcnow() + timedelta(days=30))
            await log_payment(session, user.id, amount=float(obj["amount"]["value"]), currency=obj["amount"]["currency"], status=status, payment_id=payment_id)
    return {"ok": True}