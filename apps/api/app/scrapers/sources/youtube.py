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

# Pre-seeded map: brand keywords → YouTube channel IDs of known real estate channels
BRAND_CHANNEL_MAP: dict[str, list[str]] = {
    "square yards": ["UCdS4ctBMqGJDJaUBBfmqzqA", "UC3pTRhvQhYfMnVe8HMKP7aA"],
    "99acres": ["UC5_O0oi13gnRJMQiUZkY7Eg"],
    "magicbricks": ["UCc3rEubF6zHMjJHGK9j89Xg"],
    "housing": ["UCVwMlECHLTVSYMJ3tPMH7Dg"],
    "nobroker": ["UCPqk9W7JkXwAMjEZpBJBvJw"],
    "commonfloor": ["UCgDfRwlxYMSzAVRDSNb3kgA"],
    "proptiger": ["UC7pJz6V5xhCTKNflexmBMqQ"],
}

FALLBACK_CHANNELS = [
    "UCdS4ctBMqGJDJaUBBfmqzqA",  # Square Yards official
    "UC5_O0oi13gnRJMQiUZkY7Eg",  # 99acres
]

YOUTUBE_FEED_BASE = "https://www.youtube.com/feeds/videos.xml"


class YouTubeScraper(BaseSourceScraper):
    source_name = "youtube"
    parser_version = "youtube-rss-v1"

    def _build_query(self, target_brand: str) -> str:
        return f'"{target_brand}" property review'

    def _get_channel_ids(self, target_brand: str) -> list[str]:
        brand_lower = target_brand.lower().strip()
        for key, channels in BRAND_CHANNEL_MAP.items():
            if key in brand_lower or brand_lower in key:
                return channels
        return FALLBACK_CHANNELS

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

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)

        stub_text = (
            f"The {target_brand} project walkthrough looked good, but users in comments "
            f"complained about outdated inventory."
        )
        source_url = "https://youtube.com/watch?v=example1"
        external_id = f"youtube-{target_brand.lower().replace(' ', '-')}-001"

        return [
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="video",
                external_id=external_id,
                author_name="yt_channel_1",
                source_url=source_url,
                published_at=None,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=f"{self.parser_version}-stub",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=external_id,
                    source_url=source_url,
                    raw_text=stub_text,
                ),
                raw_payload_json={"stub": True, "reason": fallback_reason},
                raw_text=stub_text,
                cleaned_text=stub_text,
                language="en",
                metadata_json={
                    "video_id": "example1",
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                },
            )
        ]

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            return self._build_stub_items(
                target_brand=target_brand,
                fallback_reason="Live fetch disabled in settings",
            )

        try:
            channel_ids = self._get_channel_ids(target_brand)
            all_items: list[ScrapedItem] = []

            for channel_id in channel_ids:
                try:
                    xml_text = self._fetch_channel_feed(channel_id)
                    items = self._parse_channel_feed(xml_text, target_brand, channel_id)
                    all_items.extend(items)
                    if len(all_items) >= settings.scraper_max_items_per_source:
                        break
                except Exception:
                    continue

            if all_items:
                return all_items[:settings.scraper_max_items_per_source]

            if settings.scraper_fail_open_to_stub:
                return self._build_stub_items(
                    target_brand=target_brand,
                    fallback_reason="No items from YouTube RSS feeds",
                )
            return []

        except Exception as exc:
            if settings.scraper_fail_open_to_stub:
                return self._build_stub_items(
                    target_brand=target_brand,
                    fallback_reason=str(exc),
                )
            raise