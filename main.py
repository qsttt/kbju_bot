import asyncio
from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from core.config import settings
from core.logging_config import setup_logging

from bot.handlers import start, diary, premium, menu
from bot.handlers import admin as admin_handlers
from bot.handlers import profile, diag
from bot.handlers import manual_input  # подключим ПОСЛЕДНИМ для приоритета
from bot.middlewares.ensure_user import EnsureUserMiddleware


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="add", description="Добавить блюдо"),
        BotCommand(command="summary", description="Сводка за сегодня"),
        BotCommand(command="diag", description="Диагностика"),
    ]
    await bot.set_my_commands(commands)


async def main():
    setup_logging()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Глобально гарантируем существование пользователя перед любым хендлером
    dp.message.middleware(EnsureUserMiddleware())
    dp.callback_query.middleware(EnsureUserMiddleware())

    # Роутеры: ручной ввод — ПОСЛЕДНИМ, чтобы не перехватывать чужие апдейты
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(diary.router)
    dp.include_router(premium.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(profile.router)
    dp.include_router(diag.router)
    dp.include_router(manual_input.router)  # важен порядок

    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())