"""Domain models for the reusable anime application layer."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class AnimeResult:
    """A search result returned by an anime provider.

    Example:
        anime = AnimeResult("id", "One Piece", 1000, 500)
    """

    id: str
    title: str
    available_episodes_sub: int
    available_episodes_dub: int


@dataclass(slots=True)
class StreamOption:
    """A normalized stream option for an episode.

    Example:
        stream = StreamOption(
            url="https://example.com/video.m3u8",
            resolution=1080,
            episode="1",
            language="sub",
            provider="allanime",
        )
    """

    url: str
    resolution: int
    episode: str
    language: str
    provider: str
    referer: Optional[str] = None
    subtitle_url: Optional[str] = None

    @property
    def resolution_label(self) -> str:
        """Return a UI-friendly resolution label.

        Args:
            None.

        Returns:
            str: The resolution label such as ``1080p``.
        """

        return f"{self.resolution}p" if self.resolution else "auto"


@dataclass(slots=True)
class DownloadResult:
    """A completed download produced by the application layer.

    Example:
        result = DownloadResult(
            file_path=Path("/tmp/video.mkv"),
            stream_url="https://example.com/video.m3u8",
            resolution="1080p",
            provider="allanime",
        )
    """

    file_path: Path
    stream_url: str
    resolution: Optional[str]
    provider: Optional[str]
    referer: Optional[str] = None
    subtitle_url: Optional[str] = None
