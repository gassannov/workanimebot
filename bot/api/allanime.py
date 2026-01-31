"""
AllAnime GraphQL API Client.

Mirrors ani-cli's GraphQL queries exactly for easy synchronization.

Reference: ani-cli lines 233-262
"""

import json
import aiohttp
from typing import List, Optional
from dataclasses import dataclass

from ..config import config


@dataclass
class AnimeResult:
    """Represents a search result anime."""
    id: str
    name: str
    available_episodes_sub: int
    available_episodes_dub: int


@dataclass
class EpisodeSource:
    """Represents an episode video source."""
    source_name: str
    source_url: str  # Encrypted URL


class AllAnimeClient:
    """GraphQL client for AllAnime API - mirrors ani-cli approach."""

    # GraphQL queries - EXACTLY as in ani-cli for easy updates
    # Reference: ani-cli line 235
    SEARCH_QUERY = '''query($search: SearchInput $limit: Int $page: Int $translationType: VaildTranslationTypeEnumType $countryOrigin: VaildCountryOriginEnumType) { shows(search: $search limit: $limit page: $page translationType: $translationType countryOrigin: $countryOrigin) { edges { _id name availableEpisodes __typename } }}'''

    # Reference: ani-cli line 258
    EPISODES_QUERY = '''query ($showId: String!) { show(_id: $showId) { _id availableEpisodesDetail }}'''

    # Reference: ani-cli line 211
    EPISODE_URL_QUERY = '''query ($showId: String!, $translationType: VaildTranslationTypeEnumType!, $episodeString: String!) { episode(showId: $showId translationType: $translationType episodeString: $episodeString) { episodeString sourceUrls }}'''

    def __init__(self):
        self.api_url = config.ALLANIME_API
        self.headers = {
            "User-Agent": config.USER_AGENT,
            "Referer": config.ALLANIME_REFERER,
        }

    async def search(self, query: str, translation_type: str = "sub") -> List[AnimeResult]:
        """
        Search anime by query.

        Mirrors search_anime() in ani-cli (lines 233-239).

        Args:
            query: Search query string
            translation_type: "sub" or "dub"

        Returns:
            List of AnimeResult objects
        """
        variables = {
            "search": {
                "allowAdult": False,
                "allowUnknown": False,
                "query": query,
            },
            "limit": config.SEARCH_LIMIT,
            "page": 1,
            "translationType": translation_type,
            "countryOrigin": "ALL",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.api_url,
                params={
                    "variables": json.dumps(variables),
                    "query": self.SEARCH_QUERY,
                },
                headers=self.headers,
            ) as resp:
                data = await resp.json()

        results = []
        edges = data.get("data", {}).get("shows", {}).get("edges", [])

        for edge in edges:
            available = edge.get("availableEpisodes", {})
            # Only include anime that has episodes for the requested type
            sub_eps = available.get("sub", 0) or 0
            dub_eps = available.get("dub", 0) or 0

            if (translation_type == "sub" and sub_eps > 0) or \
               (translation_type == "dub" and dub_eps > 0):
                results.append(AnimeResult(
                    id=edge["_id"],
                    name=edge["name"],
                    available_episodes_sub=sub_eps,
                    available_episodes_dub=dub_eps,
                ))

        return results

    async def get_episodes(self, show_id: str, translation_type: str = "sub") -> List[str]:
        """
        Get episode list for a show.

        Mirrors episodes_list() in ani-cli (lines 256-262).

        Args:
            show_id: The anime's ID
            translation_type: "sub" or "dub"

        Returns:
            List of episode numbers (as strings, sorted)
        """
        variables = {"showId": show_id}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.api_url,
                params={
                    "variables": json.dumps(variables),
                    "query": self.EPISODES_QUERY,
                },
                headers=self.headers,
            ) as resp:
                data = await resp.json()

        detail = data.get("data", {}).get("show", {}).get("availableEpisodesDetail", {})
        episodes = detail.get(translation_type, [])

        if not episodes:
            return []

        # Sort numerically (handle decimal episodes like "5.5")
        def sort_key(ep):
            try:
                return float(ep)
            except (ValueError, TypeError):
                return 0

        return sorted(episodes, key=sort_key)

    async def get_episode_sources(
        self,
        show_id: str,
        episode: str,
        translation_type: str = "sub",
    ) -> List[EpisodeSource]:
        """
        Get episode source URLs.

        Mirrors get_episode_url() in ani-cli (lines 208-230).

        Args:
            show_id: The anime's ID
            episode: Episode number string
            translation_type: "sub" or "dub"

        Returns:
            List of EpisodeSource objects with encrypted URLs
        """
        variables = {
            "showId": show_id,
            "translationType": translation_type,
            "episodeString": episode,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.api_url,
                params={
                    "variables": json.dumps(variables),
                    "query": self.EPISODE_URL_QUERY,
                },
                headers=self.headers,
            ) as resp:
                data = await resp.json()

        sources = []
        episode_data = data.get("data", {}).get("episode", {})
        source_urls = episode_data.get("sourceUrls", [])

        if not source_urls:
            return []

        for source in source_urls:
            source_url = source.get("sourceUrl", "")
            source_name = source.get("sourceName", "")

            # Skip empty sources
            if not source_url:
                continue

            # Remove leading "--" if present
            if source_url.startswith("--"):
                source_url = source_url[2:]

            sources.append(EpisodeSource(
                source_name=source_name,
                source_url=source_url,
            ))

        return sources


# Singleton instance
api_client = AllAnimeClient()
