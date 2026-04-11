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
)


class YouTubeScraper(BaseSourceScraper):
    source_name = "youtube"
    parser_version = "youtube-v2-live-1"

    def _build_query(self, target_brand: str) -> str:
        return f'"{target_brand}" property review'

    def _build_headers(self) -> dict[str, str]:
        settings = get_settings()
        return {
            "User-Agent": settings.scraper_user_agent,
            "Accept": "text/html,application/xhtml+xml",
        }

    def _fetch_search_html(self, target_brand: str) -> str:
        settings = get_settings()
        return RetryingHttpClient.get_text(
            settings.scraper_youtube_search_base_url,
            params={"search_query": self._build_query(target_brand)},
            headers=self._build_headers(),
        )

    def _fetch_watch_html(self, video_id: str) -> str:
        settings = get_settings()
        return RetryingHttpClient.get_text(
            settings.scraper_youtube_watch_base_url,
            params={"v": video_id},
            headers=self._build_headers(),
        )

    def _extract_video_ids(self, html_text: str) -> list[str]:
        matches = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', html_text)
        if not matches:
            matches = re.findall(r"watch\?v=([A-Za-z0-9_-]{11})", html_text)

        unique_ids: list[str] = []
        seen: set[str] = set()
        settings = get_settings()

        for video_id in matches:
            if video_id in seen:
                continue
            seen.add(video_id)
            unique_ids.append(video_id)
            if len(unique_ids) >= settings.scraper_max_items_per_source:
                break

        return unique_ids

    def _extract_video_title(self, html_text: str) -> str:
        match = re.search(r"<title>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return "YouTube video"
        title = normalize_whitespace(match.group(1))
        return title.replace("- YouTube", "").strip()

    def _extract_comment_pairs(self, html_text: str) -> list[tuple[str | None, str]]:
        pattern = re.compile(
            r'"authorText":\{"simpleText":"(?P<author>[^"]+)"\}.*?"contentText":\{"runs":\[(?P<runs>.*?)\]\}',
            flags=re.DOTALL,
        )
        pairs: list[tuple[str | None, str]] = []

        for match in pattern.finditer(html_text):
            author = match.group("author")
            runs = match.group("runs")
            text_parts = re.findall(r'"text":"(.*?)"', runs)
            comment_text = normalize_whitespace(" ".join(text_parts))
            if comment_text:
                pairs.append((author, comment_text))

        return pairs

    def _parse_live_items(self, target_brand: str, search_html: str) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        video_ids = self._extract_video_ids(search_html)

        parsed_items: list[ScrapedItem] = []
        settings = get_settings()

        for video_id in video_ids[: settings.scraper_max_items_per_source]:
            watch_html = self._fetch_watch_html(video_id)
            video_title = self._extract_video_title(watch_html)
            comment_pairs = self._extract_comment_pairs(watch_html)

            for index, (author_name, comment_text) in enumerate(comment_pairs, start=1):
                source_url = f"{settings.scraper_youtube_watch_base_url}?v={video_id}"
                external_id = f"{video_id}:{index}"

                parsed_items.append(
                    ScrapedItem(
                        source_name=self.source_name,
                        platform_name=target_brand,
                        content_type="comment",
                        external_id=external_id,
                        author_name=author_name,
                        source_url=source_url,
                        published_at=None,
                        fetched_at=fetched_at,
                        source_query=source_query,
                        parser_version=self.parser_version,
                        dedupe_key=build_dedupe_key(
                            source_name=self.source_name,
                            external_id=external_id,
                            source_url=source_url,
                            raw_text=comment_text,
                        ),
                        raw_payload_json=build_payload_snapshot(
                            {
                                "video_id": video_id,
                                "video_title": video_title,
                                "author_name": author_name,
                                "comment_text": comment_text,
                            }
                        ),
                        raw_text=comment_text,
                        cleaned_text=comment_text,
                        language="en",
                        metadata_json={
                            "video_id": video_id,
                            "video_title": video_title,
                            "fetch_mode": "live",
                        },
                    )
                )

        return parsed_items

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)

        stub_text = (
            f"The {target_brand} project walkthrough looked good, but users in comments "
            f"complained about outdated inventory."
        )
        source_url = "https://youtube.com/watch?v=example1"
        external_id = f"youtube-{target_brand.lower().replace(' ', '-')}-001"

        return [
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="comment",
                external_id=external_id,
                author_name="yt_viewer_1",
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
                    "video_id": "example1",
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
            search_html = self._fetch_search_html(target_brand)
            items = self._parse_live_items(target_brand, search_html)
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