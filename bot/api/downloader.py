import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional

from anipy_api.download import Downloader


class AsyncVideoDownloader:
    def __init__(
        self,
        progress_callback: Optional[Callable[[float], None]] = None,
        info_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Асинхронный загрузчик видео

        Args:
            progress_callback: Функция для отслеживания прогресса (процент)
            info_callback: Функция для информационных сообщений
            error_callback: Функция для обработки ошибок
        """
        self.progress_callback = progress_callback or self._default_progress_callback
        self.info_callback = info_callback or self._default_info_callback
        self.error_callback = error_callback or self._default_error_callback

        self.executor = ThreadPoolExecutor(max_workers=1)

        self._downloader: Optional[Downloader] = None

    @staticmethod
    def _default_progress_callback(percentage: float):
        """Обработчик прогресса по умолчанию"""
        print(f"Progress: {percentage:.1f}%", end="\r")

    @staticmethod
    def _default_info_callback(message: str):
        """Обработчик информационных сообщений по умолчанию"""
        print(f"Message from the downloader: {message}")

    @staticmethod
    def _default_error_callback(message: str):
        """Обработчик ошибок по умолчанию"""
        print(f"Soft error from the downloader: {message}")

    def _create_downloader(self) -> Downloader:
        """Создает новый экземпляр Downloader"""
        return Downloader(
            self.progress_callback, self.info_callback, self.error_callback
        )

    async def download_video(
        self,
        stream,
        download_path: str = "~/Downloads",
        container: str = ".mkv",
        max_retry: int = 3,
        ffmpeg: bool = False,
    ) -> Path:
        """
        Асинхронная загрузка видео

        Args:
            stream: Поток для загрузки
            download_path: Путь для сохранения файла
            container: Формат контейнера (например, .mkv)
            max_retry: Максимальное количество повторных попыток
            ffmpeg: Использовать ли ffmpeg

        Returns:
            Path: Путь к загруженному файлу
        """

        download_path = Path(download_path).expanduser().resolve() / Path("video.mkv")

        loop = asyncio.get_event_loop()

        try:
            download_path = await loop.run_in_executor(
                self.executor,
                self._download_sync,
                stream,
                download_path,
                container,
                max_retry,
                ffmpeg,
            )
            return download_path

        except Exception as e:
            self.error_callback(f"Download failed: {str(e)}")
            raise

    def _download_sync(
        self, stream, download_path: Path, container: str, max_retry: int, ffmpeg: bool
    ) -> Path:
        """Синхронный метод загрузки (выполняется в отдельном потоке)"""
        self._downloader = self._create_downloader()

        return self._downloader.download(
            stream=stream,
            download_path=download_path,
            container=container,
            max_retry=max_retry,
            ffmpeg=ffmpeg,
        )

    def cancel_download(self):
        """Отмена текущей загрузки (если поддерживается API)"""
        if self._downloader:
            if hasattr(self._downloader, "cancel"):
                self._downloader.cancel()

    async def close(self):
        """Корректное завершение работы загрузчика"""
        self.executor.shutdown(wait=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


downloader = AsyncVideoDownloader()
