import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import BOT_TOKEN
from database import count_all_syllabus_lessons, init_db
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
    """HTTP endpoint returning 200 OK for Render Web Service health-check."""
    return web.Response(text="OK - AI English Tutor Telegram Bot is healthy and running!")


async def run_health_check_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Runs a non-blocking aiohttp web server concurrently with polling to satisfy Render port binding."""
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Health-check server successfully listening on {host}:{port}")

    try:
        # Keep web server active indefinitely until cancelled
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Health-check server shutting down...")
    finally:
        await runner.cleanup()


async def run_bot_polling(bot: Bot, dp: Dispatcher) -> None:
    """Clears old webhooks and begins long polling."""
    # 4. Clear Webhook Before Polling to prevent queued update conflicts
    logger.info("Clearing webhook before polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot polling started successfully. Listening for Telegram updates...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def main() -> None:
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN is missing! Please configure BOT_TOKEN in your environment variables.")
        sys.exit(1)

    # 1. Initialize SQLite Database & Auto-Seed Syllabus if empty
    logger.info("Initializing database...")
    await init_db()

    total_lessons = await count_all_syllabus_lessons()
    if total_lessons == 0:
        logger.info("Syllabus table is empty on fresh deployment! Auto-seeding 60 lessons now...")
        await seed()
        logger.info("Auto-seeding completed successfully.")
    else:
        logger.info(f"Syllabus already seeded ({total_lessons} lessons available).")

    # 2. Start Background Scheduler
    start_scheduler()

    # 3. Initialize Bot & Dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # 4. Register Middlewares
    sub_middleware = SubscriptionAndBlockMiddleware()
    dp.message.outer_middleware(sub_middleware)
    dp.callback_query.outer_middleware(sub_middleware)

    # 5. Include Handlers
    dp.include_router(admin.router)       # Admin handlers with strict security filter
    dp.include_router(onboarding.router)  # /start and registration flows
    dp.include_router(menu.router)        # Profile, Tariffs, TolovAPI payments
    dp.include_router(vocab_quiz.router)   # Pure Python flashcard quiz
    dp.include_router(lesson.router)      # Lesson chat and exam engine

    # 6. Run Health-Check Server & Telegram Polling Concurrently via asyncio.gather
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Launching health-check server (port {port}) and bot polling concurrently...")

    try:
        await asyncio.gather(
            run_health_check_server(host="0.0.0.0", port=port),
            run_bot_polling(bot=bot, dp=dp),
        )
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received...")
    finally:
        shutdown_scheduler()
        await bot.session.close()
        logger.info("Bot cleanly shut down.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
