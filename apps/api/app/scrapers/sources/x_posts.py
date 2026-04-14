from datetime import datetime, timezone

from app.core.config import get_settings
from app.scrapers.base import BaseSourceScraper
from app.scrapers.http_client import RetryingHttpClient
from app.scrapers.types import ScrapedItem
from app.scrapers.utils import build_dedupe_key, build_payload_snapshot, normalize_whitespace

NEGATIVE_SIGNAL_KEYWORDS = [
    "worst", "terrible", "horrible", "awful", "very bad", "not good",
    "slow", "crash", "bug", "glitch", "fraud", "scam", "cheat", "fake",
    "mislead", "spam", "disappoint", "frustrat", "annoying", "useless",
    "waste", "hidden charge", "overpriced", "not working",
    "doesn't work", "didn't work", "broken", "no response", "not respond",
    "ignore", "stale", "wrong", "incorrect", "inaccurate", "aggressive",
    "haras", "refund", "complain", "complaint", "unverified",
    "money lost", "lost money", "no support", "poor support", "bad support",
    "fake listing", "already sold", "not available", "beware", "warning",
    "alert", "scammed", "cheated", "ripped off", "problem", "issue", "error",
    "blocking", "spam call", "duplicate listing", "token",
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


class XPostsScraper(BaseSourceScraper):
    source_name = "x"
    parser_version = "x-alt-v2-live-1"

    def _build_query(self, target_brand: str) -> str:
        return f'"{target_brand}" real estate complaint'

    def _build_headers(self) -> dict[str, str]:
        settings = get_settings()
        return {
            "User-Agent": settings.scraper_user_agent,
            "Accept": "application/json",
        }

    def _fetch_live_payload(self, target_brand: str) -> dict:
        settings = get_settings()
        return RetryingHttpClient.get_json(
            settings.scraper_public_social_search_base_url,
            params={
                "query": self._build_query(target_brand),
                "tags": "story",
                "hitsPerPage": settings.scraper_max_items_per_source,
            },
            headers=self._build_headers(),
        )

    def _parse_live_items(self, payload: dict, target_brand: str) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        hits = payload.get("hits") or []

        parsed_items: list[ScrapedItem] = []

        for hit in hits:
            external_id = hit.get("objectID")
            title = hit.get("title") or ""
            story_text = hit.get("story_text") or ""
            raw_text = normalize_whitespace(" ".join(part for part in [title, story_text] if part))
            if not raw_text:
                continue

            # Sentiment filter — skip purely positive posts
            if not _has_negative_signal(raw_text):
                continue

            source_url = hit.get("url") or hit.get("story_url")
            author_name = hit.get("author")

            published_at = None
            created_at = hit.get("created_at")
            if created_at:
                published_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

            pain_summary = _make_pain_point_summary(raw_text)

            parsed_items.append(
                ScrapedItem(
                    source_name=self.source_name,
                    platform_name=target_brand,
                    content_type="post",
                    external_id=external_id,
                    author_name=author_name,
                    source_url=source_url,
                    published_at=published_at,
                    fetched_at=fetched_at,
                    source_query=source_query,
                    parser_version=self.parser_version,
                    dedupe_key=build_dedupe_key(
                        source_name=self.source_name,
                        external_id=external_id,
                        source_url=source_url,
                        raw_text=raw_text,
                    ),
                    raw_payload_json=build_payload_snapshot(
                        {
                            "objectID": external_id,
                            "title": title,
                            "story_text": story_text,
                            "points": hit.get("points"),
                            "num_comments": hit.get("num_comments"),
                        }
                    ),
                    raw_text=raw_text,
                    cleaned_text=raw_text,
                    language="en",
                    metadata_json={
                        "platform": "x_twitter",
                        "network": "hn_algolia_fallback",
                        "points": hit.get("points"),
                        "num_comments": hit.get("num_comments"),
                        "fetch_mode": "live",
                        "pain_point_summary": pain_summary,
                    },
                )
            )

        return parsed_items

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        brand_slug = target_brand.lower().replace(" ", "-")

        stubs = [
            ("x-stub-001", "x_user_1",
             f"{target_brand} has too many duplicate property listings. Same flat shown 5 times with different prices. Waste of time."),
            ("x-stub-002", "x_user_2",
             f"Frustrated with {target_brand}. Agent called 15 times after one enquiry and never actually helped. Blocking now."),
            ("x-stub-003", "x_user_3",
             f"The {target_brand} app is crashing every time I try to apply filters for budget properties in Pune. Fix your app please."),
            ("x-stub-004", "x_user_4",
             f"Saw a great property on {target_brand} at ₹45L. Called the number — property was sold 2 months ago. Why are stale listings still up?"),
            ("x-stub-005", "x_user_5",
             f"{target_brand} does not verify builders. Friend got scammed for ₹2L token on an under-construction project. No accountability."),
        ]

        items = []
        for ext_suffix, author, text in stubs:
            ext_id = f"{brand_slug}-{ext_suffix}"
            source_url = f"https://x.com/{author}/status/{ext_suffix}"
            pain_summary = _make_pain_point_summary(text)
            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="post",
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
                    raw_text=text,
                ),
                raw_payload_json={"stub": True, "reason": fallback_reason},
                raw_text=text,
                cleaned_text=text,
                language="en",
                metadata_json={
                    "platform": "x_twitter",
                    "network": "public_social_discussion",
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                    "pain_point_summary": pain_summary,
                },
            ))
        return items

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            return self._build_stub_items(
                target_brand=target_brand,
                fallback_reason="Live fetch disabled in settings",
            )

        try:
            payload = self._fetch_live_payload(target_brand)
            items = self._parse_live_items(payload, target_brand)
            if items:
                return items

            if settings.scraper_fail_open_to_stub:
                return self._build_stub_items(
                    target_brand=target_brand,
                    fallback_reason="Live payload returned no parsable public social posts",
                )

            return []
        except Exception as exc:
            if settings.scraper_fail_open_to_stub:
                return self._build_stub_items(
                    target_brand=target_brand,
                    fallback_reason=str(exc),
                )
            raise