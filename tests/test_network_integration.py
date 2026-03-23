"""Integration tests for real provider search and download flows."""

import asyncio
import os
import unittest
from pathlib import Path

from anime_app import AnimeService
from anime_app.config import app_config

RUN_NETWORK_TESTS = os.getenv("RUN_NETWORK_TESTS") == "1"
DOWNLOAD_TIMEOUT_SECONDS = 600
HEARTBEAT_INTERVAL_SECONDS = 30


@unittest.skipUnless(
    RUN_NETWORK_TESTS,
    "Set RUN_NETWORK_TESTS=1 to run real provider network tests.",
)
class AnimeNetworkIntegrationTests(unittest.IsolatedAsyncioTestCase):
    """Verify real provider search and download behavior.

    Example:
        test_case = AnimeNetworkIntegrationTests()
    """

    async def asyncSetUp(self) -> None:
        """Create the real service and isolate downloaded files.

        Args:
            None.

        Returns:
            None.
        """

        self.service = AnimeService()
        self._original_download_dir = app_config.download_dir
        self._test_download_dir = Path("tests/.tmp/network-downloads").resolve()
        self._test_download_dir.mkdir(parents=True, exist_ok=True)
        app_config.download_dir = self._test_download_dir
        self._last_progress = None
        self.service._downloader._progress_callback = self._progress_callback
        self.service._downloader._info_callback = self._info_callback
        self.service._downloader._error_callback = self._error_callback

    async def asyncTearDown(self) -> None:
        """Remove downloaded test files and restore config state.

        Args:
            None.

        Returns:
            None.
        """

        app_config.download_dir = self._original_download_dir
        for file_path in self._test_download_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        if self._test_download_dir.exists():
            self._test_download_dir.rmdir()

    async def test_search_one_piece_returns_results(self) -> None:
        """Ensure real provider search returns One Piece results.

        Args:
            None.

        Returns:
            None.
        """

        results = await self.service.search_anime("One Piece", "sub")

        self.assertTrue(results)
        self.assertTrue(
            any("one piece" in result.title.casefold() for result in results),
        )

    async def test_download_first_one_piece_episode(self) -> None:
        """Ensure the first One Piece episode can be downloaded.

        Args:
            None.

        Returns:
            None.
        """

        print("Searching for One Piece...", flush=True)
        results = await self.service.search_anime("One Piece", "sub")
        print(f"Search returned {len(results)} result(s)", flush=True)
        one_piece = next(
            result for result in results if "one piece" in result.title.casefold()
        )
        print(f"Selected title: {one_piece.title} ({one_piece.id})", flush=True)
        episodes = await self.service.list_episodes(one_piece.id, "sub")
        print(f"Loaded {len(episodes)} episode(s)", flush=True)

        self.assertIn("1", episodes)
        print(
            "Starting download of episode 1 "
            f"with timeout {DOWNLOAD_TIMEOUT_SECONDS}s...",
            flush=True,
        )

        heartbeat_task = asyncio.create_task(self._heartbeat())
        try:
            download = await asyncio.wait_for(
                self.service.download_episode(
                    anime_id=one_piece.id,
                    episode="1",
                    translation_type="sub",
                    anime_title=one_piece.title,
                ),
                timeout=DOWNLOAD_TIMEOUT_SECONDS,
            )
        finally:
            heartbeat_task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await heartbeat_task
        print(f"Download finished: {download.file_path}", flush=True)

        self.assertTrue(download.file_path.exists())
        self.assertGreater(download.file_path.stat().st_size, 0)
        self.assertEqual(download.file_path.parent, self._test_download_dir)

    @staticmethod
    def _info_callback(message: str) -> None:
        """Print downloader info messages during integration tests.

        Args:
            message: Informational message from the downloader.

        Returns:
            None.
        """

        if message:
            print(f"[download info] {message}", flush=True)

    @staticmethod
    def _error_callback(message: str) -> None:
        """Print downloader soft errors during integration tests.

        Args:
            message: Error message from the downloader.

        Returns:
            None.
        """

        if message:
            print(f"[download error] {message}", flush=True)

    def _progress_callback(self, percentage: float) -> None:
        """Print coarse download progress updates during integration tests.

        Args:
            percentage: Download completion percentage.

        Returns:
            None.
        """

        rounded = int(percentage)
        if rounded != self._last_progress and rounded % 10 == 0:
            self._last_progress = rounded
            print(f"[download progress] {rounded}%", flush=True)

    async def _heartbeat(self) -> None:
        """Print a periodic message while the network download is running.

        Args:
            None.

        Returns:
            None.
        """

        elapsed_seconds = 0
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            elapsed_seconds += HEARTBEAT_INTERVAL_SECONDS
            print(
                "[download heartbeat] "
                f"still running after {elapsed_seconds}s",
                flush=True,
            )
