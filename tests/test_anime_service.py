"""Tests for the reusable anime application service."""

import unittest
from pathlib import Path

from anime_app.models import AnimeResult, DownloadResult, StreamOption
from anime_app.service import AnimeService


class FakeGateway:
    """Gateway double for AnimeService tests.

    Example:
        gateway = FakeGateway()
        results = await gateway.search("One Piece", "sub")
    """

    def __init__(self) -> None:
        """Initialize fake gateway state.

        Args:
            None.

        Returns:
            None.
        """

        self.search_calls = []
        self.episode_calls = []
        self.stream_calls = []

    async def search(self, query: str, translation_type: str) -> list[AnimeResult]:
        """Return deterministic search results for tests.

        Args:
            query: Search text.
            translation_type: Requested language.

        Returns:
            list[AnimeResult]: Fake search results.
        """

        self.search_calls.append((query, translation_type))
        return [AnimeResult("anime-1", "One Piece", 10, 5)]

    async def list_episodes(self, anime_id: str, translation_type: str) -> list[str]:
        """Return deterministic episode results for tests.

        Args:
            anime_id: Anime identifier.
            translation_type: Requested language.

        Returns:
            list[str]: Fake episode list.
        """

        self.episode_calls.append((anime_id, translation_type))
        return ["1", "2"]

    async def get_stream_options(
        self,
        anime_id: str,
        episode: str,
        translation_type: str,
    ) -> list[StreamOption]:
        """Return deterministic stream options for tests.

        Args:
            anime_id: Anime identifier.
            episode: Episode number.
            translation_type: Requested language.

        Returns:
            list[StreamOption]: Fake stream options.
        """

        self.stream_calls.append((anime_id, episode, translation_type))
        return [
            StreamOption(
                url="https://example.com/720",
                resolution=720,
                episode=episode,
                language=translation_type,
                provider="test-provider",
            ),
            StreamOption(
                url="https://example.com/1080",
                resolution=1080,
                episode=episode,
                language=translation_type,
                provider="test-provider",
            ),
        ]


class FakeDownloader:
    """Downloader double for AnimeService tests.

    Example:
        downloader = FakeDownloader()
        result = await downloader.download_stream(stream, "one-piece-1")
    """

    def __init__(self) -> None:
        """Initialize fake downloader state.

        Args:
            None.

        Returns:
            None.
        """

        self.calls = []

    async def download_stream(
        self,
        stream: StreamOption,
        target_name: str,
    ) -> DownloadResult:
        """Return deterministic download metadata for tests.

        Args:
            stream: Stream to "download".
            target_name: Requested file stem.

        Returns:
            DownloadResult: Fake download result.
        """

        self.calls.append((stream, target_name))
        return DownloadResult(
            file_path=Path(f"/tmp/{target_name}.mkv"),
            stream_url=stream.url,
            resolution=stream.resolution_label,
            provider=stream.provider,
            referer=stream.referer,
            subtitle_url=stream.subtitle_url,
        )


class AnimeServiceTests(unittest.IsolatedAsyncioTestCase):
    """Verify AnimeService orchestration behavior.

    Example:
        test_case = AnimeServiceTests()
    """

    async def asyncSetUp(self) -> None:
        """Create service dependencies for each test.

        Args:
            None.

        Returns:
            None.
        """

        self.gateway = FakeGateway()
        self.downloader = FakeDownloader()
        self.service = AnimeService(self.gateway, self.downloader)

    async def test_search_anime_returns_gateway_results(self) -> None:
        """Ensure search is delegated through the gateway.

        Args:
            None.

        Returns:
            None.
        """

        results = await self.service.search_anime("One Piece", "sub")

        self.assertEqual(self.gateway.search_calls, [("One Piece", "sub")])
        self.assertEqual(results[0].title, "One Piece")

    async def test_download_episode_uses_best_stream_by_default(self) -> None:
        """Ensure best-quality stream is selected when no index is provided.

        Args:
            None.

        Returns:
            None.
        """

        result = await self.service.download_episode(
            anime_id="anime-1",
            episode="1",
            translation_type="sub",
            anime_title="One Piece",
        )

        selected_stream, target_name = self.downloader.calls[0]
        self.assertEqual(selected_stream.resolution, 1080)
        self.assertEqual(target_name, "One Piece-episode-1-1080p")
        self.assertEqual(result.resolution, "1080p")

    async def test_download_episode_uses_explicit_stream_index(self) -> None:
        """Ensure caller can choose a specific stream index.

        Args:
            None.

        Returns:
            None.
        """

        await self.service.download_episode(
            anime_id="anime-1",
            episode="2",
            translation_type="dub",
            stream_selector=0,
            anime_title="One Piece",
        )

        selected_stream, target_name = self.downloader.calls[0]
        self.assertEqual(selected_stream.resolution, 720)
        self.assertEqual(target_name, "One Piece-episode-2-720p")
