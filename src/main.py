"""Entrypoint: configure, build graph, run Telegram bot (polling or webhook)."""

import asyncio
import logging
import sys

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from src.config import get_settings
from src.bot.handlers import start_command, handle_message
from src.bot.webhook import create_webhook_app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def build_application():
    """Build PTB Application with handlers."""
    s = get_settings()
    builder = ApplicationBuilder().token(s.telegram_bot_token)
    if s.bot_mode == "webhook":
        builder = builder.updater(None)
    app = builder.build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


async def run_polling():
    """Run bot with long polling (local dev)."""
    app = build_application()
    await app.initialize()
    await app.start()
    logger.info("Polling started")
    await app.updater.start_polling(drop_pending_updates=True)
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    await app.updater.stop()
    await app.stop()
    await app.shutdown()


async def run_webhook():
    """Run bot with webhook + Starlette server."""
    s = get_settings()
    app = build_application()
    await app.initialize()
    await app.bot.set_webhook(
        url=s.webhook_url,
        allowed_updates=["message", "callback_query"],
    )
    starlette_app = create_webhook_app(app)
    import uvicorn
    config = uvicorn.Config(
        starlette_app,
        host="0.0.0.0",
        port=s.port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    async with app:
        await app.start()
        logger.info("Webhook registered: %s", s.webhook_url)
        await server.serve()


def main():
    """Validate config and run bot in polling or webhook mode."""
    try:
        s = get_settings()
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)
    if s.bot_mode == "webhook":
        asyncio.run(run_webhook())
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
