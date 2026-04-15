"""
YouTube scraper — 3-tier strategy + sentiment filtering:

Enhancements:
  - Source platform tagged as "youtube" + channel in metadata
  - Sentiment filter: skip videos that are purely positive (no negative signal)
  - pain_point_summary extracted from title + description


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

NEGATIVE_SIGNAL_KEYWORDS = [
    "worst", "terrible", "horrible", "awful", "very bad", "not good",
    "slow", "crash", "bug", "glitch", "fraud", "scam", "cheat", "fake",
    "mislead", "spam", "disappoint", "frustrat", "annoying", "useless",
    "waste", "hidden charge", "hidden fee", "overpriced", "not working",
    "doesn't work", "didn't work", "broken", "no response", "not respond",
    "ignore", "no reply", "stale", "wrong", "incorrect", "inaccurate",
    "aggressive", "haras", "refund", "complain", "complaint", "unverified",
    "money lost", "lost money", "no support", "poor support", "bad support",
    "fake listing", "already sold", "not available", "beware", "warning",
    "alert", "scammed", "cheated", "ripped off", "problem", "issue", "error",
    # Review/experience signal words — include user-generated opinion content
    "review", "honest", "reality", "truth", "exposed", "dark side",
    "experience", "my experience", "worth it", "should you", "should i",
    "before you", "watch before", "must watch", "vs ", "comparison",
    "better than", "worse than", "rating", "feedback", "opinion",
    "real review", "unboxing", "walkthrough", "guide", "tips",
    # Hindi/Hinglish pain keywords (transliterated)
    "dhoka", "fraud hai", "problem hai", "bekaar", "bakwas",
    "paisa barbad", "ganda", "time waste", "bekar",
]


def _has_negative_signal(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in NEGATIVE_SIGNAL_KEYWORDS)


def _make_pain_point_summary(text: str, max_chars: int = 140) -> str:
    text = text.strip()
    for sep in [".", "!", "?", "\n"]:
        idx = text.find(sep)
        if 20 <= idx <= max_chars:
            return text[: idx + 1].strip()
    return text[:max_chars].rstrip() + ("…" if len(text) > max_chars else "")


class YouTubeScraper(BaseSourceScraper):
    source_name = "youtube"
    parser_version = "youtube-v3api-v1"

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def _build_query(self, target_brand: str, context: str | None = None) -> str:
        base = f"{target_brand} review experience India"
        if context:
            from app.scrapers.context_utils import extract_context_keywords as _ekw
            kws = _ekw(context)[:3]
            if kws:
                base = f'{base} {" ".join(kws)}'
        return base

    def _build_search_query(self, target_brand: str, context: str | None = None) -> str:
        # Primary query — complaint/review-focused to avoid promotional content
        base = f"{target_brand} review complaint experience India"
        if context:
            from app.scrapers.context_utils import extract_context_keywords as _ekw
            kws = _ekw(context)[:2]
            if kws:
                base = f"{base} {' '.join(kws)}"
        return base

    def _build_search_queries(self, target_brand: str, context: str | None = None) -> list[str]:
        """Return a diverse set of search queries to maximise recall of negative signals."""
        primary = self._build_search_query(target_brand, context)
        return [
            primary,
            f"{target_brand} problem issue feedback India",
            f"{target_brand} scam fraud beware India real estate",
            f"{target_brand} app not working hidden charges India",
            f"{target_brand} honest review India property",
        ]

    # ------------------------------------------------------------------
    # Tier 1: YouTube Data API v3 (official — no blocking)
    # ------------------------------------------------------------------

    def _scrape_via_data_api(self, target_brand: str, context: str | None = None) -> list[ScrapedItem]:
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
        source_query = self._build_query(target_brand, context)
        search_queries = self._build_search_queries(target_brand, context)

        # YouTube Data API v3 caps maxResults at 50.
        # With multiple queries we spread the budget: each query fetches up to
        # max(10, total_budget // num_queries) results.  This is more diverse
        # and less likely to be dominated by a single brand's own uploads.
        total_budget = min(settings.scraper_max_items_per_source, 50)
        per_query_limit = max(10, total_budget // len(search_queries))

        # Collect raw items_data from all queries, deduplicating by videoId
        all_items_data: list[dict] = []
        seen_video_ids: set[str] = set()

        for search_q in search_queries:
            logger.info(
                "YouTube Data API: querying '%s' (maxResults=%d, query=%r)",
                target_brand, per_query_limit, search_q,
            )
            try:
                payload = RetryingHttpClient.get_json(
                    f"{settings.youtube_data_api_base_url}/search",
                    params={
                        "part": "snippet",
                        "q": search_q,
                        "type": "video",
                        "maxResults": per_query_limit,
                        "relevanceLanguage": "en",
                        "regionCode": "IN",
                        "key": settings.youtube_data_api_key,
                    },
                    use_browser_headers=False,
                )
            except Exception as exc:
                logger.warning("YouTube Data API search failed for '%s' (query=%r): %s", target_brand, search_q, exc)
                continue

            for entry in (payload.get("items") or []):
                vid = (entry.get("id") or {}).get("videoId", "")
                if vid and vid in seen_video_ids:
                    continue
                if vid:
                    seen_video_ids.add(vid)
                all_items_data.append(entry)

        logger.info("YouTube Data API: %d unique raw results for '%s' across %d queries",
                    len(all_items_data), target_brand, len(search_queries))
        if not all_items_data:
            logger.warning("YouTube Data API returned 0 results for '%s'", target_brand)
            return []

        items: list[ScrapedItem] = []
        skipped_empty = 0
        skipped_positive = 0

        for entry in all_items_data:
            video_id = (entry.get("id") or {}).get("videoId", "")
            snippet = entry.get("snippet") or {}

            title = (snippet.get("title") or "").strip()
            description = normalize_whitespace(snippet.get("description") or "")
            channel = snippet.get("channelTitle") or None
            published_raw = snippet.get("publishedAt")  # ISO 8601

            combined = "\n\n".join(p for p in [title, description] if p).strip()
            if not combined:
                skipped_empty += 1
                continue

            # Sentiment filter — skip purely positive videos
            if not _has_negative_signal(combined):
                skipped_positive += 1
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

            pain_summary = _make_pain_point_summary(combined)

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
                    "platform": "youtube",
                    "video_id": video_id,
                    "fetch_mode": "youtube_data_api_v3",
                    "search_query": search_q,
                    "channel": channel,
                    "pain_point_summary": pain_summary,
                },
            ))

        logger.info(
            "YouTube Data API: %d kept / %d raw (skipped_positive=%d, skipped_empty=%d) for '%s'",
            len(items), len(items_data), skipped_positive, skipped_empty, target_brand,
        )
        return items

    # ------------------------------------------------------------------
    # Tier 2: yt-dlp search (no API key, may be blocked by YouTube)
    # ------------------------------------------------------------------

    def _scrape_via_ytdlp(self, target_brand: str, context: str | None = None) -> list[ScrapedItem]:
        """
        yt-dlp search as fallback when no API key is available.
        YouTube may reset connections in some environments — this is expected.
        """
        settings = get_settings()
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand, context)
        search_query = self._build_search_query(target_brand, context)
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
        logger.info("yt-dlp: %d raw entries for '%s'", len(entries), target_brand)
        items: list[ScrapedItem] = []
        ytdlp_skipped = 0

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
                ytdlp_skipped += 1
                continue

            # Sentiment filter
            if not _has_negative_signal(combined):
                ytdlp_skipped += 1
                continue

            ext_id = f"yt-{video_id}" if video_id else None
            ytdlp_pain_summary = _make_pain_point_summary(combined)

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
                    "platform": "youtube",
                    "video_id": video_id,
                    "fetch_mode": "ytdlp_search",
                    "search_query": search_query,
                    "view_count": entry.get("view_count"),
                    "pain_point_summary": ytdlp_pain_summary,
                },
            ))

        logger.info(
            "yt-dlp: %d kept / %d raw (skipped=%d) for '%s'",
            len(items), len(entries), ytdlp_skipped, target_brand,
        )
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
            stub_pain_summary = _make_pain_point_summary(combined)
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
                    "platform": "youtube",
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                    "pain_point_summary": stub_pain_summary,
                },
            ))
        return items

    # ------------------------------------------------------------------
    # Main scrape() method
    # ------------------------------------------------------------------

    def scrape(self, target_brand: str, context: str | None = None) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            logger.info("YouTube: live fetch disabled, returning stub data")
            return self._build_stub_items(target_brand, "Live fetch disabled")

        # Tier 1: YouTube Data API v3 (official, always works when key is set)
        items = self._scrape_via_data_api(target_brand, context)
        if items:
            return items

        # Tier 2: yt-dlp (may be blocked by YouTube's anti-bot)
        logger.info(
            "YouTube: Data API returned 0 or no key set for '%s' — trying yt-dlp",
            target_brand,
        )
        items = self._scrape_via_ytdlp(target_brand, context)
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
