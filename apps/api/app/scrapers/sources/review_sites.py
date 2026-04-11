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
    strip_html_tags,
)


class ReviewSitesScraper(BaseSourceScraper):
    source_name = "review_sites"
    parser_version = "review-sites-v2-live-1"

    def _build_query(self, target_brand: str) -> str:
        return f"{target_brand} reviews"

    def _build_headers(self) -> dict[str, str]:
        settings = get_settings()
        return {
            "User-Agent": settings.scraper_user_agent,
            "Accept": "text/html,application/xhtml+xml",
        }

    def _build_review_url(self, target_brand: str) -> str:
        settings = get_settings()
        slug = slugify_identifier(target_brand)
        return f"{settings.scraper_review_sites_base_url.rstrip('/')}/{slug}.com"

    def _fetch_reviews_html(self, target_brand: str) -> str:
        return RetryingHttpClient.get_text(
            self._build_review_url(target_brand),
            headers=self._build_headers(),
        )

    def _parse_live_items(self, html_text: str, target_brand: str) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        source_url = self._build_review_url(target_brand)

        pattern = re.compile(
            r'<article.*?(?:data-service-review-id|class="[^"]*review[^"]*").*?>.*?'
            r'(?:<h2.*?>.*?</h2>)?.*?'
            r'(?P<body><p[^>]*>(.*?)</p>)',
            flags=re.DOTALL | re.IGNORECASE,
        )

        parsed_items: list[ScrapedItem] = []
        index = 0

        for match in pattern.finditer(html_text):
            body_html = match.group("body")
            review_text = strip_html_tags(body_html)
            if not review_text:
                continue

            index += 1
            external_id = f"{slugify_identifier(target_brand)}-review-{index}"

            parsed_items.append(
                ScrapedItem(
                    source_name=self.source_name,
                    platform_name=target_brand,
                    content_type="review",
                    external_id=external_id,
                    author_name=None,
                    source_url=source_url,
                    published_at=None,
                    fetched_at=fetched_at,
                    source_query=source_query,
                    parser_version=self.parser_version,
                    dedupe_key=build_dedupe_key(
                        source_name=self.source_name,
                        external_id=external_id,
                        source_url=source_url,
                        raw_text=review_text,
                    ),
                    raw_payload_json=build_payload_snapshot(
                        {
                            "review_index": index,
                            "review_text": review_text,
                            "site": "trustpilot",
                        }
                    ),
                    raw_text=review_text,
                    cleaned_text=normalize_whitespace(review_text),
                    language="en",
                    metadata_json={
                        "site": "trustpilot",
                        "fetch_mode": "live",
                    },
                )
            )

        return parsed_items

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        stub_text = f"Review-site feedback suggests {target_brand} has poor response quality after enquiry."
        external_id = f"review-{target_brand.lower().replace(' ', '-')}-001"
        source_url = "https://example-review-site.com/review/1"

        return [
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="review",
                external_id=external_id,
                author_name="review_user_1",
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
                    "site": "example-review-site",
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
            html_text = self._fetch_reviews_html(target_brand)
            items = self._parse_live_items(html_text, target_brand)
            if items:
                return items

            if settings.scraper_fail_open_to_stub:
                return self._build_stub_items(
                    target_brand=target_brand,
                    fallback_reason="Live payload returned no parsable review-site items",
                )

            return []
        except Exception as exc:
            if settings.scraper_fail_open_to_stub:
                return self._build_stub_items(
                    target_brand=target_brand,
                    fallback_reason=str(exc),
                )
            raise