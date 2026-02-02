"""
Main entry point for the Telegram Anime Bot.
"""

import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from .config import config
from .handlers.menu import handle_menu, handle_menu_callback
from .handlers.search import get_conversation_handler
from .handlers.start import handle_help, handle_start

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    # Get token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN") or config.BOT_TOKEN
    base_url = os.getenv("TELEGRAM_BASE_URL") or config.TELEGRAM_BASE_URL

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        print("Error: Please set TELEGRAM_BOT_TOKEN in .env file or environment")
        return

    # Create application
    application = Application.builder().token(token).base_url(base_url).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("menu", handle_menu))
    application.add_handler(CommandHandler("help", handle_help))

    # Add menu callback handler (should be before conversation handler)
    application.add_handler(
        CallbackQueryHandler(handle_menu_callback, pattern="^menu:")
    )

    # Add conversation handler for search flow
    application.add_handler(get_conversation_handler())

    # Add error handler
    # application.add_error_handler(error_handler)

    # Start polling
    logger.info("Starting bot...")
    print("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
