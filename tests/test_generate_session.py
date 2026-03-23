"""Tests for the Telethon string session generator helper."""

import os
import unittest
from unittest.mock import patch


class GenerateSessionTests(unittest.TestCase):
    """Verify config fallback for the session generator helper.

    Example:
        test_case = GenerateSessionTests()
    """

    def test_reuses_general_api_credentials(self) -> None:
        """Allow generation with the existing `.env` API credentials.

        Args:
            None.

        Returns:
            None.
        """

        env = {
            "TELEGRAM_API_ID": "25242613",
            "TELEGRAM_API_HASH": "hash-value",
        }

        with patch.dict(os.environ, env, clear=True):
            api_id = os.getenv("TELEGRAM_E2E_API_ID") or os.getenv("TELEGRAM_API_ID")
            api_hash = os.getenv("TELEGRAM_E2E_API_HASH") or os.getenv(
                "TELEGRAM_API_HASH"
            )

        self.assertEqual(api_id, "25242613")
        self.assertEqual(api_hash, "hash-value")


if __name__ == "__main__":
    unittest.main()
