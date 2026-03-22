"""Use-case orchestration for the reusable anime application layer."""

from typing import Sequence

from .downloader import AnimeDownloader
from .gateway import AnimeGateway
from .models import AnimeResult, DownloadResult, StreamOption


class AnimeService:
    """High-level application service for anime search and download flows.

    Example:
        service = AnimeService()
        results = await service.search_anime("One Piece")
    """

    def __init__(
        self,
        gateway: AnimeGateway | None = None,
        downloader: AnimeDownloader | None = None,
    ) -> None:
        """Initialize service dependencies.

        Args:
            gateway: Optional gateway override for provider access.
            downloader: Optional downloader override for file downloads.

        Returns:
            None.
        """

        self._gateway = gateway or AnimeGateway()
        self._downloader = downloader or AnimeDownloader()

    async def search_anime(
        self, query: str, translation_type: str = "sub"
    ) -> list[AnimeResult]:
        """Search anime titles through the gateway.

        Args:
            query: Search text entered by the caller.
            translation_type: Language identifier such as ``sub`` or ``dub``.

        Returns:
            list[AnimeResult]: Matching search results.
        """

        return await self._gateway.search(query, translation_type)

    async def list_episodes(
        self, anime_id: str, translation_type: str = "sub"
    ) -> list[str]:
        """List available episodes for an anime.

        Args:
            anime_id: Provider-specific anime identifier.
            translation_type: Language identifier such as ``sub`` or ``dub``.

        Returns:
            list[str]: Episode numbers as strings.
        """

        return await self._gateway.list_episodes(anime_id, translation_type)

    async def get_stream_options(
        self,
        anime_id: str,
        episode: str,
        translation_type: str = "sub",
    ) -> list[StreamOption]:
        """Load available stream options for an episode.

        Args:
            anime_id: Provider-specific anime identifier.
            episode: Episode number as a string.
            translation_type: Language identifier such as ``sub`` or ``dub``.

        Returns:
            list[StreamOption]: Normalized stream options.
        """

        return await self._gateway.get_stream_options(
            anime_id,
            episode,
            translation_type,
        )

    async def download_episode(
        self,
        anime_id: str,
        episode: str,
        translation_type: str = "sub",
        stream_selector: str | int = "best",
        anime_title: str | None = None,
    ) -> DownloadResult:
        """Resolve stream options, select a stream, and download it.

        Args:
            anime_id: Provider-specific anime identifier.
            episode: Episode number as a string.
            translation_type: Language identifier such as ``sub`` or ``dub``.
            stream_selector: Either ``best`` or a zero-based stream index.
            anime_title: Optional title used to generate the output file name.

        Returns:
            DownloadResult: Metadata for the completed download.
        """

        streams = await self.get_stream_options(anime_id, episode, translation_type)
        selected_stream = self._select_stream(streams, stream_selector)
        return await self.download_stream(
            selected_stream,
            anime_title=anime_title or anime_id,
            episode=episode,
        )

    async def download_stream(
        self,
        stream: StreamOption,
        anime_title: str,
        episode: str,
    ) -> DownloadResult:
        """Download a previously selected stream option.

        Args:
            stream: Stream chosen by the caller.
            anime_title: Title used for naming the downloaded file.
            episode: Episode number used for naming the downloaded file.

        Returns:
            DownloadResult: Metadata for the completed download.
        """

        target_name = f"{anime_title}-episode-{episode}-{stream.resolution_label}"
        return await self._downloader.download_stream(stream, target_name)

    def _select_stream(
        self,
        streams: Sequence[StreamOption],
        selector: str | int,
    ) -> StreamOption:
        """Pick a stream from the available options.

        Args:
            streams: Available stream options.
            selector: Either ``best`` or a zero-based stream index.

        Returns:
            StreamOption: Selected stream option.
        """

        if not streams:
            raise ValueError("No stream options available")

        if isinstance(selector, int):
            if selector < 0 or selector >= len(streams):
                raise IndexError("Stream index out of range")
            return streams[selector]

        if selector == "best":
            return max(streams, key=lambda stream: stream.resolution)

        raise ValueError(f"Unsupported stream selector: {selector}")
