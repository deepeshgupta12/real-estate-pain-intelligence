"""
Review sites scraper — fetches from BOTH Google Play Store AND Apple iOS App Store
for the most accurate Indian real estate brand signal.

Strategy:
  - Up to 100 most-recent reviews from Google Play (SDK, then HTML fallback)
  - Up to 100 most-recent reviews from Apple App Store (RSS pages 1+2)
  - Each item tagged with store_platform: "google_play" | "ios_app_store"
  - Sentiment filter: skip reviews that are purely positive
    (rating >= 4 AND no negative signal keywords in text)
  - Pain point summary attached to each item's metadata
"""
import logging
import re
from datetime import datetime, timezone

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

# Negative signal keywords — include review if any are present
NEGATIVE_SIGNAL_KEYWORDS = [
    "worst", "terrible", "horrible", "awful", "very bad", "not good",
    "slow", "crash", "crashing", "hang", "freezing", "bug", "glitch",
    "fraud", "scam", "cheat", "fake", "mislead", "spam", "trap",
    "disappoint", "frustrat", "annoying", "useless", "waste", "pathetic",
    "hidden charge", "hidden fee", "overpriced", "not working",
    "doesn't work", "didn't work", "not work", "broken",
    "no response", "not respond", "ignore", "no reply", "never call",
    "stale", "wrong", "incorrect", "inaccurate", "aggressive",
    "haras", "refund", "complain", "complaint", "unverified",
    "not verified", "call too many", "spam call", "money lost",
    "lost money", "no support", "poor support", "bad support",
    "fake listing", "outdated listing", "already sold",
    "not available", "unavailable", "poor ux", "bad ux",
    "difficult to use", "confusing", "not user friendly",
]


def _has_negative_signal(text: str, rating: int | float | None = None) -> bool:
    """Return True if the content should be included (has a negative signal)."""
    if rating is not None:
        if int(rating) <= 3:
            return True
        text_lower = text.lower()
        return any(kw in text_lower for kw in NEGATIVE_SIGNAL_KEYWORDS)
    text_lower = text.lower()
    return any(kw in text_lower for kw in NEGATIVE_SIGNAL_KEYWORDS)


def _make_pain_point_summary(text: str, max_chars: int = 140) -> str:
    """Extract first meaningful sentence or truncate as pain point summary."""
    text = text.strip()
    for sep in [".", "!", "?", "\n"]:
        idx = text.find(sep)
        if 20 <= idx <= max_chars:
            return text[: idx + 1].strip()
    return text[:max_chars].rstrip() + ("…" if len(text) > max_chars else "")


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
    parser_version = "review-sites-dual-store-v2"

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
    # Google Play Store — up to 100 most-recent negative reviews
    # ------------------------------------------------------------------

    def _scrape_google_play(self, target_brand: str) -> list[ScrapedItem]:
        app_id = self._get_play_app_id(target_brand)
        if not app_id:
            logger.debug("No Play Store app ID for '%s'", target_brand)
            return []

        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        source_url = f"https://play.google.com/store/apps/details?id={app_id}"

        try:
            # Tier A: google-play-scraper SDK (best quality, most reviews)
            try:
                from google_play_scraper import reviews as gps_reviews, Sort  # type: ignore
                result, _ = gps_reviews(
                    app_id,
                    lang="en",
                    country="in",
                    sort=Sort.NEWEST,
                    count=100,
                )
                items: list[ScrapedItem] = []
                for r in result:
                    text = normalize_whitespace((r.get("content") or "").strip())
                    if not text:
                        continue
                    rating = r.get("score")
                    if not _has_negative_signal(text, rating):
                        continue

                    review_id = str(r.get("reviewId") or r.get("userName") or f"gplay-{len(items)}")
                    pain_summary = _make_pain_point_summary(text)

                    items.append(ScrapedItem(
                        source_name=self.source_name,
                        platform_name=target_brand,
                        content_type="review",
                        external_id=review_id,
                        author_name=r.get("userName"),
                        source_url=source_url,
                        published_at=r.get("at"),
                        fetched_at=fetched_at,
                        source_query=source_query,
                        parser_version="review-sites-gplay-sdk-v2",
                        dedupe_key=build_dedupe_key(
                            source_name=self.source_name,
                            external_id=review_id,
                            source_url=source_url,
                            raw_text=text,
                        ),
                        raw_payload_json=build_payload_snapshot({
                            "review_id": review_id,
                            "rating": rating,
                            "thumbs_up": r.get("thumbsUpCount"),
                            "app_id": app_id,
                        }),
                        raw_text=text,
                        cleaned_text=text,
                        language="en",
                        metadata_json={
                            "store": "google_play",
                            "store_platform": "google_play",
                            "app_id": app_id,
                            "rating": rating,
                            "fetch_mode": "google_play_scraper",
                            "pain_point_summary": pain_summary,
                        },
                    ))
                if items:
                    logger.info("Google Play (SDK): %d negative reviews for '%s'", len(items), target_brand)
                    return items
            except ImportError:
                pass

            # Tier B: HTML scrape fallback
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 Chrome/122.0.0.0 Mobile Safari/537.36",
                "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            }
            html = RetryingHttpClient.get_text(
                "https://play.google.com/store/apps/details",
                params={"id": app_id, "hl": "en", "gl": "in"},
                headers=headers,
            )
            items = self._parse_play_html(html, target_brand, app_id, fetched_at, source_query, source_url)
            if items:
                logger.info("Google Play (HTML): %d reviews for '%s'", len(items), target_brand)
            return items

        except Exception as exc:
            logger.warning("Google Play scrape failed for '%s': %s", target_brand, exc)
            return []

    def _parse_play_html(
        self, html: str, target_brand: str, app_id: str,
        fetched_at: datetime, source_query: str, source_url: str
    ) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        seen: set[str] = set()
        patterns = [
            r'"([^"]{40,500})"(?:,\d+){3},"\w+",\["[^"]+"\]',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, html):
                text = match.group(1).replace("\\n", " ").replace('\\"', '"').strip()
                text = normalize_whitespace(text)
                if len(text) < 20 or text in seen:
                    continue
                if any(skip in text.lower() for skip in ["privacy policy", "terms of service", "download", "install"]):
                    continue
                if not _has_negative_signal(text):
                    continue
                seen.add(text)
                idx = len(items)
                pain_summary = _make_pain_point_summary(text)
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
                    parser_version="review-sites-gplay-html-v2",
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
                    metadata_json={
                        "store": "google_play",
                        "store_platform": "google_play",
                        "app_id": app_id,
                        "fetch_mode": "html",
                        "pain_point_summary": pain_summary,
                    },
                ))
                if len(items) >= 50:
                    break
            if items:
                break
        return items

    # ------------------------------------------------------------------
    # Apple iOS App Store — up to 100 most-recent negative reviews (2 pages)
    # ------------------------------------------------------------------

    def _scrape_apple_store(self, target_brand: str) -> list[ScrapedItem]:
        app_id = self._get_itunes_app_id(target_brand)
        if not app_id:
            return []

        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        source_url = f"https://apps.apple.com/in/app/{app_id}"
        items: list[ScrapedItem] = []

        for page in range(1, 3):
            try:
                url = f"https://itunes.apple.com/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
                payload = RetryingHttpClient.get_json(url, params={"l": "en", "cc": "in"})
                feed = payload.get("feed") or {}
                entries = feed.get("entry") or []
                if isinstance(entries, dict):
                    entries = [entries]

                for entry in entries:
                    content = (entry.get("content") or {}).get("label") or ""
                    title = (entry.get("title") or {}).get("label") or ""
                    text = normalize_whitespace(" ".join(p for p in [title, content] if p))
                    if not text:
                        continue

                    rating_raw = (entry.get("im:rating") or {}).get("label")
                    try:
                        rating = int(rating_raw) if rating_raw else None
                    except (ValueError, TypeError):
                        rating = None

                    if not _has_negative_signal(text, rating):
                        continue

                    review_id = (entry.get("id") or {}).get("label") or f"apple-{len(items)}"
                    author = ((entry.get("author") or {}).get("name") or {}).get("label")
                    pain_summary = _make_pain_point_summary(text)

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
                        parser_version="review-sites-ios-rss-v2",
                        dedupe_key=build_dedupe_key(
                            source_name=self.source_name,
                            external_id=review_id,
                            source_url=source_url,
                            raw_text=text,
                        ),
                        raw_payload_json=build_payload_snapshot({
                            "rating": rating,
                            "app_id": app_id,
                            "title": title,
                            "content": content,
                        }),
                        raw_text=text,
                        cleaned_text=text,
                        language="en",
                        metadata_json={
                            "store": "apple_app_store",
                            "store_platform": "ios_app_store",
                            "app_id": app_id,
                            "rating": rating,
                            "fetch_mode": "itunes_rss",
                            "pain_point_summary": pain_summary,
                        },
                    ))
            except Exception as exc:
                logger.warning("Apple Store page %d failed for '%s': %s", page, target_brand, exc)
                break

        logger.info("Apple Store: %d negative reviews for '%s'", len(items), target_brand)
        return items

    # ------------------------------------------------------------------
    # Stub data
    # ------------------------------------------------------------------

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        app_id = self._get_play_app_id(target_brand) or "com.example.app"

        stubs = [
            ("gplay-stub-001", 2, "review_user_1", "google_play",
             f"{target_brand} shows lots of properties but half are already sold. Very misleading."),
            ("gplay-stub-002", 1, "review_user_2", "google_play",
             f"Agent from {target_brand} called me 10 times after one enquiry. Too aggressive and annoying."),
            ("gplay-stub-003", 3, "review_user_3", "ios_app_store",
             f"{target_brand} app crashes frequently. Login takes too long. Need to improve stability."),
            ("gplay-stub-004", 2, "review_user_4", "ios_app_store",
             f"Prices shown on {target_brand} do not match what the builder quotes. Hidden charges everywhere."),
            ("gplay-stub-005", 1, "review_user_5", "google_play",
             f"I reported a fake listing to {target_brand} support 2 weeks ago, still not removed. No trust."),
        ]

        items = []
        for ext_id, rating, author, platform, text in stubs:
            source_url = f"https://play.google.com/store/apps/details?id={app_id}" if platform == "google_play" else f"https://apps.apple.com/in/app/{app_id}"
            pain_summary = _make_pain_point_summary(text)
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
                    "store": platform,
                    "store_platform": platform,
                    "app_id": app_id,
                    "rating": str(rating),
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                    "pain_point_summary": pain_summary,
                },
            ))
        return items

    # ------------------------------------------------------------------
    # Main entry point — combines both stores
    # ------------------------------------------------------------------

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            return self._build_stub_items(target_brand, "Live fetch disabled in settings")

        play_items = self._scrape_google_play(target_brand)
        ios_items = self._scrape_apple_store(target_brand)

        combined = play_items + ios_items

        if combined:
            logger.info(
                "ReviewSites dual-store: %d Play + %d iOS = %d total for '%s'",
                len(play_items), len(ios_items), len(combined), target_brand,
            )
            return combined

        if settings.scraper_fail_open_to_stub:
            return self._build_stub_items(target_brand, "Both stores returned no negative reviews")

        return []
