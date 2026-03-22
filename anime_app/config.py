"""Configuration for the reusable anime application layer."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    """Application-layer settings shared by non-Telegram clients.

    Example:
        config = AppConfig(provider_name="allanime")
    """

    provider_name: str = os.getenv("ANIME_PROVIDER", "allanime")
    download_dir: Path = Path(
        os.getenv("ANIME_DOWNLOAD_DIR", "~/Downloads/workanimebot")
    ).expanduser()
    download_container: str = os.getenv("ANIME_DOWNLOAD_CONTAINER", ".mkv")
    download_max_retry: int = int(os.getenv("ANIME_DOWNLOAD_MAX_RETRY", "3"))
    use_ffmpeg: bool = os.getenv("ANIME_USE_FFMPEG", "false").lower() == "true"


app_config = AppConfig()
