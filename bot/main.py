"""
Main entry point for the Telegram Anime Bot.
"""

import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

from .config import config
from .handlers.search import get_conversation_handler
from .strings import COMMANDS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start_command(update, context):
    """Handle /start command."""
    await update.message.reply_text(
        COMMANDS["start_welcome"],
        parse_mode="Markdown",
    )


async def help_command(update, context):
    """Handle /help command."""
    await update.message.reply_text(
        COMMANDS["help_message"],
        parse_mode="Markdown",
    )


def main():
    """Start the bot."""
    # Get token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN") or config.BOT_TOKEN
    base_url = os.getenv("TELEGRAM_BASE_URL") or config.TELEGRAM_BASE_URL

    if not token:
        logger.error(COMMANDS["token_not_set_error"])
        print(COMMANDS["token_not_set_message"])
        return

    # Create application
    # application = Application.builder().token(token).build()
    application = Application.builder().token(token).base_url(base_url).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(get_conversation_handler())

    # Add error handler
    # application.add_error_handler(error_handler)

    # Start polling
    logger.info(COMMANDS["bot_starting"])
    print(COMMANDS["bot_running"])
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
