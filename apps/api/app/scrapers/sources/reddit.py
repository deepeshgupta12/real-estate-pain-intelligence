from datetime import datetime, timezone

from app.core.config import get_settings
from app.scrapers.base import BaseSourceScraper
from app.scrapers.http_client import RetryingHttpClient
from app.scrapers.types import ScrapedItem
from app.scrapers.utils import build_dedupe_key, build_payload_snapshot, normalize_whitespace


class RedditScraper(BaseSourceScraper):
    source_name = "reddit"
    parser_version = "reddit-v2-live-1"

    def _build_query(self, target_brand: str) -> str:
        return f'"{target_brand}" real estate'

    def _build_headers(self) -> dict[str, str]:
        settings = get_settings()
        return {
            "User-Agent": settings.scraper_user_agent,
            "Accept": "application/json",
        }

    def _build_url(self) -> str:
        settings = get_settings()
        return f"{settings.scraper_reddit_base_url.rstrip('/')}/search.json"

    def _fetch_live_payload(self, target_brand: str) -> dict:
        settings = get_settings()
        return RetryingHttpClient.get_json(
            self._build_url(),
            params={
                "q": self._build_query(target_brand),
                "limit": settings.scraper_max_items_per_source,
                "sort": "new",
                "restrict_sr": "0",
                "raw_json": "1",
            },
            headers=self._build_headers(),
        )

    def _build_source_url(self, permalink: str | None) -> str | None:
        if not permalink:
            return None
        return f"https://www.reddit.com{permalink}"

    def _parse_live_items(self, payload: dict, target_brand: str) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        children = (payload.get("data") or {}).get("children") or []

        parsed_items: list[ScrapedItem] = []

        for child in children:
            data = child.get("data") or {}

            title = (data.get("title") or "").strip()
            selftext = (data.get("selftext") or "").strip()
            combined_text = "\n\n".join(part for part in [title, selftext] if part).strip()
            normalized_text = normalize_whitespace(combined_text)

            if not normalized_text:
                continue

            external_id = data.get("id")
            source_url = self._build_source_url(data.get("permalink"))
            published_at = None
            if data.get("created_utc") is not None:
                published_at = datetime.fromtimestamp(float(data["created_utc"]), tz=timezone.utc)

            raw_payload = {
                "id": data.get("id"),
                "name": data.get("name"),
                "subreddit": data.get("subreddit"),
                "title": data.get("title"),
                "selftext": data.get("selftext"),
                "author": data.get("author"),
                "permalink": data.get("permalink"),
                "score": data.get("score"),
                "num_comments": data.get("num_comments"),
                "created_utc": data.get("created_utc"),
            }

            parsed_items.append(
                ScrapedItem(
                    source_name=self.source_name,
                    platform_name=target_brand,
                    content_type="post",
                    external_id=external_id,
                    author_name=data.get("author"),
                    source_url=source_url,
                    published_at=published_at,
                    fetched_at=fetched_at,
                    source_query=source_query,
                    parser_version=self.parser_version,
                    dedupe_key=build_dedupe_key(
                        source_name=self.source_name,
                        external_id=external_id,
                        source_url=source_url,
                        raw_text=normalized_text,
                    ),
                    raw_payload_json=build_payload_snapshot(raw_payload),
                    raw_text=combined_text,
                    cleaned_text=normalized_text,
                    language="en",
                    metadata_json={
                        "subreddit": data.get("subreddit"),
                        "score": data.get("score"),
                        "num_comments": data.get("num_comments"),
                        "fetch_mode": "live",
                    },
                )
            )

        return parsed_items

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)

        first_text = f"{target_brand} has too many stale listings and delayed callbacks."
        second_text = f"I enquired on {target_brand} but received irrelevant follow-up responses."

        return [
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="post",
                external_id=f"reddit-{target_brand.lower().replace(' ', '-')}-001",
                author_name="reddit_user_1",
                source_url="https://reddit.com/example-thread-1",
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=f"{self.parser_version}-stub",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=f"reddit-{target_brand.lower().replace(' ', '-')}-001",
                    source_url="https://reddit.com/example-thread-1",
                    raw_text=first_text,
                ),
                raw_payload_json={"stub": True, "reason": fallback_reason},
                raw_text=first_text,
                cleaned_text=first_text,
                language="en",
                metadata_json={
                    "subreddit": "indianrealestate",
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                },
            ),
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="comment",
                external_id=f"reddit-{target_brand.lower().replace(' ', '-')}-002",
                author_name="reddit_user_2",
                source_url="https://reddit.com/example-thread-2",
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=f"{self.parser_version}-stub",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=f"reddit-{target_brand.lower().replace(' ', '-')}-002",
                    source_url="https://reddit.com/example-thread-2",
                    raw_text=second_text,
                ),
                raw_payload_json={"stub": True, "reason": fallback_reason},
                raw_text=second_text,
                cleaned_text=second_text,
                language="en",
                metadata_json={
                    "subreddit": "realestateindia",
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                },
            ),
        ]

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
                    fallback_reason="Live payload returned no parsable items",
                )

            return []
        except Exception as exc:
            if settings.scraper_fail_open_to_stub:
                return self._build_stub_items(
                    target_brand=target_brand,
                    fallback_reason=str(exc),
                )
            raise