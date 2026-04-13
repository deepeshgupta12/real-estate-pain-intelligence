import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from app.core.config import get_settings
from app.scrapers.base import BaseSourceScraper
from app.scrapers.http_client import RetryingHttpClient
from app.scrapers.types import ScrapedItem
from app.scrapers.utils import build_dedupe_key, build_payload_snapshot, normalize_whitespace


class RedditScraper(BaseSourceScraper):
    source_name = "reddit"
    parser_version = "reddit-rss-v1"

    def _build_query(self, target_brand: str) -> str:
        return f'"{target_brand}" real estate'

    def _build_headers(self) -> dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }

    def _build_rss_url(self) -> str:
        settings = get_settings()
        return f"{settings.scraper_reddit_base_url.rstrip('/')}/search.rss"

    def _fetch_live_payload(self, target_brand: str) -> str:
        settings = get_settings()
        return RetryingHttpClient.get_text(
            self._build_rss_url(),
            params={
                "q": self._build_query(target_brand),
                "sort": "new",
                "limit": settings.scraper_max_items_per_source,
            },
            headers=self._build_headers(),
        )

    def _parse_rss_feed(self, xml_text: str, target_brand: str) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        # Reddit RSS uses Atom namespace
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        if not entries:
            # Try without namespace
            entries = root.findall(".//entry")

        parsed_items = []
        settings = get_settings()

        for entry in entries[:settings.scraper_max_items_per_source]:
            # Extract title
            title_el = entry.find("atom:title", ns) or entry.find("title")
            title = (title_el.text or "").strip() if title_el is not None else ""

            # Extract content/summary
            content_el = (
                entry.find("atom:content", ns) or entry.find("atom:summary", ns)
                or entry.find("content") or entry.find("summary")
            )
            content_html = (content_el.text or "") if content_el is not None else ""
            # Strip HTML tags from content
            content_text = re.sub(r'<[^>]+>', ' ', content_html).strip()
            content_text = normalize_whitespace(content_text)

            combined = "\n\n".join(p for p in [title, content_text] if p).strip()
            if not combined:
                continue

            # Extract URL from link element
            link_el = entry.find("atom:link", ns) or entry.find("link")
            source_url = None
            if link_el is not None:
                source_url = link_el.get("href") or link_el.text

            # Extract external_id from URL
            external_id = None
            if source_url:
                parts = [p for p in source_url.rstrip("/").split("/") if p]
                external_id = parts[-1] if parts else None

            # Extract author
            author_el = entry.find("atom:author/atom:name", ns) or entry.find("author/name")
            author = (author_el.text or "").strip() if author_el is not None else None

            # Extract published date
            updated_el = entry.find("atom:updated", ns) or entry.find("updated")
            published_at = None
            if updated_el is not None and updated_el.text:
                try:
                    published_at = datetime.fromisoformat(updated_el.text.replace("Z", "+00:00"))
                except ValueError:
                    pass

            # Extract subreddit from category
            category_el = entry.find("atom:category", ns) or entry.find("category")
            subreddit = category_el.get("term", "") if category_el is not None else ""

            parsed_items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="post",
                external_id=external_id,
                author_name=author,
                source_url=source_url,
                published_at=published_at,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=self.parser_version,
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=external_id,
                    source_url=source_url,
                    raw_text=combined,
                ),
                raw_payload_json=build_payload_snapshot({
                    "title": title,
                    "content": content_text,
                    "author": author,
                    "source_url": source_url,
                    "subreddit": subreddit,
                }),
                raw_text=combined,
                cleaned_text=combined,
                language="en",
                metadata_json={
                    "subreddit": subreddit,
                    "fetch_mode": "live",
                    "source_format": "rss",
                },
            ))

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
            xml_text = self._fetch_live_payload(target_brand)
            items = self._parse_rss_feed(xml_text, target_brand)
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