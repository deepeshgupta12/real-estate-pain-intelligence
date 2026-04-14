"""
YouTube scraper — 3-tier strategy:

Tier 1: YouTube Data API v3 (official, free 10k units/day, always works)
         Requires YOUTUBE_DATA_API_KEY in .env
         Get key: console.cloud.google.com → Enable "YouTube Data API v3" → Credentials

Tier 2: yt-dlp search (no API key, but YouTube may block in some environments)

Tier 3: Stub data (only when SCRAPER_FAIL_OPEN_TO_STUB=true)
"""

import logging
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


class YouTubeScraper(BaseSourceScraper):
    source_name = "youtube"
    parser_version = "youtube-v3api-v1"

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def _build_query(self, target_brand: str) -> str:
        return f'"{target_brand}" real estate review'

    def _build_search_query(self, target_brand: str) -> str:
        return f"{target_brand} real estate app review India"

    # ------------------------------------------------------------------
    # Tier 1: YouTube Data API v3 (official — no blocking)
    # ------------------------------------------------------------------

    def _scrape_via_data_api(self, target_brand: str) -> list[ScrapedItem]:
        """
        Uses the official YouTube Data API v3 search endpoint.
        Free quota: 10,000 units/day (~100 search calls).
        Set YOUTUBE_DATA_API_KEY in .env to enable.
        """
        settings = get_settings()

        if not settings.youtube_data_api_key:
            logger.debug("YouTube Data API key not set — skipping Tier 1")
            return []

        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        search_q = self._build_search_query(target_brand)

        try:
            payload = RetryingHttpClient.get_json(
                f"{settings.youtube_data_api_base_url}/search",
                params={
                    "part": "snippet",
                    "q": search_q,
                    "type": "video",
                    "maxResults": settings.scraper_max_items_per_source,
                    "relevanceLanguage": "en",
                    "regionCode": "IN",
                    "key": settings.youtube_data_api_key,
                },
                use_browser_headers=False,
            )
        except Exception as exc:
            logger.warning("YouTube Data API search failed for '%s': %s", target_brand, exc)
            return []

        items_data = payload.get("items") or []
        if not items_data:
            logger.warning("YouTube Data API returned 0 results for '%s'", target_brand)
            return []

        items: list[ScrapedItem] = []

        for entry in items_data:
            video_id = (entry.get("id") or {}).get("videoId", "")
            snippet = entry.get("snippet") or {}

            title = (snippet.get("title") or "").strip()
            description = normalize_whitespace(snippet.get("description") or "")
            channel = snippet.get("channelTitle") or None
            published_raw = snippet.get("publishedAt")  # ISO 8601

            combined = "\n\n".join(p for p in [title, description] if p).strip()
            if not combined:
                continue

            source_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
            ext_id = f"yt-{video_id}" if video_id else None

            published_at = None
            if published_raw:
                try:
                    published_at = datetime.fromisoformat(
                        published_raw.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="video",
                external_id=ext_id,
                author_name=channel,
                source_url=source_url,
                published_at=published_at,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=self.parser_version,
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=ext_id,
                    source_url=source_url,
                    raw_text=combined,
                ),
                raw_payload_json=build_payload_snapshot({
                    "video_id": video_id,
                    "title": title,
                    "description": description,
                    "channel": channel,
                    "published_at": published_raw,
                }),
                raw_text=combined,
                cleaned_text=combined,
                language="en",
                metadata_json={
                    "video_id": video_id,
                    "fetch_mode": "youtube_data_api_v3",
                    "search_query": search_q,
                    "channel": channel,
                },
            ))

        logger.info(
            "YouTube Data API: fetched %d videos for '%s'", len(items), target_brand
        )
        return items

    # ------------------------------------------------------------------
    # Tier 2: yt-dlp search (no API key, may be blocked by YouTube)
    # ------------------------------------------------------------------

    def _scrape_via_ytdlp(self, target_brand: str) -> list[ScrapedItem]:
        """
        yt-dlp search as fallback when no API key is available.
        YouTube may reset connections in some environments — this is expected.
        """
        settings = get_settings()
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        search_query = self._build_search_query(target_brand)
        n = settings.scraper_max_items_per_source

        try:
            import yt_dlp  # type: ignore[import]
        except ImportError:
            logger.warning("yt-dlp not installed — skipping Tier 2")
            return []

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "socket_timeout": 15,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{n}:{search_query}", download=False)
        except Exception as exc:
            logger.warning(
                "yt-dlp search failed for '%s' (YouTube may be blocking): %s",
                target_brand,
                exc,
            )
            return []

        entries = (info or {}).get("entries") or []
        items: list[ScrapedItem] = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            video_id = entry.get("id") or ""
            title = (entry.get("title") or "").strip()
            description = normalize_whitespace(entry.get("description") or "")
            uploader = entry.get("uploader") or entry.get("channel") or None
            source_url = entry.get("webpage_url") or (
                f"https://www.youtube.com/watch?v={video_id}" if video_id else None
            )
            upload_date = entry.get("upload_date")  # YYYYMMDD

            published_at = None
            if upload_date and len(upload_date) == 8:
                try:
                    published_at = datetime.strptime(upload_date, "%Y%m%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    pass

            combined = "\n\n".join(p for p in [title, description] if p).strip()
            if not combined:
                continue

            ext_id = f"yt-{video_id}" if video_id else None

            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="video",
                external_id=ext_id,
                author_name=uploader,
                source_url=source_url,
                published_at=published_at,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version="youtube-ytdlp-v1",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=ext_id,
                    source_url=source_url,
                    raw_text=combined,
                ),
                raw_payload_json=build_payload_snapshot({
                    "video_id": video_id,
                    "title": title,
                    "channel": uploader,
                    "view_count": entry.get("view_count"),
                }),
                raw_text=combined,
                cleaned_text=combined,
                language="en",
                metadata_json={
                    "video_id": video_id,
                    "fetch_mode": "ytdlp_search",
                    "search_query": search_query,
                    "view_count": entry.get("view_count"),
                },
            ))

        logger.info("yt-dlp: found %d videos for '%s'", len(items), target_brand)
        return items

    # ------------------------------------------------------------------
    # Tier 3: Stub items (only when SCRAPER_FAIL_OPEN_TO_STUB=true)
    # ------------------------------------------------------------------

    def _build_stub_items(
        self, target_brand: str, fallback_reason: str | None = None
    ) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        brand_slug = target_brand.lower().replace(" ", "-")

        stubs = [
            ("yt-stub-ex1", "yt_reviewer_1",
             f"{target_brand} Project Walkthrough Review 2024",
             f"Visited {target_brand} listed properties in Bangalore. 3 of 5 units were already "
             f"sold — listings were badly out of date."),
            ("yt-stub-ex2", "yt_reviewer_2",
             f"{target_brand} App Review: Is It Worth Using?",
             f"Using {target_brand} for 3 months — app is slow, search filters don't work, "
             f"agents listed don't respond."),
            ("yt-stub-ex3", "yt_reviewer_3",
             f"My Experience Buying a Home Through {target_brand}",
             f"{target_brand} showed budget options but hidden charges added 15% to the final "
             f"price. Not transparent."),
            ("yt-stub-ex4", "yt_reviewer_4",
             f"{target_brand} vs Competitors: Honest Review",
             f"Photo quality is lower and many listings lack RERA numbers. Customer support "
             f"took 4 days to respond."),
            ("yt-stub-ex5", "yt_reviewer_5",
             f"Fraud Alert: My {target_brand} Experience",
             f"Lost token money after booking through {target_brand}. Builder was unverified. "
             f"Platform takes no responsibility."),
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
                raw_payload_json={"stub": True, "reason": fallback_reason},
                raw_text=combined,
                cleaned_text=combined,
                language="en",
                metadata_json={
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                },
            ))
        return items

    # ------------------------------------------------------------------
    # Main scrape() method
    # ------------------------------------------------------------------

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            logger.info("YouTube: live fetch disabled, returning stub data")
            return self._build_stub_items(target_brand, "Live fetch disabled")

        # Tier 1: YouTube Data API v3 (official, always works when key is set)
        items = self._scrape_via_data_api(target_brand)
        if items:
            return items

        # Tier 2: yt-dlp (may be blocked by YouTube's anti-bot)
        logger.info(
            "YouTube: Data API returned 0 or no key set for '%s' — trying yt-dlp",
            target_brand,
        )
        items = self._scrape_via_ytdlp(target_brand)
        if items:
            return items

        logger.warning(
            "YouTube: all live tiers failed for '%s'. "
            "Fix: add YOUTUBE_DATA_API_KEY to .env "
            "(free at console.cloud.google.com → YouTube Data API v3).",
            target_brand,
        )

        # Tier 3: stubs (only if explicitly enabled)
        if settings.scraper_fail_open_to_stub:
            return self._build_stub_items(target_brand, "All live tiers failed")

        return []
