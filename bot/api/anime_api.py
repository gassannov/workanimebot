"""
Anime API wrapper using anipy-cli library.

Provides a simplified interface for the Telegram bot.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Optional

from anipy_api.provider import (
    BaseProvider,
    LanguageTypeEnum,
    get_provider,
)


@dataclass
class AnimeResult:
    """Represents a search result anime."""

    id: str
    name: str
    available_episodes_sub: int
    available_episodes_dub: int


@dataclass
class VideoLink:
    """Represents an extracted video link."""

    quality: str
    url: str
    provider: str
    format: str
    referer: Optional[str] = None
    subtitle_url: Optional[str] = None


class AnimeAPIClient:
    """Wrapper around anipy-cli for telegram bot usage."""

    provider: BaseProvider

    def __init__(self, provider_name: str = "allanime"):
        provider = get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not found")
        self.provider = provider
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous function in an executor."""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self._executor, lambda: func(*args, **kwargs))

    async def search(
        self, query: str, translation_type: str = "sub"
    ) -> List[AnimeResult]:
        """
        Search anime by query.

        Args:
            query: Search query string
            translation_type: "sub" or "dub"

        Returns:
            List of AnimeResult objects
        """

        def _search_sync():
            lang = (
                LanguageTypeEnum.DUB
                if translation_type == "dub"
                else LanguageTypeEnum.SUB
            )

            # Use provider's search (synchronous)
            results = self.provider.get_search(query)

            # Convert to our format and filter by language
            anime_results = []
            for result in results:
                # Check if requested language is available
                if lang not in result.languages:
                    continue

                # Get episode count info
                try:
                    # Determine episode counts
                    sub_eps = 0
                    dub_eps = 0

                    if LanguageTypeEnum.SUB in result.languages:
                        try:
                            sub_eps = len(
                                self.provider.get_episodes(
                                    result.identifier, LanguageTypeEnum.SUB
                                )
                            )
                        except Exception:
                            pass

                    if LanguageTypeEnum.DUB in result.languages:
                        try:
                            dub_eps = len(
                                self.provider.get_episodes(
                                    result.identifier, LanguageTypeEnum.DUB
                                )
                            )
                        except Exception:
                            pass

                    anime_results.append(
                        AnimeResult(
                            id=result.identifier,
                            name=result.name,
                            available_episodes_sub=sub_eps,
                            available_episodes_dub=dub_eps,
                        )
                    )
                except Exception:
                    # If we can't get info, skip this result
                    continue

            return anime_results

        return await self._run_sync(_search_sync)

    async def get_episodes(
        self, show_id: str, translation_type: str = "sub"
    ) -> List[str]:
        """
        Get episode list for a show.

        Args:
            show_id: The anime's ID
            translation_type: "sub" or "dub"

        Returns:
            List of episode numbers (as strings, sorted)
        """

        def _get_episodes_sync():
            lang = (
                LanguageTypeEnum.DUB
                if translation_type == "dub"
                else LanguageTypeEnum.SUB
            )

            episodes = self.provider.get_episodes(show_id, lang)

            # Convert to strings
            return [str(ep) for ep in episodes]

        return await self._run_sync(_get_episodes_sync)

    async def get_video_streams(
        self,
        show_id: str,
        episode: str,
        translation_type: str = "sub",
    ) -> List[VideoLink]:
        """
        Get video links for an episode.

        Args:
            show_id: The anime's ID
            episode: Episode number string
            translation_type: "sub" or "dub"

        Returns:
            List of VideoLink objects
        """

        def _get_video_links_sync():
            lang = (
                LanguageTypeEnum.DUB
                if translation_type == "dub"
                else LanguageTypeEnum.SUB
            )

            # Convert episode string to number
            try:
                episode_num = float(episode) if "." in episode else int(episode)
            except ValueError:
                return []

            # Get streams from provider
            streams = self.provider.get_video(show_id, episode_num, lang)

            return streams

        return await self._run_sync(_get_video_links_sync)


# Singleton instance
api_client = AnimeAPIClient()
