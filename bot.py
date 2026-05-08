import asyncio
import logging
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from app.loader import bot, dp
from app.database.db import create_tables, async_session_maker
from app.middlewares import ForceSubscribeMiddleware, AntiFloodMiddleware, DatabaseMiddleware
from app.handlers import main_router
from app.database.queries.ads import deactivate_expired_ads


# ─── RENDER UCHUN HEALTH SERVER ──────────────────────────

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK - KinoBot ishlayapti!")

    def log_message(self, *args):
        pass


def run_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# ─── STARTUP / SHUTDOWN ──────────────────────────────────

async def on_startup(bot: Bot) -> None:
    await create_tables()

    async with async_session_maker() as session:
        try:
            expired = await deactivate_expired_ads(session)
            if expired:
                logging.info(f"📢 {expired} ta muddati o'tgan reklama o'chirildi")
        except Exception as e:
            logging.warning(f"Ads tekshirishda xato: {e}")

    # set_my_commands — xato bo'lsa bot to'xtamasin
    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="Botni ishga tushirish"),
            BotCommand(command="help", description="Yordam"),
            BotCommand(command="admin", description="Admin panel"),
        ])
    except Exception as e:
        logging.warning(f"set_my_commands xatosi (muhim emas): {e}")

    logging.info("✅ Bot ishga tushdi!")


async def on_shutdown(bot: Bot) -> None:
    logging.info("🛑 Bot to'xtatildi.")
    await bot.session.close()


# ─── MAIN ────────────────────────────────────────────────

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Render health server — port 8080
    thread = threading.Thread(target=run_health_server, daemon=True)
    thread.start()
    logging.info("🌐 Health server 8080 portda ishga tushdi")

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
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
