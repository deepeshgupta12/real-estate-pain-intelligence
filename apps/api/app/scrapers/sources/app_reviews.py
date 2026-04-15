"""
App Reviews scraper — fetches from BOTH Google Play Store AND Apple iOS App Store.

Strategy:
  - Up to 100 most-recent reviews from Google Play (via google-play-scraper SDK)
  - Up to 100 most-recent reviews from Apple App Store (RSS, pages 1+2)
  - Each item tagged with store_platform: "google_play" | "ios_app_store"
  - Sentiment filter: skip reviews that are purely positive
    (rating >= 4 AND no negative signal keywords in text)
  - Pain point summary generated from review text for each item
"""
import logging
from datetime import datetime, timezone

from app.core.config import get_settings
from app.scrapers.base import BaseSourceScraper
from app.scrapers.http_client import RetryingHttpClient
from app.scrapers.types import ScrapedItem
from app.scrapers.utils import build_dedupe_key, build_payload_snapshot, normalize_whitespace

logger = logging.getLogger(__name__)

# Keywords that signal a complaint even in an otherwise positive review
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
    "lost money", "trust issue", "no support", "poor support",
    "bad support", "fake listing", "outdated listing", "already sold",
    "not available", "unavailable", "poor ux", "bad ux",
    "difficult to use", "confusing", "not user friendly",
]


def _has_negative_signal(text: str, rating: int | float | None = None) -> bool:
    """Return True if the content should be included (has a negative signal)."""
    if rating is not None:
        # Low-rated reviews always included
        if int(rating) <= 3:
            return True
        # High-rated (4-5) only if they contain negative keywords
        text_lower = text.lower()
        return any(kw in text_lower for kw in NEGATIVE_SIGNAL_KEYWORDS)
    # No rating available — include if any negative keyword found
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


def _matches_context(text: str, context_keywords: list[str]) -> bool:
    """
    Post-filter: return True if text matches ANY context keyword, OR if no context given.
    Store scrapers (Google Play SDK, iTunes RSS) don't support query-based filtering,
    so we post-filter the result set when a research context is active.
    """
    if not context_keywords:
        return True
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in context_keywords)


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


class AppReviewsScraper(BaseSourceScraper):
    source_name = "app_reviews"
    parser_version = "app-reviews-v3-dual-store"

    def _build_query(self, target_brand: str, context: str | None = None) -> str:
        base = f"{target_brand} app"
        if context:
            from app.scrapers.context_utils import extract_context_keywords as _ekw
            kws = _ekw(context)[:3]
            if kws:
                base = f'{base} {" ".join(kws)}'
        return base

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
    # Google Play Store — up to 100 most-recent reviews
    # ------------------------------------------------------------------

    def _scrape_google_play(self, target_brand: str, context: str | None = None) -> list[ScrapedItem]:
        app_id = self._get_play_app_id(target_brand)
        if not app_id:
            return []

        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand, context)
        source_url = f"https://play.google.com/store/apps/details?id={app_id}"

        try:
            from google_play_scraper import reviews as gps_reviews, Sort  # type: ignore
            # NOTE: Do NOT set lang="en" — Indian users review in Hindi/Hinglish.
            # Filtering to English returns 0 results for Indian real-estate apps.
            # We fetch all languages and let the sentiment filter handle relevance.
            result, _ = gps_reviews(
                app_id,
                country="in",
                sort=Sort.NEWEST,
                count=100,
            )
            logger.info("Google Play SDK: fetched %d raw reviews for '%s' app_id=%s", len(result), target_brand, app_id)
            items: list[ScrapedItem] = []
            skipped_positive = 0
            skipped_empty = 0
            for r in result:
                text = normalize_whitespace((r.get("content") or "").strip())
                if not text:
                    skipped_empty += 1
                    continue
                rating = r.get("score")
                if not _has_negative_signal(text, rating):
                    skipped_positive += 1
                    continue  # skip purely positive reviews

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
                    parser_version="app-reviews-gplay-sdk-v2",
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
            logger.info(
                "Google Play SDK: %d kept / %d raw (skipped_positive=%d, skipped_empty=%d) for '%s'",
                len(items), len(result), skipped_positive, skipped_empty, target_brand,
            )
            return items
        except ImportError:
            logger.warning("google_play_scraper not installed — skipping Google Play SDK tier for '%s'", target_brand)
            return []
        except Exception as exc:
            logger.warning("Google Play scrape failed for '%s' (app_id=%s): %s", target_brand, app_id, exc)
            return []

    # ------------------------------------------------------------------
    # Apple iOS App Store — up to 100 most-recent reviews (2 pages × 50)
    # ------------------------------------------------------------------

    def _scrape_ios_store(self, target_brand: str, context: str | None = None) -> list[ScrapedItem]:
        app_id = self._get_itunes_app_id(target_brand)
        if not app_id:
            return []

        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand, context)
        source_url = f"https://apps.apple.com/in/app/{app_id}"
        items: list[ScrapedItem] = []

        # Fetch up to 5 pages (50 reviews/page = up to 250 reviews).
        # NOTE: Do NOT pass l=en or cc=in — these locale params cause Apple's RSS to
        # return 0 entries for Indian apps where most reviews are in Hindi/Hinglish.
        # Fetching without locale params returns all recent reviews regardless of language.
        for page in range(1, 6):
            try:
                url = f"https://itunes.apple.com/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
                logger.debug("Apple App Store: fetching page %d — %s", page, url)
                payload = RetryingHttpClient.get_json(url)
                feed = payload.get("feed") or {}
                entries = feed.get("entry") or []
                if isinstance(entries, dict):
                    entries = [entries]

                page_raw = len(entries)
                page_kept = 0
                logger.info("Apple App Store: page %d — %d raw entries for '%s' app_id=%s", page, page_raw, target_brand, app_id)

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
                        continue  # skip purely positive reviews

                    page_kept += 1
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
                        parser_version="app-reviews-ios-rss-v2",
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
                logger.info(
                    "Apple App Store: page %d — kept %d / %d (skipped_positive=%d) for '%s'",
                    page, page_kept, page_raw, page_raw - page_kept, target_brand,
                )
            except Exception as exc:
                logger.warning("Apple App Store page %d failed for '%s': %s", page, target_brand, exc)
                break  # stop if a page fails

        logger.info("Apple App Store: %d negative-signal reviews total for '%s'", len(items), target_brand)
        return items

    # ------------------------------------------------------------------
    # Stub data fallback
    # ------------------------------------------------------------------

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        brand_slug = target_brand.lower().replace(" ", "-")

        stubs = [
            ("app-stub-001", 2, "app_user_1", "google_play",
             f"The {target_brand} app feels very slow and the property leads shown don't match my budget intent at all."),
            ("app-stub-002", 1, "app_user_2", "google_play",
             f"{target_brand} app crashes on Android when switching between listings. Very annoying, lost interest 3 times."),
            ("app-stub-003", 3, "app_user_3", "ios_app_store",
             f"Good property selection on {target_brand} but the in-app chat with agents never works. Always shows error."),
            ("app-stub-004", 2, "app_user_4", "ios_app_store",
             f"Notifications from {target_brand} are spammy. I get 10+ alerts daily for properties I have no interest in."),
            ("app-stub-005", 1, "app_user_5", "google_play",
             f"The {target_brand} search filter resets every time I leave the app. Frustrating UX."),
        ]

        items = []
        for ext_suffix, rating, author, platform, text in stubs:
            ext_id = f"{brand_slug}-{ext_suffix}"
            pain_summary = _make_pain_point_summary(text)
            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="review",
                external_id=ext_id,
                author_name=author,
                source_url=None,
                published_at=None,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=f"{self.parser_version}-stub",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=ext_id,
                    source_url=None,
                    raw_text=text,
                ),
                raw_payload_json={"stub": True, "reason": fallback_reason, "rating": rating},
                raw_text=text,
                cleaned_text=text,
                language="en",
                metadata_json={
                    "store": platform,
                    "store_platform": platform,
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

    def scrape(self, target_brand: str, context: str | None = None) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            return self._build_stub_items(
                target_brand=target_brand,
                fallback_reason="Live fetch disabled in settings",
            )

        play_items = self._scrape_google_play(target_brand, context)
        ios_items = self._scrape_ios_store(target_brand, context)

        combined = play_items + ios_items

        # Post-filter by context keywords when a research context is active.
        # Store SDKs don't support query-based filtering, so we apply context
        # keywords as a post-fetch filter.  When no context is set, all
        # negative-signal reviews are included.
        if context and combined:
            from app.scrapers.context_utils import extract_context_keywords as _ekw
            ctx_kws = _ekw(context)
            if ctx_kws:
                filtered = [
                    item for item in combined
                    if _matches_context(item.raw_text or "", ctx_kws)
                ]
                # Fall back to unfiltered set if context filter removes everything
                # (keeps the run useful even with a narrow context)
                if filtered:
                    combined = filtered

        if combined:
            return combined

        if settings.scraper_fail_open_to_stub:
            return self._build_stub_items(
                target_brand=target_brand,
                fallback_reason="Both Google Play and iOS App Store returned no results",
            )

        return []
