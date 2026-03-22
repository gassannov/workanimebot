"""Gateway that normalizes access to the anipy provider layer."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List

from anipy_api.provider import LanguageTypeEnum, get_provider

from .config import app_config
from .models import AnimeResult, StreamOption


class AnimeGateway:
    """Async gateway for provider search, episode listing, and stream lookup.

    Example:
        gateway = AnimeGateway()
        results = await gateway.search("One Piece", "sub")
    """

    def __init__(self, provider_name: str | None = None) -> None:
        """Initialize the gateway with a concrete provider instance.

        Args:
            provider_name: Optional provider name override.

        Returns:
            None.
        """

        resolved_name = provider_name or app_config.provider_name
        provider = get_provider(resolved_name)
        if not provider:
            raise ValueError(f"Provider {resolved_name} not found")
        self.provider = provider
        self._provider_name = resolved_name
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _language(self, translation_type: str) -> LanguageTypeEnum:
        """Convert application language text to provider enum.

        Args:
            translation_type: Language identifier such as ``sub`` or ``dub``.

        Returns:
            LanguageTypeEnum: Provider-compatible language enum.
        """

        return (
            LanguageTypeEnum.DUB
            if translation_type == "dub"
            else LanguageTypeEnum.SUB
        )

    async def _run_sync(self, func, *args, **kwargs):
        """Run a blocking provider call on the executor.

        Args:
            func: Callable to execute.
            *args: Positional arguments for the callable.
            **kwargs: Keyword arguments for the callable.

        Returns:
            object: Result returned by the callable.
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: func(*args, **kwargs),
        )

    async def search(
        self, query: str, translation_type: str = "sub"
    ) -> List[AnimeResult]:
        """Search anime and normalize provider results.

        Args:
            query: Search text entered by the caller.
            translation_type: Language identifier such as ``sub`` or ``dub``.

        Returns:
            List[AnimeResult]: Matching anime entries available in the language.
        """

        def _search_sync() -> List[AnimeResult]:
            language = self._language(translation_type)
            results = self.provider.get_search(query)
            anime_results: List[AnimeResult] = []

            for result in results:
                if language not in result.languages:
                    continue

                sub_eps = 0
                dub_eps = 0

                if LanguageTypeEnum.SUB in result.languages:
                    try:
                        sub_eps = len(
                            self.provider.get_episodes(
                                result.identifier,
                                LanguageTypeEnum.SUB,
                            )
                        )
                    except Exception:
                        sub_eps = 0

                if LanguageTypeEnum.DUB in result.languages:
                    try:
                        dub_eps = len(
                            self.provider.get_episodes(
                                result.identifier,
                                LanguageTypeEnum.DUB,
                            )
                        )
                    except Exception:
                        dub_eps = 0

                anime_results.append(
                    AnimeResult(
                        id=result.identifier,
                        title=result.name,
                        available_episodes_sub=sub_eps,
                        available_episodes_dub=dub_eps,
                    )
                )

            return anime_results

        return await self._run_sync(_search_sync)

    async def list_episodes(
        self, anime_id: str, translation_type: str = "sub"
    ) -> List[str]:
        """Return available episodes for an anime.

        Args:
            anime_id: Provider-specific anime identifier.
            translation_type: Language identifier such as ``sub`` or ``dub``.

        Returns:
            List[str]: Episode numbers normalized as strings.
        """

        def _list_episodes_sync() -> List[str]:
            language = self._language(translation_type)
            episodes = self.provider.get_episodes(anime_id, language)
            return [str(episode) for episode in episodes]

        return await self._run_sync(_list_episodes_sync)

    async def get_stream_options(
        self,
        anime_id: str,
        episode: str,
        translation_type: str = "sub",
    ) -> List[StreamOption]:
        """Return normalized stream options for an episode.

        Args:
            anime_id: Provider-specific anime identifier.
            episode: Episode number as a string.
            translation_type: Language identifier such as ``sub`` or ``dub``.

        Returns:
            List[StreamOption]: Stream options for the requested episode.
        """

        def _get_stream_options_sync() -> List[StreamOption]:
            language = self._language(translation_type)
            episode_number = float(episode) if "." in episode else int(episode)
            streams = self.provider.get_video(anime_id, episode_number, language)

            return [
                StreamOption(
                    url=stream.url,
                    resolution=stream.resolution,
                    episode=str(stream.episode),
                    language=translation_type,
                    provider=self._provider_name,
                    referer=stream.referrer,
                    subtitle_url=next(
                        iter(stream.subtitle.values())
                    ).url if stream.subtitle else None,
                )
                for stream in streams
            ]

        return await self._run_sync(_get_stream_options_sync)
