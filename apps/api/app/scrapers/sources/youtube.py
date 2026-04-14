import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from app.core.config import get_settings
from app.scrapers.base import BaseSourceScraper
from app.scrapers.http_client import RetryingHttpClient
from app.scrapers.types import ScrapedItem
from app.scrapers.utils import (
    build_dedupe_key,
    build_payload_snapshot,
    normalize_whitespace,
)

logger = logging.getLogger(__name__)

# Verified YouTube channel IDs for Indian real estate brands
# Format: UC... (channel IDs found via youtube.com/@handle page)
BRAND_CHANNEL_MAP: dict[str, list[str]] = {
    "square yards": [
        "UCT4lJHHMSFHuuHFeyZxAuKA",  # Square Yards official (@squareyards)
    ],
    "99acres": [
        "UC4K4pCcwkz5fOsAzTMvnMUQ",  # 99acres official (@99acres)
    ],
    "magicbricks": [
        "UCIwu4PBhEM-EFnBqKbXNi6A",  # MagicBricks official (@magicbricks)
    ],
    "housing": [
        "UCdkl5YM_8kn4Guk0R5IVMFA",  # Housing.com (@housingdotcom)
    ],
    "nobroker": [
        "UCC5AHmMM39xl7pHQSdwjPtQ",  # NoBroker official (@NoBroker)
    ],
    "commonfloor": [
        "UCgDfRwlxYMSzAVRDSNb3kgA",  # CommonFloor
    ],
    "proptiger": [
        "UCjXCzVHXYF0YdkSwzV5HKOA",  # PropTiger official
    ],
}

YOUTUBE_FEED_BASE = "https://www.youtube.com/feeds/videos.xml"
YOUTUBE_SEARCH_URL = "https://www.youtube.com/results"


class YouTubeScraper(BaseSourceScraper):
    source_name = "youtube"
    parser_version = "youtube-rss-v1"

    def _build_query(self, target_brand: str) -> str:
        return f'"{target_brand}" property review'

    def _build_search_query(self, target_brand: str) -> str:
        return f"{target_brand} real estate review India"

    def _get_channel_ids(self, target_brand: str) -> list[str]:
        brand_lower = target_brand.lower().strip()
        for key, channels in BRAND_CHANNEL_MAP.items():
            if key in brand_lower or brand_lower in key:
                return channels
        return []

    def _build_headers(self) -> dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/atom+xml, application/xml, text/xml, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def _fetch_channel_feed(self, channel_id: str) -> str:
        return RetryingHttpClient.get_text(
            YOUTUBE_FEED_BASE,
            params={"channel_id": channel_id},
            headers=self._build_headers(),
        )

    def _parse_channel_feed(self, xml_text: str, target_brand: str, channel_id: str) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        settings = get_settings()

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
            "media": "http://search.yahoo.com/mrss/",
        }

        entries = root.findall("atom:entry", ns)
        if not entries:
            entries = root.findall(".//entry")

        parsed_items: list[ScrapedItem] = []

        for entry in entries[:settings.scraper_max_items_per_source]:
            # Video ID
            video_id_el = entry.find("yt:videoId", ns) or entry.find("videoId")
            video_id = (video_id_el.text or "").strip() if video_id_el is not None else ""

            # Title
            title_el = entry.find("atom:title", ns) or entry.find("title")
            title = (title_el.text or "").strip() if title_el is not None else ""

            # Description from media:description
            desc_el = (entry.find("media:group/media:description", ns)
                      or entry.find(".//description"))
            description = (desc_el.text or "").strip() if desc_el is not None else ""
            description = normalize_whitespace(description)

            combined = "\n\n".join(p for p in [title, description] if p).strip()
            if not combined:
                continue

            source_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
            external_id = f"yt-{video_id}" if video_id else None

            # Published date
            published_el = entry.find("atom:published", ns) or entry.find("published")
            published_at = None
            if published_el is not None and published_el.text:
                try:
                    published_at = datetime.fromisoformat(
                        published_el.text.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            # Channel name
            author_el = entry.find("atom:author/atom:name", ns) or entry.find("author/name")
            author = (author_el.text or "").strip() if author_el is not None else None

            parsed_items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="video",
                external_id=external_id,
                author_name=author,
                source_url=source_url,
                published_at=published_at,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=self.parser_version,
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=external_id,
                    source_url=source_url,
                    raw_text=combined,
                ),
                raw_payload_json=build_payload_snapshot({
                    "video_id": video_id,
                    "channel_id": channel_id,
                    "title": title,
                    "description": description,
                }),
                raw_text=combined,
                cleaned_text=combined,
                language="en",
                metadata_json={
                    "video_id": video_id,
                    "channel_id": channel_id,
                    "fetch_mode": "live",
                    "source_format": "rss",
                },
            ))

        return parsed_items

    # ------------------------------------------------------------------
    # Tier 2: YouTube search page (scrape ytInitialData for video IDs)
    # ------------------------------------------------------------------

    def _scrape_via_search(self, target_brand: str) -> list[ScrapedItem]:
        """
        Scrape YouTube search results page and extract video IDs from the
        embedded ytInitialData JSON blob. Then fetch each video's RSS entry.
        No API key required.
        """
        settings = get_settings()
        search_query = self._build_search_query(target_brand)
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)

        try:
            headers = {
                **self._build_headers(),
                "Accept-Language": "en-US,en;q=0.9",
            }
            html = RetryingHttpClient.get_text(
                YOUTUBE_SEARCH_URL,
                params={"search_query": search_query, "sp": "EgIIAQ%3D%3D"},  # Sort by upload date
                headers=headers,
            )

            # Extract ytInitialData JSON from the page
            match = re.search(r"var ytInitialData\s*=\s*(\{.+?\});\s*(?:var|</script>)", html, re.DOTALL)
            if not match:
                # Try alternative pattern
                match = re.search(r"ytInitialData\s*=\s*(\{.+?\});", html, re.DOTALL)
            if not match:
                logger.warning("YouTube search: could not extract ytInitialData for '%s'", target_brand)
                return []

            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.warning("YouTube search: ytInitialData JSON parse failed for '%s'", target_brand)
                return []

            # Navigate the ytInitialData structure to find video renderers
            video_ids: list[str] = []
            video_titles: dict[str, str] = {}

            def extract_video_ids(obj: object) -> None:
                if isinstance(obj, dict):
                    if "videoId" in obj:
                        vid = obj["videoId"]
                        if vid not in video_ids:
                            video_ids.append(vid)
                        # Try to get title
                        title_obj = obj.get("title") or {}
                        if isinstance(title_obj, dict):
                            runs = title_obj.get("runs") or [{}]
                            if runs and isinstance(runs[0], dict):
                                video_titles[vid] = runs[0].get("text", "")
                    for v in obj.values():
                        extract_video_ids(v)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_video_ids(item)

            extract_video_ids(data)
            video_ids = video_ids[:settings.scraper_max_items_per_source]

            if not video_ids:
                logger.warning("YouTube search: no video IDs found for '%s'", target_brand)
                return []

            items: list[ScrapedItem] = []
            for video_id in video_ids:
                title = video_titles.get(video_id, "")
                source_url = f"https://www.youtube.com/watch?v={video_id}"
                ext_id = f"yt-search-{video_id}"
                combined = title or f"YouTube video about {target_brand}"
                items.append(ScrapedItem(
                    source_name=self.source_name,
                    platform_name=target_brand,
                    content_type="video",
                    external_id=ext_id,
                    author_name=None,
                    source_url=source_url,
                    published_at=None,
                    fetched_at=fetched_at,
                    source_query=source_query,
                    parser_version="youtube-search-v1",
                    dedupe_key=build_dedupe_key(
                        source_name=self.source_name,
                        external_id=ext_id,
                        source_url=source_url,
                        raw_text=combined,
                    ),
                    raw_payload_json=build_payload_snapshot({"video_id": video_id, "title": title}),
                    raw_text=combined,
                    cleaned_text=combined,
                    language="en",
                    metadata_json={
                        "video_id": video_id,
                        "fetch_mode": "search_scrape",
                        "search_query": search_query,
                    },
                ))

            logger.info("YouTube search: found %d videos for '%s'", len(items), target_brand)
            return items

        except Exception as exc:
            logger.warning("YouTube search scrape failed for '%s': %s", target_brand, exc)
            return []

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        brand_slug = target_brand.lower().replace(" ", "-")

        stubs = [
            ("yt-stub-ex1", "yt_reviewer_1",
             f"{target_brand} Project Walkthrough Review 2024",
             f"We visited the {target_brand} listed properties in Bangalore. The listings look good on app "
             f"but on-ground reality is different — 3 out of 5 units were already sold. Very misleading."),
            ("yt-stub-ex2", "yt_reviewer_2",
             f"{target_brand} App Review: Is It Worth Using?",
             f"I have been using {target_brand} for 3 months. The app is slow to load and the search "
             f"filters don't work well. Agents listed don't respond to calls or messages."),
            ("yt-stub-ex3", "yt_reviewer_3",
             f"My Experience Buying a Home Through {target_brand}",
             f"The {target_brand} platform showed budget-friendly options but hidden charges were added "
             f"later. The final price was 15% more than what was shown. Not transparent at all."),
            ("yt-stub-ex4", "yt_reviewer_4",
             f"{target_brand} vs Competitors: Honest Review",
             f"Comparing {target_brand} with other portals — the photo quality is lower and many listings "
             f"lack RERA numbers. Customer support took 4 days to respond to my query."),
            ("yt-stub-ex5", "yt_reviewer_5",
             f"Fraud Alert: My {target_brand} Experience",
             f"Lost my token money after booking through {target_brand}. The builder was not verified. "
             f"Platform does not take responsibility. Beware of unverified listings."),
        ]

        items = []
        for video_id, author, title, description in stubs:
            ext_id = f"youtube-{brand_slug}-{video_id}"
            source_url = f"https://youtube.com/watch?v={video_id}"
            combined = f"{title}\n\n{description}"
            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="video",
                external_id=ext_id,
                author_name=author,
                source_url=source_url,
                published_at=None,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=f"{self.parser_version}-stub",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=ext_id,
                    source_url=source_url,
                    raw_text=combined,
                ),
                raw_payload_json={"stub": True, "reason": fallback_reason, "title": title},
                raw_text=combined,
                cleaned_text=combined,
                language="en",
                metadata_json={
                    "video_id": video_id,
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                },
            ))
        return items

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            logger.info("YouTube: live fetch disabled, using stub data")
            return self._build_stub_items(
                target_brand=target_brand,
                fallback_reason="Live fetch disabled in settings",
            )

        # Tier 1: Known brand channel RSS feeds
        channel_ids = self._get_channel_ids(target_brand)
        if channel_ids:
            all_items: list[ScrapedItem] = []
            for channel_id in channel_ids:
                try:
                    xml_text = self._fetch_channel_feed(channel_id)
                    items = self._parse_channel_feed(xml_text, target_brand, channel_id)
                    all_items.extend(items)
                    if len(all_items) >= settings.scraper_max_items_per_source:
                        break
                except Exception as exc:
                    logger.warning("YouTube channel %s failed: %s", channel_id, exc)
                    continue

            if all_items:
                logger.info("YouTube RSS: fetched %d items for '%s'", len(all_items), target_brand)
                return all_items[:settings.scraper_max_items_per_source]
            logger.warning("YouTube RSS: 0 items from channel feeds for '%s'", target_brand)

        # Tier 2: YouTube search page scraping
        search_items = self._scrape_via_search(target_brand)
        if search_items:
            return search_items[:settings.scraper_max_items_per_source]

        logger.warning("YouTube: all live tiers returned 0 items for '%s'", target_brand)

        # Tier 3: Stub fallback (only if explicitly enabled)
        if settings.scraper_fail_open_to_stub:
            return self._build_stub_items(
                target_brand=target_brand,
                fallback_reason="All live YouTube tiers failed",
            )
        return []