from datetime import datetime, timezone

from app.core.config import get_settings
from app.scrapers.base import BaseSourceScraper
from app.scrapers.http_client import RetryingHttpClient
from app.scrapers.types import ScrapedItem
from app.scrapers.utils import build_dedupe_key, build_payload_snapshot, normalize_whitespace


class AppReviewsScraper(BaseSourceScraper):
    source_name = "app_reviews"
    parser_version = "app-reviews-v2-live-1"

    def _build_query(self, target_brand: str) -> str:
        return f"{target_brand} app"

    def _build_headers(self) -> dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def _fetch_app_lookup_payload(self, target_brand: str) -> dict:
        settings = get_settings()
        return RetryingHttpClient.get_json(
            settings.scraper_itunes_search_base_url,
            params={
                "term": self._build_query(target_brand),
                "entity": "software",
                "limit": 1,
                "country": "in",
            },
            headers=self._build_headers(),
        )

    def _fetch_reviews_payload(self, app_id: int) -> dict:
        settings = get_settings()
        url = f"{settings.scraper_apple_reviews_base_url}/page=1/id={app_id}/sortby=mostrecent/json"
        return RetryingHttpClient.get_json(
            url,
            params={"l": "en", "cc": "in"},
            headers=self._build_headers(),
        )

    def _parse_live_items(self, target_brand: str, lookup_payload: dict, reviews_payload: dict) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)

        results = lookup_payload.get("results") or []
        if not results:
            return []

        app_meta = results[0]
        app_id = app_meta.get("trackId")
        app_name = app_meta.get("trackName") or target_brand
        app_store_url = app_meta.get("trackViewUrl")

        feed = reviews_payload.get("feed") or {}
        entries = feed.get("entry") or []

        if isinstance(entries, dict):
            entries = [entries]

        parsed_items: list[ScrapedItem] = []

        for entry in entries:
            review_id = (entry.get("id") or {}).get("label")
            if not review_id:
                continue

            author_name = ((entry.get("author") or {}).get("name") or {}).get("label")
            title = (entry.get("title") or {}).get("label") or ""
            content = (entry.get("content") or {}).get("label") or ""
            rating = (entry.get("im:rating") or {}).get("label")
            updated_at_raw = (entry.get("updated") or {}).get("label")
            source_url = (entry.get("link") or {}).get("attributes", {}).get("href") or app_store_url

            combined_text = normalize_whitespace(" ".join(part for part in [title, content] if part))
            if not combined_text:
                continue

            published_at = None
            if updated_at_raw:
                normalized = updated_at_raw.replace("Z", "+00:00")
                published_at = datetime.fromisoformat(normalized)

            parsed_items.append(
                ScrapedItem(
                    source_name=self.source_name,
                    platform_name=target_brand,
                    content_type="review",
                    external_id=review_id,
                    author_name=author_name,
                    source_url=source_url,
                    published_at=published_at,
                    fetched_at=fetched_at,
                    source_query=source_query,
                    parser_version=self.parser_version,
                    dedupe_key=build_dedupe_key(
                        source_name=self.source_name,
                        external_id=review_id,
                        source_url=source_url,
                        raw_text=combined_text,
                    ),
                    raw_payload_json=build_payload_snapshot(
                        {
                            "review_id": review_id,
                            "title": title,
                            "content": content,
                            "rating": rating,
                            "app_id": app_id,
                            "app_name": app_name,
                        }
                    ),
                    raw_text=combined_text,
                    cleaned_text=combined_text,
                    language="en",
                    metadata_json={
                        "store": "apple_app_store",
                        "app_id": app_id,
                        "app_name": app_name,
                        "rating": rating,
                        "fetch_mode": "live",
                    },
                )
            )

        return parsed_items

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        brand_slug = target_brand.lower().replace(" ", "-")

        stubs = [
            ("app-stub-001", 2, "app_user_1",
             f"The {target_brand} app feels very slow and the property leads shown don't match my budget intent at all."),
            ("app-stub-002", 1, "app_user_2",
             f"{target_brand} app crashes on Android when switching between listings. Very annoying, lost interest 3 times."),
            ("app-stub-003", 3, "app_user_3",
             f"Good property selection on {target_brand} but the in-app chat with agents never works. Always shows error."),
            ("app-stub-004", 2, "app_user_4",
             f"Notifications from {target_brand} are spammy. I get 10+ alerts daily for properties I have no interest in. Can't turn them off."),
            ("app-stub-005", 1, "app_user_5",
             f"The {target_brand} search filter resets every time I leave the app. I have to set city, budget and BHK again and again. Frustrating UX."),
        ]

        items = []
        for ext_suffix, rating, author, text in stubs:
            ext_id = f"{brand_slug}-{ext_suffix}"
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
                    "store": "app_store",
                    "rating": str(rating),
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
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
            lookup_payload = self._fetch_app_lookup_payload(target_brand)
            results = lookup_payload.get("results") or []
            if not results:
                if settings.scraper_fail_open_to_stub:
                    return self._build_stub_items(
                        target_brand=target_brand,
                        fallback_reason="No app lookup results found",
                    )
                return []

            app_id = results[0].get("trackId")
            if app_id is None:
                if settings.scraper_fail_open_to_stub:
                    return self._build_stub_items(
                        target_brand=target_brand,
                        fallback_reason="App lookup result did not contain trackId",
                    )
                return []

            reviews_payload = self._fetch_reviews_payload(int(app_id))
            items = self._parse_live_items(target_brand, lookup_payload, reviews_payload)
            if items:
                return items

            if settings.scraper_fail_open_to_stub:
                return self._build_stub_items(
                    target_brand=target_brand,
                    fallback_reason="Live payload returned no parsable app reviews",
                )

            return []
        except Exception as exc:
            if settings.scraper_fail_open_to_stub:
                return self._build_stub_items(
                    target_brand=target_brand,
                    fallback_reason=str(exc),
                )
            raise