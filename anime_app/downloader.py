"""Downloader implementation for the reusable anime application layer."""

import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from anipy_api.download import Downloader
from anipy_api.provider import LanguageTypeEnum, ProviderStream

from .config import app_config
from .models import DownloadResult, StreamOption


class AnimeDownloader:
    """Download anime streams into local files.

    Example:
        downloader = AnimeDownloader()
        result = await downloader.download_stream(stream, target_name="one-piece-1")
    """

    def __init__(self) -> None:
        """Initialize downloader dependencies and thread executor.

        Args:
            None.

        Returns:
            None.
        """

        self._executor = ThreadPoolExecutor(max_workers=1)
        self._downloader: Downloader | None = None

    def _create_downloader(self) -> Downloader:
        """Build a fresh anipy downloader instance.

        Args:
            None.

        Returns:
            Downloader: Configured downloader instance.
        """

        return Downloader(
            self._progress_callback,
            self._info_callback,
            self._error_callback,
        )

    @staticmethod
    def _progress_callback(percentage: float) -> None:
        """Handle downloader progress events.

        Args:
            percentage: Download completion percentage.

        Returns:
            None.
        """

        return None

    @staticmethod
    def _info_callback(message: str) -> None:
        """Handle downloader info messages.

        Args:
            message: Informational message from the downloader.

        Returns:
            None.
        """

        return None

    @staticmethod
    def _error_callback(message: str) -> None:
        """Handle downloader soft errors.

        Args:
            message: Error message emitted by the downloader.

        Returns:
            None.
        """

        return None

    def _sanitize_name(self, value: str) -> str:
        """Convert an arbitrary title into a safe filename stem.

        Args:
            value: Raw text to sanitize.

        Returns:
            str: Filesystem-safe filename stem.
        """

        sanitized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
        return sanitized or "video"

    def _build_provider_stream(self, stream: StreamOption) -> ProviderStream:
        """Convert a normalized stream into anipy's provider stream type.

        Args:
            stream: Normalized application stream.

        Returns:
            ProviderStream: Stream object compatible with anipy downloader.
        """

        language = (
            LanguageTypeEnum.DUB
            if stream.language == "dub"
            else LanguageTypeEnum.SUB
        )
        episode = (
            float(stream.episode) if "." in stream.episode else int(stream.episode)
        )
        return ProviderStream(
            url=stream.url,
            resolution=stream.resolution,
            episode=episode,
            language=language,
            subtitle=None,
            referrer=stream.referer,
        )

    async def download_stream(
        self,
        stream: StreamOption,
        target_name: str,
    ) -> DownloadResult:
        """Download a normalized stream and return file metadata.

        Args:
            stream: Normalized stream selected by a caller.
            target_name: Desired file name stem without extension.

        Returns:
            DownloadResult: File path and source metadata for the download.
        """

        file_name = f"{self._sanitize_name(target_name)}{app_config.download_container}"
        target_path = app_config.download_dir.expanduser().resolve() / file_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        provider_stream = self._build_provider_stream(stream)

        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            self._executor,
            self._download_sync,
            provider_stream,
            target_path,
        )

        return DownloadResult(
            file_path=file_path,
            stream_url=stream.url,
            resolution=stream.resolution_label,
            provider=stream.provider,
            referer=stream.referer,
            subtitle_url=stream.subtitle_url,
        )

    def _download_sync(self, stream: ProviderStream, target_path: Path) -> Path:
        """Run the blocking download on a worker thread.

        Args:
            stream: Provider stream compatible with anipy downloader.
            target_path: Final output path for the downloaded file.

        Returns:
            Path: Path produced by the downloader.
        """

        self._downloader = self._create_downloader()
        return self._downloader.download(
            stream=stream,
            download_path=target_path,
            container=app_config.download_container,
            max_retry=app_config.download_max_retry,
            ffmpeg=app_config.use_ffmpeg,
        )

    async def close(self) -> None:
        """Shutdown downloader executor resources.

        Args:
            None.

        Returns:
            None.
        """

        self._executor.shutdown(wait=True)
