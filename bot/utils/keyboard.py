"""
Inline keyboard builders for Telegram bot UI.
"""

from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..api import AnimeResult
from ..config import config

# Callback data prefixes
ANIME_PREFIX = "anime:"
EPISODE_PREFIX = "ep:"
PAGE_PREFIX = "page:"
QUALITY_PREFIX = "quality:"
BACK_PREFIX = "back:"
DUB_TOGGLE = "toggle_dub"
NOOP = "noop"

# Menu commands
MENU_SEARCH = "menu:search"
MENU_HELP = "menu:help"


def build_anime_list_keyboard(
    results: List[AnimeResult],
    page: int = 0,
    translation_type: str = "sub",
) -> InlineKeyboardMarkup:
    """Build inline keyboard for anime search results with pagination."""
    per_page = config.ITEMS_PER_PAGE
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(results))
    page_results = results[start_idx:end_idx]

    buttons = []

    for i, anime in enumerate(page_results, start=start_idx + 1):
        ep_count = (
            anime.available_episodes_sub
            if translation_type == "sub"
            else anime.available_episodes_dub
        )
        # Truncate long names
        name = anime.name
        if len(name) > 35:
            name = name[:32] + "..."
        text = f"{i}. {name} ({ep_count} ep)"
        buttons.append(
            [InlineKeyboardButton(text, callback_data=f"{ANIME_PREFIX}{anime.id}")]
        )

    # Navigation row
    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                "◀️ Prev", callback_data=f"{PAGE_PREFIX}anime:{page - 1}"
            )
        )

    # Dub/Sub toggle
    toggle_text = "🔊 Dub" if translation_type == "sub" else "📝 Sub"
    nav_row.append(InlineKeyboardButton(toggle_text, callback_data=DUB_TOGGLE))

    if end_idx < len(results):
        nav_row.append(
            InlineKeyboardButton(
                "Next ▶️", callback_data=f"{PAGE_PREFIX}anime:{page + 1}"
            )
        )

    if nav_row:
        buttons.append(nav_row)

    # Cancel button
    buttons.append(
        [InlineKeyboardButton("❌ Cancel", callback_data=f"{BACK_PREFIX}cancel")]
    )

    return InlineKeyboardMarkup(buttons)


def build_episode_list_keyboard(
    episodes: List[str],
    page: int = 0,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for episode selection with pagination."""
    per_page = config.EPISODES_PER_PAGE
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(episodes))
    page_episodes = episodes[start_idx:end_idx]

    buttons = []

    # Create episode buttons in rows of 5
    row = []
    for ep in page_episodes:
        row.append(
            InlineKeyboardButton(f"Ep {ep}", callback_data=f"{EPISODE_PREFIX}{ep}")
        )
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Navigation row
    total_pages = (len(episodes) - 1) // per_page + 1
    nav_row = []

    if page > 0:
        nav_row.append(
            InlineKeyboardButton("◀️", callback_data=f"{PAGE_PREFIX}ep:{page - 1}")
        )

    nav_row.append(
        InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data=NOOP)
    )

    if end_idx < len(episodes):
        nav_row.append(
            InlineKeyboardButton("▶️", callback_data=f"{PAGE_PREFIX}ep:{page + 1}")
        )

    buttons.append(nav_row)

    # Back button
    buttons.append(
        [
            InlineKeyboardButton(
                "🔙 Back to Search", callback_data=f"{BACK_PREFIX}search"
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


def build_quality_keyboard(streams) -> InlineKeyboardMarkup:
    """Build inline keyboard for quality selection."""
    buttons = []

    # Deduplicate by quality
    seen_qualities = set()
    unique_streams = []
    for stream in streams:
        if stream.resolution not in seen_qualities:
            seen_qualities.add(stream.resolution)
            unique_streams.append(stream)

    for stream in unique_streams[:6]:  # Limit to 6 quality options
        text = f"{stream.resolution}"
        # Use index in original list for callback
        idx = streams.index(stream)
        buttons.append(
            [InlineKeyboardButton(text, callback_data=f"{QUALITY_PREFIX}{idx}")]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🔙 Back to Episodes", callback_data=f"{BACK_PREFIX}episodes"
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build main menu keyboard with command options."""
    buttons = [
        [InlineKeyboardButton("🔍 Search Anime", callback_data=MENU_SEARCH)],
        [InlineKeyboardButton("❓ Help", callback_data=MENU_HELP)],
    ]
    return InlineKeyboardMarkup(buttons)
