"""Main entry point for the Telegram Job Bot."""
import asyncio
import os
import sys
import platform
import logging
from telegram import Update
from telegram.ext import Application
from bot import get_bot
from scheduler import run_digest
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def run_polling():
    """Run bot in polling mode (for development)."""
    logger.info("Starting bot in polling mode...")
    print("Starting bot in polling mode...")
    
    # Create application
    job_bot = get_bot()
    application = job_bot.create_application()
    
    # Start polling
    logger.info("Bot is running. Press Ctrl+C to stop.")
    print("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def run_webhook(port: int = 8080):
    """Run bot in webhook mode (for Cloud Run)."""
    print(f"Starting bot in webhook mode on port {port}...")
    
    # Create application
    job_bot = get_bot()
    application = job_bot.create_application()
    
    base_url = (config.WEBHOOK_BASE_URL or os.getenv("RENDER_EXTERNAL_URL") or "").strip()
    if not base_url:
        raise ValueError("WEBHOOK_BASE_URL or RENDER_EXTERNAL_URL must be set for webhook mode")
    webhook_url = base_url.rstrip('/') + "/webhook"
    
    # Start webhook server
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="/webhook",
        webhook_url=webhook_url
    )


def run_server(port: int = 8080):
    """Run a combined HTTP server for Telegram webhook and digest cron."""
    import asyncio
    from aiohttp import web
    from telegram import Update
    
    job_bot = get_bot()
    application = job_bot.create_application()
    base_url = (config.WEBHOOK_BASE_URL or os.getenv("RENDER_EXTERNAL_URL") or "").strip()
    if not base_url:
        raise ValueError("WEBHOOK_BASE_URL or RENDER_EXTERNAL_URL must be set for server mode")
    webhook_url = base_url.rstrip('/') + "/webhook"
    
    async def telegram_webhook(request: web.Request):
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(text="ok")
    
    async def digest_cron(request: web.Request):
        await run_digest()
        return web.Response(text="digest triggered")
    
    async def on_startup(app: web.Application):
        await application.initialize()
        await application.start()
        await application.bot.set_webhook(webhook_url)
        print("Telegram application started")
    
    async def on_cleanup(app: web.Application):
        await application.stop()
        await application.shutdown()
        await application.post_stop()
        print("Telegram application stopped")
    
    app = web.Application()
    app.router.add_post("/webhook", telegram_webhook)
    app.router.add_post("/digest-cron", digest_cron)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    print(f"Starting combined server on port {port}...")
    web.run_app(app, host="0.0.0.0", port=port)

def run_digest_job():
    """Run the daily digest job (sync wrapper)."""
    asyncio.run(run_digest())


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "digest":
            # Run digest job
            print("Running digest job...")
            run_digest_job()
        elif sys.argv[1] == "webhook":
            # Run in webhook mode
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            run_webhook(port)
        elif sys.argv[1] == "serve":
            # Run combined webhook + digest-cron HTTP server
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            run_server(port)
        else:
            print("Unknown command. Use 'python main.py [polling|webhook|digest|serve]'")
    else:
        # Default to polling mode for development
        run_polling()
