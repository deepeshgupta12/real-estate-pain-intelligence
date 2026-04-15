"""
Web Review Sites scraper — fetches from Trustpilot and MouthShut.

These are DISTINCT from `app_reviews.py` (Google Play + Apple App Store).
This scraper targets web-based review platforms where users post full written
reviews about their real estate portal experience.

Sources:
  - Trustpilot: Extracts reviews from `__NEXT_DATA__` JSON embedded in the page
  - MouthShut: HTML scraping for Indian consumer reviews
  - AmbitionBox: Company/brand review site (India-focused)

Tier strategy per source:
  Tier A: Live fetch (RetryingHttpClient)
  Tier B: Stub data (only when SCRAPER_FAIL_OPEN_TO_STUB=true)

Why NOT app stores here:
  App store reviews are already fetched by `app_reviews.py`. Duplicating them here
  would inflate review counts and skew analysis. This scraper focuses on web-only
  review platforms.
"""

import json
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
    # Indian/Hinglish pain signals
    "dhoka", "fraud hai", "problem hai", "bekaar", "bakwas",
    "paisa barbad", "bekar", "time waste",
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


# Trustpilot domain mappings for Indian real estate brands
BRAND_TRUSTPILOT_DOMAINS: dict[str, str] = {
    "square yards":  "squareyards.com",
    "99acres":       "99acres.com",
    "magicbricks":   "magicbricks.com",
    "housing":       "housing.com",
    "nobroker":      "nobroker.in",
    "commonfloor":   "commonfloor.com",
    "proptiger":     "proptiger.com",
    "makaan":        "makaan.com",
}

# MouthShut search slugs for Indian real estate brands
# MouthShut.com uses URL patterns like /product/<slug>/reviews/
BRAND_MOUTHSHUT_SLUGS: dict[str, str] = {
    "square yards":  "squareyards",
    "99acres":       "99acres",
    "magicbricks":   "magicbricks",
    "housing":       "housingcom",
    "nobroker":      "nobroker",
}


class ReviewSitesScraper(BaseSourceScraper):
    source_name = "review_sites"
    parser_version = "review-sites-web-v3"

    def _build_query(self, target_brand: str, context: str | None = None) -> str:
        base = f"{target_brand} web reviews"
        if context:
            from app.scrapers.context_utils import extract_context_keywords as _ekw
            kws = _ekw(context)[:3]
            if kws:
                base = f'{base} {" ".join(kws)}'
        return base

    def _get_trustpilot_domain(self, target_brand: str) -> str | None:
        brand_lower = target_brand.lower().strip()
        for key, domain in BRAND_TRUSTPILOT_DOMAINS.items():
            if key in brand_lower or brand_lower in key:
                return domain
        return None

    def _get_mouthshut_slug(self, target_brand: str) -> str | None:
        brand_lower = target_brand.lower().strip()
        for key, slug in BRAND_MOUTHSHUT_SLUGS.items():
            if key in brand_lower or brand_lower in key:
                return slug
        return None

    # ------------------------------------------------------------------
    # Trustpilot — extract reviews from __NEXT_DATA__ JSON
    # ------------------------------------------------------------------

    def _scrape_trustpilot(self, target_brand: str, context: str | None = None) -> list[ScrapedItem]:
        """
        Fetches Trustpilot reviews by extracting the embedded __NEXT_DATA__ JSON.
        Trustpilot renders review data server-side in a <script id="__NEXT_DATA__">
        tag — no API key required.  Fetches pages 1–3 (up to ~60 reviews per page).
        """
        domain = self._get_trustpilot_domain(target_brand)
        if not domain:
            logger.debug("No Trustpilot domain mapping for '%s'", target_brand)
            return []

        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand, context)
        settings = get_settings()
        items: list[ScrapedItem] = []
        seen_ids: set[str] = set()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
        }

        max_pages = 3  # Each page has up to 20 reviews; 3 pages = up to 60 reviews
        base_url = f"https://www.trustpilot.com/review/{domain}"

        for page in range(1, max_pages + 1):
            url = base_url if page == 1 else f"{base_url}?page={page}"
            try:
                html = RetryingHttpClient.get_text(url, headers=headers)
            except Exception as exc:
                logger.warning("Trustpilot fetch failed for '%s' page %d: %s", target_brand, page, exc)
                break

            # Extract __NEXT_DATA__ JSON
            match = re.search(
                r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
                html, re.DOTALL
            )
            if not match:
                logger.debug("Trustpilot: no __NEXT_DATA__ found for '%s' page %d", target_brand, page)
                break

            try:
                next_data = json.loads(match.group(1))
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("Trustpilot: JSON parse error for '%s' page %d: %s", target_brand, page, exc)
                break

            # Navigate to reviews array — path varies by Trustpilot version
            reviews_raw: list[dict] = []
            try:
                page_props = next_data.get("props", {}).get("pageProps", {})
                # Try multiple known paths
                for path in [
                    ["reviews"],
                    ["businessUnit", "reviews"],
                    ["initialState", "reviews"],
                    ["reviewsData", "reviews"],
                ]:
                    node = page_props
                    for key in path:
                        node = node.get(key) if isinstance(node, dict) else None
                    if isinstance(node, list) and node:
                        reviews_raw = node
                        break
            except Exception as exc:
                logger.debug("Trustpilot: review path extraction failed: %s", exc)

            if not reviews_raw:
                # Fallback: regex-extract review text directly from HTML
                text_matches = re.findall(
                    r'"text"\s*:\s*"([^"]{30,500})"',
                    html,
                )
                if text_matches:
                    logger.debug("Trustpilot: using regex fallback for '%s' page %d (%d texts)", target_brand, page, len(text_matches))
                    for idx, raw_text in enumerate(text_matches[:30]):
                        text = normalize_whitespace(raw_text.replace("\\n", " ").replace('\\"', '"'))
                        if not text or len(text) < 20:
                            continue
                        if not _has_negative_signal(text):
                            continue
                        ext_id = f"tp-regex-{slugify_identifier(target_brand)}-p{page}-{idx}"
                        if ext_id in seen_ids:
                            continue
                        seen_ids.add(ext_id)
                        pain_summary = _make_pain_point_summary(text)
                        items.append(ScrapedItem(
                            source_name=self.source_name,
                            platform_name=target_brand,
                            content_type="review",
                            external_id=ext_id,
                            author_name=None,
                            source_url=url,
                            published_at=None,
                            fetched_at=fetched_at,
                            source_query=source_query,
                            parser_version=f"{self.parser_version}-tp-regex",
                            dedupe_key=build_dedupe_key(
                                source_name=self.source_name,
                                external_id=ext_id,
                                source_url=url,
                                raw_text=text,
                            ),
                            raw_payload_json=build_payload_snapshot({"text": text, "domain": domain}),
                            raw_text=text,
                            cleaned_text=text,
                            language="en",
                            metadata_json={
                                "platform": "trustpilot",
                                "domain": domain,
                                "fetch_mode": "regex_fallback",
                                "pain_point_summary": pain_summary,
                            },
                        ))
                if page == 1 and not items:
                    logger.info("Trustpilot: no review data found for '%s'", target_brand)
                break

            page_kept = 0
            page_skipped = 0
            for review in reviews_raw:
                # Review shape varies — handle common Trustpilot JSON shapes
                review_id = (
                    str(review.get("id") or review.get("reviewId") or "")
                    or f"tp-{slugify_identifier(target_brand)}-{len(items)}"
                )
                if review_id in seen_ids:
                    continue
                seen_ids.add(review_id)

                title = (review.get("title") or review.get("reviewHeadline") or "").strip()
                body = (review.get("text") or review.get("reviewBody") or review.get("body") or "").strip()
                text = normalize_whitespace(" ".join(p for p in [title, body] if p))
                if not text or len(text) < 15:
                    page_skipped += 1
                    continue

                rating = review.get("rating") or review.get("stars") or review.get("reviewRating")
                if isinstance(rating, dict):
                    rating = rating.get("ratingValue") or rating.get("value")
                try:
                    rating = int(rating) if rating is not None else None
                except (ValueError, TypeError):
                    rating = None

                if not _has_negative_signal(text, rating):
                    page_skipped += 1
                    continue

                author = (
                    review.get("consumer", {}).get("displayName")
                    if isinstance(review.get("consumer"), dict)
                    else review.get("authorName") or review.get("author")
                )

                published_raw = review.get("dates", {}).get("publishedDate") if isinstance(review.get("dates"), dict) else review.get("publishedDate")
                published_at = None
                if published_raw:
                    try:
                        published_at = datetime.fromisoformat(str(published_raw).replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass

                pain_summary = _make_pain_point_summary(text)
                page_kept += 1

                items.append(ScrapedItem(
                    source_name=self.source_name,
                    platform_name=target_brand,
                    content_type="review",
                    external_id=review_id,
                    author_name=str(author) if author else None,
                    source_url=url,
                    published_at=published_at,
                    fetched_at=fetched_at,
                    source_query=source_query,
                    parser_version=f"{self.parser_version}-tp",
                    dedupe_key=build_dedupe_key(
                        source_name=self.source_name,
                        external_id=review_id,
                        source_url=url,
                        raw_text=text,
                    ),
                    raw_payload_json=build_payload_snapshot({
                        "review_id": review_id,
                        "rating": rating,
                        "domain": domain,
                    }),
                    raw_text=text,
                    cleaned_text=text,
                    language="en",
                    metadata_json={
                        "platform": "trustpilot",
                        "domain": domain,
                        "rating": rating,
                        "fetch_mode": "next_data_json",
                        "pain_point_summary": pain_summary,
                    },
                ))

            logger.info(
                "Trustpilot: page %d — kept %d / %d for '%s'",
                page, page_kept, len(reviews_raw), target_brand,
            )
            # Stop if we got nothing useful from this page
            if not reviews_raw:
                break

        logger.info("Trustpilot: %d total negative reviews for '%s'", len(items), target_brand)
        return items

    # ------------------------------------------------------------------
    # MouthShut — Indian consumer review site
    # ------------------------------------------------------------------

    def _scrape_mouthshut(self, target_brand: str, context: str | None = None) -> list[ScrapedItem]:
        """
        Fetches reviews from MouthShut.com — a major Indian consumer review portal.
        Parses HTML to extract review text.  MouthShut is India-specific and surfaces
        Hinglish / regional-language reviews not found on Trustpilot.
        """
        slug = self._get_mouthshut_slug(target_brand)
        if not slug:
            logger.debug("No MouthShut slug mapping for '%s'", target_brand)
            return []

        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand, context)
        items: list[ScrapedItem] = []
        seen_texts: set[str] = set()

        # MouthShut website review listing URL
        url = f"https://www.mouthshut.com/websites/{slug}/reviews"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        }

        try:
            html = RetryingHttpClient.get_text(url, headers=headers)
        except Exception as exc:
            logger.warning("MouthShut fetch failed for '%s': %s", target_brand, exc)
            return []

        # Extract review blocks using known MouthShut HTML patterns
        # MouthShut embeds review text in <div class="review-description"> or similar
        review_patterns = [
            r'class="[^"]*review[^"]*description[^"]*"[^>]*>(.*?)</div>',
            r'class="[^"]*review-text[^"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*class="[^"]*review[^"]*"[^>]*>(.*?)</p>',
            # Fallback: any paragraph-length text block
            r'<p[^>]*>(([^<]{60,500}))</p>',
        ]

        raw_texts: list[str] = []
        for pattern in review_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            for m in matches:
                raw = m[0] if isinstance(m, tuple) else m
                # Strip HTML tags
                clean = re.sub(r'<[^>]+>', ' ', raw)
                clean = normalize_whitespace(clean)
                if len(clean) >= 30:
                    raw_texts.append(clean)
            if raw_texts:
                break

        if not raw_texts:
            logger.info("MouthShut: no review text found for '%s' (anti-bot or no reviews)", target_brand)
            return []

        logger.info("MouthShut: %d raw text blocks for '%s'", len(raw_texts), target_brand)

        for idx, text in enumerate(raw_texts[:50]):  # limit to 50 per scrape
            if text in seen_texts:
                continue
            seen_texts.add(text)

            if not _has_negative_signal(text):
                continue

            ext_id = f"ms-{slugify_identifier(target_brand)}-{idx}"
            pain_summary = _make_pain_point_summary(text)

            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="review",
                external_id=ext_id,
                author_name=None,
                source_url=url,
                published_at=None,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=f"{self.parser_version}-ms",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=ext_id,
                    source_url=url,
                    raw_text=text,
                ),
                raw_payload_json=build_payload_snapshot({"text": text, "slug": slug}),
                raw_text=text,
                cleaned_text=text,
                language="en",
                metadata_json={
                    "platform": "mouthshut",
                    "slug": slug,
                    "fetch_mode": "html_scrape",
                    "pain_point_summary": pain_summary,
                },
            ))

        logger.info("MouthShut: %d negative reviews kept for '%s'", len(items), target_brand)
        return items

    # ------------------------------------------------------------------
    # Stub data — used when SCRAPER_FAIL_OPEN_TO_STUB=true
    # ------------------------------------------------------------------

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        domain = self._get_trustpilot_domain(target_brand) or "example.com"

        stubs = [
            ("tp-stub-001", 2, "trustpilot", "trustpilot",
             f"Very disappointed with {target_brand}. Listed property prices were ₹10L lower than actual quotes from the builder. Hidden charges not disclosed upfront."),
            ("tp-stub-002", 1, "trustpilot", "trustpilot",
             f"{target_brand} has terrible customer support. Waited 3 weeks for a response about a duplicate listing. No accountability whatsoever."),
            ("ms-stub-001", 2, "mouthshut", "mouthshut",
             f"Fake listings problem on {target_brand} is very bad. Called 4 agents — 3 properties already sold. Complete waste of time and money."),
            ("ms-stub-002", 1, "mouthshut", "mouthshut",
             f"{target_brand} agents are very aggressive. Gave my number and got 20+ calls in one day. No option to opt out. Very frustrating experience."),
            ("ms-stub-003", 2, "mouthshut", "mouthshut",
             f"App crashes frequently on {target_brand}. Search filters don't work properly. Photos are outdated. Would not recommend."),
        ]

        items = []
        for ext_id, rating, platform, src_platform, text in stubs:
            source_url = f"https://www.trustpilot.com/review/{domain}" if platform == "trustpilot" else f"https://www.mouthshut.com/websites/{slugify_identifier(target_brand)}/reviews"
            pain_summary = _make_pain_point_summary(text)
            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="review",
                external_id=f"{slugify_identifier(target_brand)}-{ext_id}",
                author_name=None,
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
                    "platform": src_platform,
                    "fetch_mode": "stub",
                    "rating": str(rating),
                    "fallback_reason": fallback_reason,
                    "pain_point_summary": pain_summary,
                },
            ))
        return items

    # ------------------------------------------------------------------
    # Main entry point — combines Trustpilot + MouthShut
    # ------------------------------------------------------------------

    def scrape(self, target_brand: str, context: str | None = None) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            return self._build_stub_items(target_brand, "Live fetch disabled in settings")

        trustpilot_items = self._scrape_trustpilot(target_brand, context)
        mouthshut_items = self._scrape_mouthshut(target_brand, context)

        combined = trustpilot_items + mouthshut_items

        if combined:
            logger.info(
                "ReviewSites web: %d Trustpilot + %d MouthShut = %d total for '%s'",
                len(trustpilot_items), len(mouthshut_items), len(combined), target_brand,
            )
            return combined

        if settings.scraper_fail_open_to_stub:
            return self._build_stub_items(target_brand, "All web review sources returned no negative reviews")

        return []
