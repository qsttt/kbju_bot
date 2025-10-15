from __future__ import annotations
from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from core.db import SessionLocal
from core.crud import get_or_create_user

DEFAULT_TZ = "Europe/Moscow"

class EnsureUserMiddleware(BaseMiddleware):
    """Гарантирует, что запись о пользователе есть в БД до обработки любого апдейта.

    Покрывает Message и CallbackQuery. Если пользователь отсутствует — создаёт его.
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        tg_user_id: int | None = None

        if isinstance(event, Message) and event.from_user:
            tg_user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            tg_user_id = event.from_user.id

        if tg_user_id is not None:
            # Сигнатура get_or_create_user(session, tg_id) — без передачи tz
            # Поле tz в модели имеет дефолт, поэтому пользователь создастся корректно
            async with SessionLocal() as session:
                await get_or_create_user(session, tg_user_id)

        return await handler(event, data)