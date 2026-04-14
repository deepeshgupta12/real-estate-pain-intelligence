"""
Review sites scraper — 3-tier fallback:
  1. Google Play Store reviews (unofficial JSON API, reliable for Indian market)
  2. Apple App Store RSS feed
  3. Stub data

Trustpilot/AmbitionBox require JS rendering and block all bots — not viable.
Google Play Store reviews are the best public signal for Indian real estate apps.
"""
import logging
import re
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.scrapers.base import BaseSourceScraper
from app.scrapers.http_client import RetryingHttpClient
from app.scrapers.types import ScrapedItem
from app.scrapers.utils import (
    build_dedupe_key,
    build_payload_snapshot,
    normalize_whitespace,
    slugify_identifier,
)

logger = logging.getLogger(__name__)

# Known Google Play app IDs for Indian real estate brands
BRAND_PLAY_APP_IDS: dict[str, str] = {
    "square yards":  "com.squareyards.app",
    "99acres":       "com.ninetynineacres.app",
    "magicbricks":   "com.magicbricks.app",
    "housing":       "com.housing.app",
    "nobroker":      "com.nobroker.app",
    "commonfloor":   "com.commonfloor",
    "proptiger":     "com.proptiger.app",
    "makaan":        "com.makaan",
}

# Known Apple App Store IDs for Indian real estate brands
BRAND_ITUNES_IDS: dict[str, str] = {
    "square yards":  "1082944916",
    "99acres":       "438985091",
    "magicbricks":   "567898523",
    "housing":       "878516912",
    "nobroker":      "1085715402",
}


class ReviewSitesScraper(BaseSourceScraper):
    source_name = "review_sites"
    parser_version = "review-sites-play-v1"

    def _build_query(self, target_brand: str) -> str:
        return f"{target_brand} reviews"

    def _get_play_app_id(self, target_brand: str) -> str | None:
        brand_lower = target_brand.lower().strip()
        for key, app_id in BRAND_PLAY_APP_IDS.items():
            if key in brand_lower or brand_lower in key:
                return app_id
        return None

    def _get_itunes_app_id(self, target_brand: str) -> str | None:
        brand_lower = target_brand.lower().strip()
        for key, app_id in BRAND_ITUNES_IDS.items():
            if key in brand_lower or brand_lower in key:
                return app_id
        return None

    # ------------------------------------------------------------------
    # Tier 1: Google Play Store reviews (unofficial JSON endpoint)
    # ------------------------------------------------------------------

    def _scrape_google_play(self, target_brand: str) -> list[ScrapedItem]:
        """
        Uses the unofficial Google Play internal API that the mobile app calls.
        Returns review JSON without authentication.
        """
        app_id = self._get_play_app_id(target_brand)
        if not app_id:
            logger.debug("No Play Store app ID for '%s'", target_brand)
            return []

        settings = get_settings()
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)

        try:
            # google-play-scraper package (optional, best quality)
            try:
                from google_play_scraper import reviews as gps_reviews, Sort  # type: ignore
                result, _ = gps_reviews(
                    app_id,
                    lang="en",
                    country="in",
                    sort=Sort.NEWEST,
                    count=settings.scraper_max_items_per_source,
                )
                items = []
                for r in result:
                    text = normalize_whitespace((r.get("content") or "").strip())
                    if not text:
                        continue
                    review_id = str(r.get("reviewId") or r.get("userName") or "")
                    source_url = f"https://play.google.com/store/apps/details?id={app_id}"
                    items.append(ScrapedItem(
                        source_name=self.source_name,
                        platform_name=target_brand,
                        content_type="review",
                        external_id=review_id or f"gplay-{len(items)}",
                        author_name=r.get("userName"),
                        source_url=source_url,
                        published_at=r.get("at"),
                        fetched_at=fetched_at,
                        source_query=source_query,
                        parser_version="review-sites-gplay-sdk-v1",
                        dedupe_key=build_dedupe_key(
                            source_name=self.source_name,
                            external_id=review_id,
                            source_url=source_url,
                            raw_text=text,
                        ),
                        raw_payload_json=build_payload_snapshot({
                            "review_id": review_id,
                            "rating": r.get("score"),
                            "thumbs_up": r.get("thumbsUpCount"),
                            "app_id": app_id,
                        }),
                        raw_text=text,
                        cleaned_text=text,
                        language="en",
                        metadata_json={
                            "store": "google_play",
                            "app_id": app_id,
                            "rating": r.get("score"),
                            "fetch_mode": "google_play_scraper",
                        },
                    ))
                if items:
                    logger.info("Google Play (SDK): %d reviews for '%s'", len(items), target_brand)
                    return items
            except ImportError:
                pass  # fall through to HTTP method

            # Fallback: direct RSS-style request to Play Store
            url = f"https://play.google.com/store/apps/details"
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
                "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            }
            html = RetryingHttpClient.get_text(url, params={"id": app_id, "hl": "en", "gl": "in"}, headers=headers)
            items = self._parse_play_html(html, target_brand, app_id, fetched_at, source_query)
            if items:
                logger.info("Google Play (HTML): %d reviews for '%s'", len(items), target_brand)
            return items

        except Exception as exc:
            logger.warning("Google Play scrape failed for '%s': %s", target_brand, exc)
            return []

    def _parse_play_html(
        self, html: str, target_brand: str, app_id: str,
        fetched_at: datetime, source_query: str
    ) -> list[ScrapedItem]:
        """Extract review text from Google Play HTML using JSON embedded in page."""
        source_url = f"https://play.google.com/store/apps/details?id={app_id}"
        items = []

        # Google Play embeds review data as JSON in script tags
        patterns = [
            r'"([^"]{40,500})"(?:,\d+){3},"\w+",\["[^"]+"\]',  # review text pattern
        ]
        seen: set[str] = set()

        for pattern in patterns:
            for match in re.finditer(pattern, html):
                text = match.group(1).replace("\\n", " ").replace('\\"', '"').strip()
                text = normalize_whitespace(text)
                if len(text) < 20 or text in seen:
                    continue
                # Filter out non-review strings (UI labels etc)
                if any(skip in text.lower() for skip in ["privacy policy", "terms of service", "download", "install"]):
                    continue
                seen.add(text)
                idx = len(items)
                items.append(ScrapedItem(
                    source_name=self.source_name,
                    platform_name=target_brand,
                    content_type="review",
                    external_id=f"gplay-html-{idx}",
                    author_name=None,
                    source_url=source_url,
                    published_at=None,
                    fetched_at=fetched_at,
                    source_query=source_query,
                    parser_version="review-sites-gplay-html-v1",
                    dedupe_key=build_dedupe_key(
                        source_name=self.source_name,
                        external_id=f"gplay-html-{idx}",
                        source_url=source_url,
                        raw_text=text,
                    ),
                    raw_payload_json=build_payload_snapshot({"app_id": app_id, "text": text}),
                    raw_text=text,
                    cleaned_text=text,
                    language="en",
                    metadata_json={"store": "google_play", "app_id": app_id, "fetch_mode": "html"},
                ))
                if len(items) >= 10:
                    break
            if items:
                break

        return items

    # ------------------------------------------------------------------
    # Tier 2: Apple App Store RSS (iOS reviews)
    # ------------------------------------------------------------------

    def _scrape_apple_store(self, target_brand: str) -> list[ScrapedItem]:
        settings = get_settings()
        app_id = self._get_itunes_app_id(target_brand)
        if not app_id:
            return []

        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)

        try:
            url = f"https://itunes.apple.com/rss/customerreviews/page=1/id={app_id}/sortby=mostrecent/json"
            payload = RetryingHttpClient.get_json(url, params={"l": "en", "cc": "in"})
            feed = payload.get("feed") or {}
            entries = feed.get("entry") or []
            if isinstance(entries, dict):
                entries = [entries]

            items = []
            for entry in entries[:settings.scraper_max_items_per_source]:
                content = (entry.get("content") or {}).get("label") or ""
                title = (entry.get("title") or {}).get("label") or ""
                text = normalize_whitespace(" ".join(p for p in [title, content] if p))
                if not text:
                    continue
                review_id = (entry.get("id") or {}).get("label") or f"apple-{len(items)}"
                source_url = f"https://apps.apple.com/in/app/{app_id}"
                rating = (entry.get("im:rating") or {}).get("label")
                author = ((entry.get("author") or {}).get("name") or {}).get("label")
                items.append(ScrapedItem(
                    source_name=self.source_name,
                    platform_name=target_brand,
                    content_type="review",
                    external_id=review_id,
                    author_name=author,
                    source_url=source_url,
                    published_at=None,
                    fetched_at=fetched_at,
                    source_query=source_query,
                    parser_version="review-sites-apple-v1",
                    dedupe_key=build_dedupe_key(
                        source_name=self.source_name,
                        external_id=review_id,
                        source_url=source_url,
                        raw_text=text,
                    ),
                    raw_payload_json=build_payload_snapshot({"rating": rating, "app_id": app_id}),
                    raw_text=text,
                    cleaned_text=text,
                    language="en",
                    metadata_json={"store": "apple_app_store", "app_id": app_id, "rating": rating, "fetch_mode": "rss"},
                ))
            logger.info("Apple Store: %d reviews for '%s'", len(items), target_brand)
            return items
        except Exception as exc:
            logger.warning("Apple Store scrape failed for '%s': %s", target_brand, exc)
            return []

    # ------------------------------------------------------------------
    # Tier 3: Stub data — realistic, varied
    # ------------------------------------------------------------------

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        app_id = self._get_play_app_id(target_brand) or "com.example.app"
        source_url = f"https://play.google.com/store/apps/details?id={app_id}"

        stubs = [
            ("gplay-stub-001", 2, "review_user_1",
             f"{target_brand} shows lots of properties but half are already sold. Very misleading."),
            ("gplay-stub-002", 1, "review_user_2",
             f"Agent from {target_brand} called me 10 times after one enquiry. Too aggressive and annoying."),
            ("gplay-stub-003", 3, "review_user_3",
             f"{target_brand} app crashes frequently. Login takes too long. Need to improve stability."),
            ("gplay-stub-004", 2, "review_user_4",
             f"Prices shown on {target_brand} do not match what the builder quotes. Hidden charges everywhere."),
            ("gplay-stub-005", 1, "review_user_5",
             f"I reported a fake listing to {target_brand} support 2 weeks ago, still not removed. No trust."),
        ]

        items = []
        for ext_id, rating, author, text in stubs:
            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="review",
                external_id=f"{slugify_identifier(target_brand)}-{ext_id}",
                author_name=author,
                source_url=source_url,
                published_at=None,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=f"{self.parser_version}-stub",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=f"{slugify_identifier(target_brand)}-{ext_id}",
                    source_url=source_url,
                    raw_text=text,
                ),
                raw_payload_json={"stub": True, "reason": fallback_reason, "rating": rating},
                raw_text=text,
                cleaned_text=text,
                language="en",
                metadata_json={
                    "store": "google_play",
                    "app_id": app_id,
                    "rating": str(rating),
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                },
            ))
        return items

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            return self._build_stub_items(target_brand, "Live fetch disabled in settings")

        # Tier 1: Google Play
        items = self._scrape_google_play(target_brand)
        if items:
            return items

        # Tier 2: Apple App Store
        items = self._scrape_apple_store(target_brand)
        if items:
            return items

        # Tier 3: Stub fallback
        if settings.scraper_fail_open_to_stub:
            return self._build_stub_items(target_brand, "All live tiers failed")

        return []
