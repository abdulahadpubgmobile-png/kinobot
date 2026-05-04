import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from app.loader import bot, dp
from app.database.db import create_tables, async_session_maker
from app.middlewares import ForceSubscribeMiddleware, AntiFloodMiddleware, DatabaseMiddleware
from app.handlers import main_router
from app.database.queries.ads import deactivate_expired_ads


async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="help", description="Yordam"),
        BotCommand(command="admin", description="Admin panel (adminlar uchun)"),
    ]
    await bot.set_my_commands(commands)


async def on_startup(bot: Bot) -> None:
    await create_tables()

    # Muddati o'tgan reklamalarni o'chiramiz
    async with async_session_maker() as session:
        expired = await deactivate_expired_ads(session)
        if expired:
            logging.info(f"📢 {expired} ta muddati o'tgan reklama o'chirildi")

    await set_commands(bot)
    logging.info("✅ Bot ishga tushdi!")


async def on_shutdown(bot: Bot) -> None:
    logging.info("🛑 Bot to'xtatildi.")
    await bot.session.close()


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(AntiFloodMiddleware())
    dp.message.middleware(ForceSubscribeMiddleware())
    dp.callback_query.middleware(ForceSubscribeMiddleware())

    # Handlers
    dp.include_router(main_router)

    # Hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Polling
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
