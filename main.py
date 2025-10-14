import asyncio
import os
import socket
import aiohttp
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from core.config import settings
from bot.handlers import start, manual_input, diary, premium, menu
from bot.handlers import admin as admin_handlers
from aiogram.client.default import DefaultBotProperties
from bot.handlers import profile, diag
from core.logging_config import setup_logging
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
setup_logging()

async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск"),
        BotCommand(command="add", description="Добавить приём пищи"),
        BotCommand(command="summary", description="Сводка за сегодня"),
        BotCommand(command="premium", description="Премиум"),
    ])

async def main():
    # Форсируем IPv4, адекватные таймауты и (если нужно) прокси из TG_PROXY_URL
    connector = aiohttp.TCPConnector(
        family=socket.AF_INET,   # <-- ключевая строка: только IPv4
        # ssl оставляем по умолчанию (True), ничего выключать не нужно
    )
    timeout = aiohttp.ClientTimeout(total=120, connect=30)

    session = AiohttpSession(
        connector=connector,
        timeout=timeout,
        proxy=os.getenv("TG_PROXY_URL")  # например: socks5://127.0.0.1:1080 (если используешь)
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
        session=session
    )

    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(manual_input.router)
    dp.include_router(diary.router)
    dp.include_router(premium.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(profile.router)
    dp.include_router(diag.router)

    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())