from __future__ import annotations

from aiogram import Dispatcher

# Импортируем подмодули, чтобы их routers были доступны
from . import start, menu, profile, diary, premium, admin, diag, manual_input  # noqa: F401


def register_all(dp: Dispatcher) -> None:
    """Регистрируем роутеры в правильном порядке.
    manual_input — последним, чтобы не перехватывать чужие события.
    """
    dp.include_router(start.router)
    try:
        dp.include_router(menu.router)
    except Exception:
        pass
    dp.include_router(profile.router)
    dp.include_router(diary.router)
    try:
        dp.include_router(premium.router)
    except Exception:
        pass
    try:
        dp.include_router(admin.router)
    except Exception:
        pass
    try:
        dp.include_router(diag.router)
    except Exception:
        pass
    # Всегда в самом конце
    dp.include_router(manual_input.router)