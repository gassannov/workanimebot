"""
Conversation state management for the search -> anime -> episode flow.

Uses in-memory storage for MVP (no persistence).
"""

from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Dict, List, Optional

from anime_app.models import AnimeResult, StreamOption


class ConversationState(IntEnum):
    """States for the conversation flow.

    Example:
        state = ConversationState.SELECTING_ANIME
    """

    WAITING_SEARCH_QUERY = auto()
    SELECTING_ANIME = auto()
    SELECTING_EPISODE = auto()
    SELECTING_QUALITY = auto()


@dataclass
class UserSession:
    """Store one user's current bot session state.

    Example:
        session = UserSession(translation_type="sub")
    """

    # Search state
    search_query: Optional[str] = None
    search_results: List[AnimeResult] = field(default_factory=list)

    # Selected anime
    selected_anime_id: Optional[str] = None
    selected_anime_name: Optional[str] = None

    # Episode state
    episodes: List[str] = field(default_factory=list)
    selected_episode: Optional[str] = None

    # Video links
    video_streams: List[StreamOption] = field(default_factory=list)

    # Preferences
    translation_type: str = "sub"

    # Pagination
    anime_page: int = 0
    episode_page: int = 0


class SessionManager:
    """Manage in-memory user sessions for bot conversations.

    Example:
        manager = SessionManager()
        session = manager.get(123)
    """

    def __init__(self):
        """Initialize the in-memory session store.

        Args:
            None.

        Returns:
            None.
        """

        self._sessions: Dict[int, UserSession] = {}

    def get(self, user_id: int) -> UserSession:
        """Get or create a session for a user.

        Args:
            user_id: Telegram user identifier.

        Returns:
            UserSession: Existing or newly created session.
        """

        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession()
        return self._sessions[user_id]

    def clear(self, user_id: int) -> None:
        """Remove a user's session from memory.

        Args:
            user_id: Telegram user identifier.

        Returns:
            None.
        """

        if user_id in self._sessions:
            del self._sessions[user_id]

    def reset_search(self, user_id: int) -> None:
        """Reset search state while preserving user preferences.

        Args:
            user_id: Telegram user identifier.

        Returns:
            None.
        """

        session = self.get(user_id)
        translation = session.translation_type
        self._sessions[user_id] = UserSession(translation_type=translation)


# Global session manager instance
sessions = SessionManager()
