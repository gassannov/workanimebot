"""
Configuration for the Telegram Anime Bot.
Mirrors ani-cli settings for easy synchronization.
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    # Telegram
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # AllAnime API (mirrors ani-cli lines 381-384)
    ALLANIME_API: str = "https://api.allanime.day/api"
    ALLANIME_REFERER: str = "https://allmanga.to"
    ALLANIME_BASE: str = "allanime.day"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"

    # Default settings
    TRANSLATION_TYPE: str = "sub"  # or "dub"
    SEARCH_LIMIT: int = 40
    ITEMS_PER_PAGE: int = 8
    EPISODES_PER_PAGE: int = 15


config = Config()
