"""
Main menu command handler for command selection layer.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from ..utils.keyboard import MENU_HELP, MENU_SEARCH, build_main_menu_keyboard

logger = logging.getLogger(__name__)


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu command - show main menu."""
    await update.message.reply_text(
        "📋 *Main Menu*\n\nSelect a command or type it directly:",
        reply_markup=build_main_menu_keyboard(),
        parse_mode="Markdown",
    )


async def handle_menu_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle menu button callbacks."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == MENU_SEARCH:
        await query.edit_message_text(
            "🔍 *Search Anime*\n\n"
            "You can:\n"
            "• Type `/search <anime name>` for direct search\n"
            "• Type `/search` to start interactive search\n\n"
            "*Example:* `/search One Piece`",
            parse_mode="Markdown",
        )

    elif data == MENU_HELP:
        from .start import handle_help

        # Create a pseudo message update for help command
        update.message = query.message
        await handle_help(update, context)
