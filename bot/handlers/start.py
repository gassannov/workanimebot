"""
Start and help command handlers.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from ..utils.keyboard import build_main_menu_keyboard

logger = logging.getLogger(__name__)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - show welcome message and main menu."""
    user_name = update.effective_user.first_name

    await update.message.reply_text(
        f"👋 *Welcome, {user_name}!*\n\n"
        "🎌 I'm your Anime Bot assistant.\n"
        "I can help you find and watch anime episodes.\n\n"
        "*Quick Start:*\n"
        "• Click a button below to select a command\n"
        "• Or type a command directly (e.g., `/search One Piece`)\n\n"
        "Choose an option:",
        reply_markup=build_main_menu_keyboard(),
        parse_mode="Markdown",
    )


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(
        "🎌 *Anime Bot Help*\n\n"
        "*Available Commands:*\n"
        "• `/start` - Show main menu\n"
        "• `/menu` - Show command menu\n"
        "• `/search <anime name>` - Search for anime\n"
        "• `/help` - Show this help message\n"
        "• `/cancel` - Cancel current operation\n\n"
        "*How to use:*\n"
        "1. Use `/search` or click Search button\n"
        "2. Select an anime from results\n"
        "3. Choose an episode\n"
        "4. Select video quality\n"
        "5. Video will be sent to you!\n\n"
        "*Features:*\n"
        "• Sub/Dub toggle\n"
        "• Multiple video quality options\n"
        "• Direct video in chat\n"
        "• Pagination for long lists\n\n"
        "*Tips:*\n"
        "• Type `/search One Piece` for direct search\n"
        "• Use pagination buttons to browse results\n"
        "• Switch between sub/dub with toggle button\n"
        "• If video fails, you'll get a direct URL",
        reply_markup=build_main_menu_keyboard(),
        parse_mode="Markdown",
    )
