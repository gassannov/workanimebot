"""API modules using anipy-cli library."""

from .anime_api import AnimeResult, VideoLink, api_client
from .downloader import downloader

__all__ = ["api_client", "AnimeResult", "VideoLink", "downloader"]
