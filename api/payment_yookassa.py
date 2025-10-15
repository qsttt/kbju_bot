import base64, uuid
import httpx
from core.config import settings

API_URL = "https://api.yookassa.ru/v3/payments"

async def create_payment(amount: int, description: str, return_url: str = "https://t.me"):
    auth_str = f"{settings.yookassa_shop_id}:{settings.yookassa_secret_key}".encode()
    headers = {
        "Authorization": "Basic " + base64.b64encode(auth_str).decode(),
        "Idempotence-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    payload = {
        "amount": {"value": f"{amount}.00", "currency": "RUB"},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": description,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(API_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["confirmation"]["confirmation_url"], data["id"]