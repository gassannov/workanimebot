"""
Video provider extractors.

Mirrors get_links() and generate_link() from ani-cli.

Reference: ani-cli lines 138-183
"""

import re
import aiohttp
from typing import List, Optional
from dataclasses import dataclass

from ..config import config
from .decoder import decode_provider_url


@dataclass
class VideoLink:
    """Represents an extracted video link."""
    quality: str  # e.g., "1080p", "720p"
    url: str
    provider: str
    format: str  # "m3u8" or "mp4"
    referer: Optional[str] = None
    subtitle_url: Optional[str] = None


# Provider name patterns (from ani-cli's generate_link, lines 176-180)
PROVIDER_PATTERNS = {
    "Default :": "wixmp",      # wixmp(default)(m3u8)(multi) -> (mp4)(multi)
    "Yt-mp4 :": "youtube",     # youtube(mp4)(single)
    "S-mp4 :": "sharepoint",   # sharepoint(mp4)(single)
    "Luf-Mp4 :": "hianime",    # hianime(m3u8)(multi)
}


class ProviderExtractor:
    """Extract video URLs from providers - mirrors get_links() in ani-cli."""

    def __init__(self):
        self.base_url = f"https://{config.ALLANIME_BASE}"
        self.headers = {
            "User-Agent": config.USER_AGENT,
            "Referer": config.ALLANIME_REFERER,
        }

    async def extract_from_source(self, source_name: str, encrypted_url: str) -> List[VideoLink]:
        """
        Extract video links from a source.

        Args:
            source_name: The source name (e.g., "Default", "Yt-mp4")
            encrypted_url: The encrypted provider URL

        Returns:
            List of VideoLink objects
        """
        # Decode the URL
        decoded_url = decode_provider_url(encrypted_url)

        if not decoded_url:
            return []

        # Determine provider type
        provider = "unknown"
        for pattern, name in PROVIDER_PATTERNS.items():
            if pattern.replace(" :", "") in source_name:
                provider = name
                break

        # Build full URL
        full_url = f"{self.base_url}{decoded_url}"

        try:
            return await self._extract_links(full_url, provider)
        except Exception as e:
            print(f"Error extracting from {provider}: {e}")
            return []

    async def _extract_links(self, url: str, provider: str) -> List[VideoLink]:
        """
        Extract video links from a provider URL.

        Mirrors the get_links() function from ani-cli (lines 138-165).
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status != 200:
                    return []
                response_text = await resp.text()

        links = []

        # Check for different response types
        if "repackager.wixmp.com" in response_text:
            links = self._parse_wixmp(response_text, provider)
        elif "master.m3u8" in response_text or "hls" in response_text.lower():
            links = await self._parse_m3u8(response_text, provider)
        elif "tools.fast4speed.rsvp" in url:
            # YouTube proxy
            links.append(VideoLink(
                quality="auto",
                url=url,
                provider="youtube",
                format="mp4",
                referer=config.ALLANIME_REFERER,
            ))
        else:
            links = self._parse_direct(response_text, provider)

        return links

    def _parse_wixmp(self, response: str, provider: str) -> List[VideoLink]:
        """
        Parse wixmp provider response.

        Mirrors ani-cli lines 144-149.
        """
        links = []

        # Find link and resolution patterns
        # Pattern: "link":"URL"..."resolutionStr":"QUALITY"
        for match in re.finditer(
            r'"link":"([^"]*)"[^}]*"resolutionStr":"([^"]*)"',
            response
        ):
            url = match.group(1).replace("\\u002F", "/").replace("\\", "")
            quality = match.group(2)

            # Process wixmp URL (remove repackager prefix, clean up)
            if "repackager.wixmp.com" in url:
                # Extract the actual video URL
                url = re.sub(r'repackager\.wixmp\.com/', '', url)
                url = re.sub(r'\.urlset.*', '', url)

            links.append(VideoLink(
                quality=quality,
                url=url,
                provider=provider,
                format="mp4",
            ))

        # Also try to extract from different format
        if not links:
            # Try alternate extraction pattern
            extract_match = re.search(r'"link":"([^"]*)"', response)
            if extract_match:
                url = extract_match.group(1).replace("\\u002F", "/").replace("\\", "")
                links.append(VideoLink(
                    quality="auto",
                    url=url,
                    provider=provider,
                    format="mp4",
                ))

        return links

    async def _parse_m3u8(self, response: str, provider: str) -> List[VideoLink]:
        """
        Parse m3u8/HLS playlist and extract quality variants.

        Mirrors ani-cli lines 151-158.
        """
        links = []

        # Extract referer for m3u8 streams
        referer_match = re.search(r'"Referer":"([^"]*)"', response)
        m3u8_referer = referer_match.group(1) if referer_match else config.ALLANIME_REFERER

        # Extract HLS URL - try multiple patterns
        hls_url = None

        # Pattern 1: hls object with url
        hls_match = re.search(r'"hls"[^}]*"url":"([^"]*)"', response)
        if hls_match:
            hls_url = hls_match.group(1)

        # Pattern 2: direct link with m3u8
        if not hls_url:
            m3u8_match = re.search(r'"link":"([^"]*\.m3u8[^"]*)"', response)
            if m3u8_match:
                hls_url = m3u8_match.group(1)

        # Pattern 3: any URL containing master.m3u8
        if not hls_url:
            master_match = re.search(r'(https?://[^"]*master\.m3u8[^"]*)', response)
            if master_match:
                hls_url = master_match.group(1)

        if not hls_url:
            return links

        # Clean URL
        hls_url = hls_url.replace("\\u002F", "/").replace("\\", "")

        # Try to fetch the m3u8 playlist to get quality variants
        try:
            async with aiohttp.ClientSession() as session:
                headers = {**self.headers, "Referer": m3u8_referer}
                async with session.get(hls_url, headers=headers) as resp:
                    if resp.status == 200:
                        m3u8_content = await resp.text()

                        if "#EXTM3U" in m3u8_content:
                            base_url = hls_url.rsplit("/", 1)[0] + "/"

                            # Parse quality variants
                            lines = m3u8_content.split("\n")
                            for i, line in enumerate(lines):
                                if line.startswith("#EXT-X-STREAM"):
                                    res_match = re.search(r"RESOLUTION=\d+x(\d+)", line)
                                    if res_match and i + 1 < len(lines):
                                        quality = res_match.group(1) + "p"
                                        stream_url = lines[i + 1].strip()

                                        if stream_url and not stream_url.startswith("#"):
                                            if not stream_url.startswith("http"):
                                                stream_url = base_url + stream_url

                                            links.append(VideoLink(
                                                quality=quality,
                                                url=stream_url,
                                                provider=provider,
                                                format="m3u8",
                                                referer=m3u8_referer,
                                            ))
        except Exception:
            pass

        # If no quality variants found, add the master URL
        if not links:
            links.append(VideoLink(
                quality="auto",
                url=hls_url,
                provider=provider,
                format="m3u8",
                referer=m3u8_referer,
            ))

        # Check for subtitles
        subtitle_match = re.search(
            r'"subtitles":\[.*?"lang":"en".*?"src":"([^"]*)"',
            response,
        )
        if subtitle_match and links:
            subtitle_url = subtitle_match.group(1).replace("\\u002F", "/").replace("\\", "")
            for link in links:
                link.subtitle_url = subtitle_url

        return links

    def _parse_direct(self, response: str, provider: str) -> List[VideoLink]:
        """Parse direct video links."""
        links = []

        # Find link and resolution pairs
        for match in re.finditer(
            r'"link":"([^"]*)"[^}]*"resolutionStr":"([^"]*)"',
            response,
        ):
            url = match.group(1).replace("\\u002F", "/").replace("\\", "")
            quality = match.group(2)

            # Skip empty or invalid URLs
            if not url or url == "null":
                continue

            # Determine format
            fmt = "m3u8" if ".m3u8" in url else "mp4"

            links.append(VideoLink(
                quality=quality,
                url=url,
                provider=provider,
                format=fmt,
            ))

        # If no links with resolution, try to get any link
        if not links:
            link_match = re.search(r'"link":"([^"]+)"', response)
            if link_match:
                url = link_match.group(1).replace("\\u002F", "/").replace("\\", "")
                if url and url != "null":
                    fmt = "m3u8" if ".m3u8" in url else "mp4"
                    links.append(VideoLink(
                        quality="auto",
                        url=url,
                        provider=provider,
                        format=fmt,
                    ))

        return links

    def select_best_quality(
        self,
        links: List[VideoLink],
        preferred: str = "best",
    ) -> Optional[VideoLink]:
        """
        Select link matching preferred quality.

        Mirrors select_quality() in ani-cli (lines 185-205).
        """
        if not links:
            return None

        # Sort by quality (numeric extraction, descending)
        def quality_key(link):
            match = re.search(r"(\d+)", link.quality)
            return int(match.group(1)) if match else 0

        sorted_links = sorted(links, key=quality_key, reverse=True)

        if preferred == "best":
            return sorted_links[0]
        elif preferred == "worst":
            return sorted_links[-1]
        else:
            # Find specific quality
            for link in sorted_links:
                if preferred in link.quality:
                    return link
            # Default to best if not found
            return sorted_links[0]


# Singleton instance
provider_extractor = ProviderExtractor()
