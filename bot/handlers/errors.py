"""
Error handling for the bot.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error(f"Exception while handling an update: {context.error}")

    # Determine if we can notify the user
    if update and update.effective_message:
        try:
            error_msg = str(context.error)
            # Truncate long error messages
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."

            await update.effective_message.reply_text(
                f"❌ An error occurred: {error_msg}\n\n"
                "Please try again or use /search to start a new search."
            )
        except Exception as e:
            logger.error(f"Could not send error message to user: {e}")
