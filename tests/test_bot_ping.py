"""Tests for the Telegram end-to-end bot ping helper."""

import os
import unittest
from unittest.mock import patch

from tools.bot_ping import PingConfig, PingScenario, select_matching_response


class BotPingTests(unittest.TestCase):
    """Verify the Telegram e2e ping configuration helpers.

    Example:
        test_case = BotPingTests()
    """

    def test_from_env_reads_required_values(self) -> None:
        """Build config from environment variables.

        Args:
            None.

        Returns:
            None.
        """

        env = {
            "TELEGRAM_API_ID": "25242613",
            "TELEGRAM_API_HASH": "hash-value",
            "TELEGRAM_E2E_BOT_USERNAME": "anime_test_bot",
            "TELEGRAM_E2E_SESSION_STRING": "session-value",
            "TELEGRAM_E2E_TIMEOUT_SECONDS": "9.5",
        }

        with patch.dict(os.environ, env, clear=False):
            config = PingConfig.from_env()

        self.assertEqual(config.api_id, 25242613)
        self.assertEqual(config.api_hash, "hash-value")
        self.assertEqual(config.bot_username, "anime_test_bot")
        self.assertEqual(config.session_string, "session-value")
        self.assertEqual(config.timeout_seconds, 9.5)
        self.assertEqual(config.scenarios[0].command, "/start")

    def test_from_env_prefers_e2e_values(self) -> None:
        """Prefer dedicated e2e values when both variants are present.

        Args:
            None.

        Returns:
            None.
        """

        env = {
            "TELEGRAM_API_ID": "1",
            "TELEGRAM_API_HASH": "general-hash",
            "TELEGRAM_E2E_API_ID": "2",
            "TELEGRAM_E2E_API_HASH": "e2e-hash",
            "TELEGRAM_E2E_BOT_USERNAME": "anime_test_bot",
            "TELEGRAM_E2E_SESSION_STRING": "session-value",
        }

        with patch.dict(os.environ, env, clear=False):
            config = PingConfig.from_env()

        self.assertEqual(config.api_id, 2)
        self.assertEqual(config.api_hash, "e2e-hash")

    def test_from_env_rejects_missing_values(self) -> None:
        """Fail fast when required credentials are absent.

        Args:
            None.

        Returns:
            None.
        """

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "TELEGRAM_E2E_API_ID"):
                PingConfig.from_env()

    def test_select_matching_response_returns_first_valid_message(self) -> None:
        """Pick the first bot reply newer than the command message.

        Args:
            None.

        Returns:
            None.
        """

        messages = [
            {"id": 10, "text": "old message"},
            {"id": 12, "text": "Welcome to Anime Bot"},
            {"id": 13, "text": "Anime Bot Help"},
        ]

        matched = select_matching_response(messages, 11, ("Welcome", "Anime Bot"))

        self.assertEqual(matched, "Welcome to Anime Bot")

    def test_select_matching_response_ignores_non_matching_messages(self) -> None:
        """Return None when no response satisfies all expected fragments.

        Args:
            None.

        Returns:
            None.
        """

        messages = [
            {"id": 12, "text": "Welcome only"},
            {"id": 13, "text": "Anime Bot only"},
        ]

        matched = select_matching_response(messages, 11, ("Welcome", "Anime Bot"))

        self.assertIsNone(matched)

    def test_custom_scenarios_are_preserved(self) -> None:
        """Allow callers to override the default ping scenarios.

        Args:
            None.

        Returns:
            None.
        """

        scenario = PingScenario("/custom", ("ready",))
        config = PingConfig(
            api_id=1,
            api_hash="hash",
            bot_username="bot",
            session_string="session",
            timeout_seconds=5.0,
            scenarios=(scenario,),
        )

        self.assertEqual(config.scenarios, (scenario,))


if __name__ == "__main__":
    unittest.main()
