"""
Conversation state management for the search -> anime -> episode flow.

Uses in-memory storage for MVP (no persistence).
"""

from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Dict, List, Optional


class ConversationState(IntEnum):
    """States for the conversation flow."""

    WAITING_SEARCH_QUERY = auto()
    SELECTING_ANIME = auto()
    SELECTING_EPISODE = auto()
    SELECTING_QUALITY = auto()


@dataclass
class UserSession:
    """Stores user's current session data."""

    # Search state
    search_query: Optional[str] = None
    search_results: List = field(default_factory=list)

    # Selected anime
    selected_anime_id: Optional[str] = None
    selected_anime_name: Optional[str] = None

    # Episode state
    episodes: List[str] = field(default_factory=list)
    selected_episode: Optional[str] = None

    # Video links
    video_streams: List = field(default_factory=list)

    # Preferences
    translation_type: str = "sub"

    # Pagination
    anime_page: int = 0
    episode_page: int = 0


class SessionManager:
    """Manages user sessions (in-memory for MVP)."""

    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}

    def get(self, user_id: int) -> UserSession:
        """Get or create session for user."""
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession()
        return self._sessions[user_id]

    def clear(self, user_id: int) -> None:
        """Clear user's session."""
        if user_id in self._sessions:
            del self._sessions[user_id]

    def reset_search(self, user_id: int) -> None:
        """Reset search-related state while keeping preferences."""
        session = self.get(user_id)
        translation = session.translation_type
        self._sessions[user_id] = UserSession(translation_type=translation)


# Global session manager instance
sessions = SessionManager()
