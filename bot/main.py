"""
Main entry point for the Telegram Anime Bot.
"""

import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

from .config import config
from .handlers.search import get_conversation_handler
from .handlers.errors import error_handler

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
        "🎌 *Welcome to Anime Bot!*\n\n"
        "I can help you find and watch anime episodes.\n\n"
        "*Commands:*\n"
        "• `/search <query>` - Search for anime\n"
        "• `/search` - Start interactive search\n"
        "• `/help` - Show help message\n\n"
        "*Example:*\n"
        "`/search One Piece`",
        parse_mode="Markdown",
    )


async def help_command(update, context):
    """Handle /help command."""
    await update.message.reply_text(
        "🎌 *Anime Bot Help*\n\n"
        "*How to use:*\n"
        "1. Use `/search <anime name>` to find anime\n"
        "2. Select an anime from the results\n"
        "3. Choose an episode\n"
        "4. Video will be sent to you!\n\n"
        "*Features:*\n"
        "• Sub/Dub toggle\n"
        "• Multiple video quality options\n"
        "• Direct video in chat\n\n"
        "*Tips:*\n"
        "• Use the pagination buttons for long lists\n"
        "• Switch between sub/dub with the toggle button\n"
        "• If video fails, you'll get a direct URL",
        parse_mode="Markdown",
    )


def main():
    """Start the bot."""
    # Get token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN") or config.BOT_TOKEN

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        print("Error: Please set TELEGRAM_BOT_TOKEN in .env file or environment")
        return

    # Create application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(get_conversation_handler())

    # Add error handler
    application.add_error_handler(error_handler)

    # Start polling
    logger.info("Starting bot...")
    print("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
