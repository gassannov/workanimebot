"""Tests for the Telegram search handler as an adapter layer."""

import unittest
from unittest.mock import patch

from anime_app.models import AnimeResult
from bot.handlers.search import perform_search
from bot.utils.state import ConversationState, sessions


class FakeService:
    """Service double used by Telegram handler tests.

    Example:
        service = FakeService()
        results = await service.search_anime("One Piece", "sub")
    """

    def __init__(self) -> None:
        """Initialize fake service state.

        Args:
            None.

        Returns:
            None.
        """

        self.calls = []

    async def search_anime(
        self,
        query: str,
        translation_type: str,
    ) -> list[AnimeResult]:
        """Return deterministic search results for tests.

        Args:
            query: Search text.
            translation_type: Requested language.

        Returns:
            list[AnimeResult]: Fake search results.
        """

        self.calls.append((query, translation_type))
        return [AnimeResult("anime-1", "One Piece", 10, 5)]


class FakeSentMessage:
    """Telegram message double that records edits.

    Example:
        message = FakeSentMessage()
        await message.edit_text("updated")
    """

    def __init__(self) -> None:
        """Initialize recorded message state.

        Args:
            None.

        Returns:
            None.
        """

        self.edits = []

    async def edit_text(self, text: str, **kwargs) -> None:
        """Record a message edit call.

        Args:
            text: Updated message text.
            **kwargs: Telegram message edit options.

        Returns:
            None.
        """

        self.edits.append((text, kwargs))


class FakeEffectiveMessage:
    """Telegram effective message double for reply flow tests.

    Example:
        message = FakeEffectiveMessage()
        sent = await message.reply_text("hello")
    """

    def __init__(self) -> None:
        """Initialize fake reply state.

        Args:
            None.

        Returns:
            None.
        """

        self.sent_messages = []

    async def reply_text(self, text: str, **kwargs) -> FakeSentMessage:
        """Return a fake sent message object.

        Args:
            text: Reply text.
            **kwargs: Telegram reply options.

        Returns:
            FakeSentMessage: Reply placeholder used by the handler.
        """

        sent_message = FakeSentMessage()
        self.sent_messages.append((text, kwargs, sent_message))
        return sent_message


class FakeUser:
    """Minimal user object for handler tests.

    Example:
        user = FakeUser(42)
    """

    def __init__(self, user_id: int) -> None:
        """Store the fake user identifier.

        Args:
            user_id: Telegram user identifier.

        Returns:
            None.
        """

        self.id = user_id


class FakeUpdate:
    """Minimal Telegram update used by handler tests.

    Example:
        update = FakeUpdate(42)
    """

    def __init__(self, user_id: int) -> None:
        """Create effective message and user objects for tests.

        Args:
            user_id: Telegram user identifier.

        Returns:
            None.
        """

        self.effective_user = FakeUser(user_id)
        self.effective_message = FakeEffectiveMessage()


class SearchHandlerTests(unittest.IsolatedAsyncioTestCase):
    """Verify the Telegram handler uses AnimeService as an adapter boundary.

    Example:
        test_case = SearchHandlerTests()
    """

    async def asyncSetUp(self) -> None:
        """Reset session state before each test.

        Args:
            None.

        Returns:
            None.
        """

        sessions.clear(42)

    async def test_perform_search_uses_application_service(self) -> None:
        """Ensure perform_search delegates search to the application layer.

        Args:
            None.

        Returns:
            None.
        """

        update = FakeUpdate(42)
        context = object()
        fake_service = FakeService()

        with patch("bot.handlers.search.anime_service", fake_service):
            state = await perform_search(update, context, "One Piece")

        session = sessions.get(42)
        sent_text, sent_kwargs, sent_message = update.effective_message.sent_messages[0]

        self.assertEqual(state, ConversationState.SELECTING_ANIME)
        self.assertEqual(fake_service.calls, [("One Piece", "sub")])
        self.assertEqual(session.search_results[0].title, "One Piece")
        self.assertIn("Searching for", sent_text)
        self.assertIn("reply_markup", sent_message.edits[0][1])
