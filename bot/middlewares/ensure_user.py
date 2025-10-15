# File: bot/middlewares/ensure_user.py
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
    Это защищает все хендлеры от NoResultFound на select(User)...scalar_one().
    """
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        tg_user_id = None
        if isinstance(event, Message) and event.from_user:
            tg_user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            tg_user_id = event.from_user.id

        if tg_user_id is not None:
            async with SessionLocal() as session:
                await get_or_create_user(session, tg_user_id, DEFAULT_TZ)
        return await handler(event, data)