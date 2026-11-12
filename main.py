import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import BOT_TOKEN
from database import count_syllabus_lessons, init_db
from handlers import admin, lesson, menu, onboarding, vocab_quiz
from middlewares.sub_check import SubscriptionAndBlockMiddleware
from scheduler import shutdown_scheduler, start_scheduler
from seed_syllabus import seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("bot")


async def health_check(request: web.Request) -> web.Response:
    return web.Response(text="AI English Tutor Telegram Bot is healthy and running!")


async def start_dummy_web_server(port: int) -> web.AppRunner:
    """Starts a lightweight web server so Render Free Web Service doesn't shut down."""
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check web server running on port {port}")
    return runner


async def main() -> None:
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN is missing! Please set BOT_TOKEN in environment variables.")
        sys.exit(1)

    # 1. Start lightweight web server if PORT is provided by Render / Heroku
    port_env = os.getenv("PORT")
    web_runner = None
    if port_env:
        try:
            web_runner = await start_dummy_web_server(int(port_env))
        except Exception as e:
            logger.warning(f"Could not start dummy web server on port {port_env}: {e}")

    # 2. Initialize SQLite Database
    logger.info("Initializing database...")
    await init_db()

    # 3. Check and Seed Syllabus if empty
    beginner_count = await count_syllabus_lessons("Beginner")
    if beginner_count < 10:
        logger.info("Seeding syllabus curriculum with 60 comprehensive lessons...")
        await seed()
    else:
        logger.info(f"Syllabus already seeded ({beginner_count} Beginner lessons found).")

    # 4. Start Background Scheduler
    start_scheduler()

    # 5. Initialize Bot & Dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # 6. Register Middlewares
    sub_middleware = SubscriptionAndBlockMiddleware()
    dp.message.outer_middleware(sub_middleware)
    dp.callback_query.outer_middleware(sub_middleware)

    # 7. Include Handlers in logical order
    dp.include_router(admin.router)       # Admin handlers with strict security filter
    dp.include_router(onboarding.router)  # /start and registration flows
    dp.include_router(menu.router)        # Profile, Tariffs, TolovAPI payments
    dp.include_router(vocab_quiz.router)   # Pure Python flashcard quiz
    dp.include_router(lesson.router)      # Lesson chat and exam engine

    # 8. Start Polling
    logger.info("Bot started successfully. Listening for updates...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopping...")
    finally:
        shutdown_scheduler()
        if web_runner:
            await web_runner.cleanup()
        await bot.session.close()
        logger.info("Bot cleanly shut down.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
