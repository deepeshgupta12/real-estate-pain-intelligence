import random
import re
import time
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
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }

    def _build_review_urls(self, target_brand: str) -> list[str]:
        """Try multiple URL patterns if first fails."""
        settings = get_settings()
        slug = slugify_identifier(target_brand)
        return [
            f"{settings.scraper_review_sites_base_url.rstrip('/')}/{slug}.com",
            f"{settings.scraper_review_sites_base_url.rstrip('/')}/{slug}",
            f"https://www.ambitionbox.com/reviews/{slug}-reviews",
        ]

    def _fetch_reviews_html(self, target_brand: str) -> str:
        urls = self._build_review_urls(target_brand)
        last_exception: Exception | None = None

        for url in urls:
            try:
                # Add delay before fetching
                time.sleep(random.uniform(1.0, 2.5))
                return RetryingHttpClient.get_text(
                    url,
                    headers=self._build_headers(),
                )
            except Exception as exc:
                last_exception = exc
                continue

        if last_exception:
            raise last_exception
        raise RuntimeError(f"Failed to fetch reviews for {target_brand} from all URLs")

    def _parse_live_items(self, html_text: str, target_brand: str) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        source_url = self._build_review_urls(target_brand)[0]

        pattern = re.compile(
            r'<article.*?(?:data-service-review-id|class="[^"]*review[^"]*"|data-review-content-text).*?>.*?'
            r'(?:<h2.*?>.*?</h2>)?.*?'
            r'(?P<body><p[^>]*>(.*?)</p>|data-review-content-text[^>]*>(.*?)</)',
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