import logging
import xml.etree.ElementTree as ET
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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Brand → known official channel ID map (verified as of 2024)
# These are used as Tier 1 to get the brand's own upload feed.
# Channel IDs can be found at: youtube.com/@handle → view-source → "channelId"
# ---------------------------------------------------------------------------
BRAND_CHANNEL_MAP: dict[str, list[str]] = {
    "square yards": ["UCT4lJHHMSFHuuHFeyZxAuKA"],
    "99acres":       ["UC4K4pCcwkz5fOsAzTMvnMUQ"],
    "magicbricks":   ["UCIwu4PBhEM-EFnBqKbXNi6A"],
    "housing":       ["UCdkl5YM_8kn4Guk0R5IVMFA"],
    "nobroker":      ["UCC5AHmMM39xl7pHQSdwjPtQ"],
    "commonfloor":   ["UCgDfRwlxYMSzAVRDSNb3kgA"],
    "proptiger":     ["UCjXCzVHXYF0YdkSwzV5HKOA"],
}

YOUTUBE_FEED_BASE = "https://www.youtube.com/feeds/videos.xml"


class YouTubeScraper(BaseSourceScraper):
    source_name = "youtube"
    parser_version = "youtube-ytdlp-v1"

    # ------------------------------------------------------------------
    # Query builders
    # ------------------------------------------------------------------

    def _build_query(self, target_brand: str) -> str:
        return f'"{target_brand}" real estate review'

    def _build_search_query(self, target_brand: str) -> str:
        # yt-dlp search prefix: ytsearchN:query
        return f"{target_brand} real estate app review India"

    def _get_channel_ids(self, target_brand: str) -> list[str]:
        brand_lower = target_brand.lower().strip()
        for key, channels in BRAND_CHANNEL_MAP.items():
            if key in brand_lower or brand_lower in key:
                return channels
        return []

    # ------------------------------------------------------------------
    # Tier 1: yt-dlp search (primary — no API key required)
    # ------------------------------------------------------------------

    def _scrape_via_ytdlp(self, target_brand: str) -> list[ScrapedItem]:
        """
        Use yt-dlp to search YouTube and extract video metadata.
        yt-dlp handles all anti-bot measures and ytInitialData parsing.
        This works without a YouTube Data API key.
        """
        settings = get_settings()
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        search_query = self._build_search_query(target_brand)
        n = settings.scraper_max_items_per_source

        try:
            import yt_dlp  # type: ignore[import]
        except ImportError:
            logger.warning("yt-dlp not installed — skipping YouTube yt-dlp scrape")
            return []

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,    # don't download, just get metadata
            "skip_download": True,
            "noplaylist": False,
            "socket_timeout": 15,
        }

        search_url = f"ytsearch{n}:{search_query}"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_url, download=False)
        except Exception as exc:
            logger.warning("yt-dlp search failed for '%s': %s", target_brand, exc)
            return []

        if not info or not isinstance(info, dict):
            return []

        entries = info.get("entries") or []
        items: list[ScrapedItem] = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            video_id = entry.get("id") or ""
            title = (entry.get("title") or "").strip()
            description = normalize_whitespace(entry.get("description") or "")
            uploader = entry.get("uploader") or entry.get("channel") or None
            source_url = entry.get("webpage_url") or (
                f"https://www.youtube.com/watch?v={video_id}" if video_id else None
            )
            upload_date = entry.get("upload_date")  # YYYYMMDD string

            published_at = None
            if upload_date and len(upload_date) == 8:
                try:
                    published_at = datetime.strptime(upload_date, "%Y%m%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    pass

            combined = "\n\n".join(p for p in [title, description] if p).strip()
            if not combined:
                continue

            ext_id = f"yt-{video_id}" if video_id else None

            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="video",
                external_id=ext_id,
                author_name=uploader,
                source_url=source_url,
                published_at=published_at,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version=self.parser_version,
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=ext_id,
                    source_url=source_url,
                    raw_text=combined,
                ),
                raw_payload_json=build_payload_snapshot({
                    "video_id": video_id,
                    "title": title,
                    "view_count": entry.get("view_count"),
                    "like_count": entry.get("like_count"),
                    "comment_count": entry.get("comment_count"),
                    "channel": uploader,
                }),
                raw_text=combined,
                cleaned_text=combined,
                language="en",
                metadata_json={
                    "video_id": video_id,
                    "fetch_mode": "ytdlp_search",
                    "search_query": search_query,
                    "view_count": entry.get("view_count"),
                },
            ))

        logger.info("yt-dlp: found %d videos for '%s'", len(items), target_brand)
        return items

    # ------------------------------------------------------------------
    # Tier 2: YouTube channel RSS (known brand channels)
    # ------------------------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/atom+xml, application/xml, text/xml, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _fetch_channel_feed(self, channel_id: str) -> str:
        return RetryingHttpClient.get_text(
            YOUTUBE_FEED_BASE,
            params={"channel_id": channel_id},
            headers=self._build_headers(),
        )

    def _parse_channel_feed(self, xml_text: str, target_brand: str, channel_id: str) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        settings = get_settings()

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
            "media": "http://search.yahoo.com/mrss/",
        }

        entries = root.findall("atom:entry", ns)
        if not entries:
            entries = root.findall(".//entry")

        parsed_items: list[ScrapedItem] = []

        for entry in entries[:settings.scraper_max_items_per_source]:
            video_id_el = entry.find("yt:videoId", ns) or entry.find("videoId")
            video_id = (video_id_el.text or "").strip() if video_id_el is not None else ""

            title_el = entry.find("atom:title", ns) or entry.find("title")
            title = (title_el.text or "").strip() if title_el is not None else ""

            desc_el = (
                entry.find("media:group/media:description", ns)
                or entry.find(".//description")
            )
            description = normalize_whitespace(
                (desc_el.text or "").strip() if desc_el is not None else ""
            )

            combined = "\n\n".join(p for p in [title, description] if p).strip()
            if not combined:
                continue

            source_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
            ext_id = f"yt-{video_id}" if video_id else None

            published_el = entry.find("atom:published", ns) or entry.find("published")
            published_at = None
            if published_el is not None and published_el.text:
                try:
                    published_at = datetime.fromisoformat(
                        published_el.text.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            author_el = (
                entry.find("atom:author/atom:name", ns) or entry.find("author/name")
            )
            author = (author_el.text or "").strip() if author_el is not None else None

            parsed_items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="video",
                external_id=ext_id,
                author_name=author,
                source_url=source_url,
                published_at=published_at,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version="youtube-rss-v1",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=ext_id,
                    source_url=source_url,
                    raw_text=combined,
                ),
                raw_payload_json=build_payload_snapshot({
                    "video_id": video_id,
                    "channel_id": channel_id,
                    "title": title,
                    "description": description,
                }),
                raw_text=combined,
                cleaned_text=combined,
                language="en",
                metadata_json={
                    "video_id": video_id,
                    "channel_id": channel_id,
                    "fetch_mode": "channel_rss",
                },
            ))

        return parsed_items

    def _scrape_via_channel_rss(self, target_brand: str) -> list[ScrapedItem]:
        settings = get_settings()
        channel_ids = self._get_channel_ids(target_brand)
        if not channel_ids:
            return []

        all_items: list[ScrapedItem] = []
        for channel_id in channel_ids:
            try:
                xml_text = self._fetch_channel_feed(channel_id)
                items = self._parse_channel_feed(xml_text, target_brand, channel_id)
                all_items.extend(items)
                if len(all_items) >= settings.scraper_max_items_per_source:
                    break
            except Exception as exc:
                logger.warning("YouTube channel RSS %s failed: %s", channel_id, exc)
                continue

        return all_items[:settings.scraper_max_items_per_source]

    # ------------------------------------------------------------------
    # Tier 3: stub items (only if SCRAPER_FAIL_OPEN_TO_STUB=true in .env)
    # ------------------------------------------------------------------

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        brand_slug = target_brand.lower().replace(" ", "-")

        stubs = [
            ("yt-stub-ex1", "yt_reviewer_1",
             f"{target_brand} Project Walkthrough Review 2024",
             f"We visited the {target_brand} listed properties in Bangalore. The listings look good on app "
             f"but on-ground reality is different — 3 out of 5 units were already sold. Very misleading."),
            ("yt-stub-ex2", "yt_reviewer_2",
             f"{target_brand} App Review: Is It Worth Using?",
             f"I have been using {target_brand} for 3 months. The app is slow to load and the search "
             f"filters don't work well. Agents listed don't respond to calls or messages."),
            ("yt-stub-ex3", "yt_reviewer_3",
             f"My Experience Buying a Home Through {target_brand}",
             f"The {target_brand} platform showed budget-friendly options but hidden charges were added "
             f"later. The final price was 15% more than what was shown. Not transparent at all."),
            ("yt-stub-ex4", "yt_reviewer_4",
             f"{target_brand} vs Competitors: Honest Review",
             f"Comparing {target_brand} with other portals — the photo quality is lower and many listings "
             f"lack RERA numbers. Customer support took 4 days to respond to my query."),
            ("yt-stub-ex5", "yt_reviewer_5",
             f"Fraud Alert: My {target_brand} Experience",
             f"Lost my token money after booking through {target_brand}. The builder was not verified. "
             f"Platform does not take responsibility. Beware of unverified listings."),
        ]

        items = []
        for video_id, author, title, description in stubs:
            ext_id = f"youtube-{brand_slug}-{video_id}"
            source_url = f"https://youtube.com/watch?v={video_id}"
            combined = f"{title}\n\n{description}"
            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="video",
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
                    raw_text=combined,
                ),
                raw_payload_json={"stub": True, "reason": fallback_reason, "title": title},
                raw_text=combined,
                cleaned_text=combined,
                language="en",
                metadata_json={
                    "video_id": video_id,
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                },
            ))
        return items

    # ------------------------------------------------------------------
    # Main scrape method
    # ------------------------------------------------------------------

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            logger.info("YouTube: live fetch disabled, returning stub data")
            return self._build_stub_items(target_brand, "Live fetch disabled in settings")

        # Tier 1: yt-dlp search (most reliable, no API key)
        items = self._scrape_via_ytdlp(target_brand)
        if items:
            return items

        logger.warning("YouTube yt-dlp returned 0 items for '%s', trying channel RSS", target_brand)

        # Tier 2: known brand channel RSS feed
        items = self._scrape_via_channel_rss(target_brand)
        if items:
            logger.info("YouTube RSS: %d items for '%s'", len(items), target_brand)
            return items

        logger.warning("YouTube RSS returned 0 items for '%s'", target_brand)

        # Tier 3: stub (only when explicitly enabled — NOT the default)
        if settings.scraper_fail_open_to_stub:
            logger.info("YouTube: SCRAPER_FAIL_OPEN_TO_STUB=true — returning stub data")
            return self._build_stub_items(target_brand, "All live YouTube tiers failed")

        logger.warning(
            "YouTube: all live tiers failed for '%s'. "
            "Set SCRAPER_FAIL_OPEN_TO_STUB=true to enable stub fallback.",
            target_brand,
        )
        return []
