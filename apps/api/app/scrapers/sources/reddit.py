"""
Reddit scraper with three-tier fallback:
  1. PRAW (official Reddit API) — requires REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET
  2. Reddit RSS feed           — no auth, but often blocked/rate-limited
  3. Stub data                 — always works, used when SCRAPER_FAIL_OPEN_TO_STUB=true
"""
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from app.core.config import get_settings
from app.scrapers.base import BaseSourceScraper
from app.scrapers.http_client import RetryingHttpClient
from app.scrapers.types import ScrapedItem
from app.scrapers.utils import build_dedupe_key, build_payload_snapshot, normalize_whitespace

logger = logging.getLogger(__name__)

# Subreddits to search for Indian real estate content
INDIA_REALESTATE_SUBREDDITS = [
    "indianrealestate",
    "realestateindia",
    "india",
    "mumbai",
    "bangalore",
    "delhi",
    "pune",
    "hyderabad",
]


class RedditScraper(BaseSourceScraper):
    source_name = "reddit"
    parser_version = "reddit-praw-v1"

    def _build_query(self, target_brand: str) -> str:
        return f'"{target_brand}" real estate'

    # ------------------------------------------------------------------
    # Tier 1: PRAW — Official Reddit API
    # ------------------------------------------------------------------

    def _scrape_via_praw(self, target_brand: str) -> list[ScrapedItem]:
        """Use the official Reddit API via PRAW. Returns [] if PRAW unavailable."""
        settings = get_settings()

        try:
            import praw  # type: ignore
        except ImportError:
            logger.debug("praw not installed; skipping PRAW tier")
            return []

        if not settings.reddit_client_id or not settings.reddit_client_secret:
            logger.debug("Reddit API credentials not configured; skipping PRAW tier")
            return []

        try:
            reddit = praw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent,
                username=settings.reddit_username or None,
                password=settings.reddit_password or None,
                # read-only mode when no username/password
                read_only=not (settings.reddit_username and settings.reddit_password),
            )

            query = self._build_query(target_brand)
            fetched_at = datetime.now(timezone.utc)
            items: list[ScrapedItem] = []
            limit = settings.scraper_max_items_per_source

            # Search across targeted subreddits first, then globally
            subreddit_str = "+".join(INDIA_REALESTATE_SUBREDDITS)
            search_targets = [
                (reddit.subreddit(subreddit_str), "subreddit_search"),
                (reddit.subreddit("all"), "global_search"),
            ]

            seen_ids: set[str] = set()

            for subreddit_obj, mode in search_targets:
                if len(items) >= limit:
                    break
                try:
                    results = subreddit_obj.search(
                        query,
                        sort="new",
                        time_filter="year",
                        limit=limit,
                    )
                    for submission in results:
                        if len(items) >= limit:
                            break
                        if submission.id in seen_ids:
                            continue
                        seen_ids.add(submission.id)

                        title = submission.title or ""
                        body = submission.selftext or ""
                        combined = "\n\n".join(p for p in [title, body] if p).strip()
                        if not combined or combined == "[removed]" or combined == "[deleted]":
                            continue

                        source_url = f"https://reddit.com{submission.permalink}"
                        published_at = datetime.fromtimestamp(
                            submission.created_utc, tz=timezone.utc
                        )

                        items.append(ScrapedItem(
                            source_name=self.source_name,
                            platform_name=target_brand,
                            content_type="post",
                            external_id=submission.id,
                            author_name=str(submission.author) if submission.author else None,
                            source_url=source_url,
                            published_at=published_at,
                            fetched_at=fetched_at,
                            source_query=query,
                            parser_version=self.parser_version,
                            dedupe_key=build_dedupe_key(
                                source_name=self.source_name,
                                external_id=submission.id,
                                source_url=source_url,
                                raw_text=combined,
                            ),
                            raw_payload_json=build_payload_snapshot({
                                "title": title,
                                "body": body,
                                "score": submission.score,
                                "num_comments": submission.num_comments,
                                "subreddit": str(submission.subreddit),
                                "author": str(submission.author),
                                "search_mode": mode,
                            }),
                            raw_text=combined,
                            cleaned_text=combined,
                            language="en",
                            metadata_json={
                                "subreddit": str(submission.subreddit),
                                "score": submission.score,
                                "num_comments": submission.num_comments,
                                "fetch_mode": "praw",
                                "search_mode": mode,
                            },
                        ))

                        # Also collect top comments for richer signal
                        try:
                            submission.comments.replace_more(limit=0)
                            for comment in submission.comments[:3]:
                                if len(items) >= limit:
                                    break
                                comment_text = (comment.body or "").strip()
                                if not comment_text or comment_text in ("[removed]", "[deleted]"):
                                    continue
                                comment_url = f"https://reddit.com{comment.permalink}"
                                items.append(ScrapedItem(
                                    source_name=self.source_name,
                                    platform_name=target_brand,
                                    content_type="comment",
                                    external_id=comment.id,
                                    author_name=str(comment.author) if comment.author else None,
                                    source_url=comment_url,
                                    published_at=datetime.fromtimestamp(
                                        comment.created_utc, tz=timezone.utc
                                    ),
                                    fetched_at=fetched_at,
                                    source_query=query,
                                    parser_version=self.parser_version,
                                    dedupe_key=build_dedupe_key(
                                        source_name=self.source_name,
                                        external_id=comment.id,
                                        source_url=comment_url,
                                        raw_text=comment_text,
                                    ),
                                    raw_payload_json=build_payload_snapshot({
                                        "body": comment_text,
                                        "score": comment.score,
                                        "parent_id": submission.id,
                                    }),
                                    raw_text=comment_text,
                                    cleaned_text=comment_text,
                                    language="en",
                                    metadata_json={
                                        "subreddit": str(submission.subreddit),
                                        "score": comment.score,
                                        "parent_post_id": submission.id,
                                        "fetch_mode": "praw",
                                        "search_mode": "comment",
                                    },
                                ))
                        except Exception:
                            pass  # comments are best-effort

                except Exception as e:
                    logger.warning("PRAW search failed for mode %s: %s", mode, e)
                    continue

            logger.info("Reddit PRAW: fetched %d items for '%s'", len(items), target_brand)
            return items

        except Exception as exc:
            logger.warning("Reddit PRAW scrape failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Tier 2: PullPush.io — Pushshift-compatible Reddit archive (no auth)
    # ------------------------------------------------------------------

    def _scrape_via_pullpush(self, target_brand: str) -> list[ScrapedItem]:
        """
        PullPush.io (https://pullpush.io) is a community-run Reddit data service
        that indexes public posts. No authentication required.
        """
        settings = get_settings()
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)

        try:
            payload = RetryingHttpClient.get_json(
                "https://api.pullpush.io/reddit/search/submission/",
                params={
                    "q": target_brand,
                    "sort": "desc",
                    "sort_type": "created_utc",
                    "size": settings.scraper_max_items_per_source,
                    "subreddit": ",".join(INDIA_REALESTATE_SUBREDDITS[:4]),
                },
                headers={"User-Agent": settings.scraper_user_agent},
                use_browser_headers=False,
            )

            hits = payload.get("data") or []
            items: list[ScrapedItem] = []

            for post in hits:
                title = (post.get("title") or "").strip()
                body = (post.get("selftext") or "").strip()
                if body in ("[removed]", "[deleted]", ""):
                    body = ""
                combined = "\n\n".join(p for p in [title, body] if p).strip()
                if not combined:
                    continue

                post_id = post.get("id") or ""
                subreddit = post.get("subreddit") or ""
                author = post.get("author") or None
                created_utc = post.get("created_utc")
                source_url = f"https://reddit.com/r/{subreddit}/comments/{post_id}/"
                published_at = None
                if created_utc:
                    try:
                        published_at = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
                    except Exception:
                        pass

                items.append(ScrapedItem(
                    source_name=self.source_name,
                    platform_name=target_brand,
                    content_type="post",
                    external_id=post_id,
                    author_name=author,
                    source_url=source_url,
                    published_at=published_at,
                    fetched_at=fetched_at,
                    source_query=source_query,
                    parser_version="reddit-pullpush-v1",
                    dedupe_key=build_dedupe_key(
                        source_name=self.source_name,
                        external_id=post_id,
                        source_url=source_url,
                        raw_text=combined,
                    ),
                    raw_payload_json=build_payload_snapshot({
                        "title": title,
                        "body": body,
                        "score": post.get("score"),
                        "num_comments": post.get("num_comments"),
                        "subreddit": subreddit,
                    }),
                    raw_text=combined,
                    cleaned_text=combined,
                    language="en",
                    metadata_json={
                        "subreddit": subreddit,
                        "score": post.get("score"),
                        "num_comments": post.get("num_comments"),
                        "fetch_mode": "pullpush",
                    },
                ))

            logger.info("PullPush: fetched %d items for '%s'", len(items), target_brand)
            return items

        except Exception as exc:
            logger.warning("PullPush scrape failed for '%s': %s", target_brand, exc)
            return []

    # ------------------------------------------------------------------
    # Tier 3: RSS feed (no auth, original fallback)
    # ------------------------------------------------------------------

    def _build_rss_url(self) -> str:
        settings = get_settings()
        return f"{settings.scraper_reddit_base_url.rstrip('/')}/search.rss"

    def _fetch_rss_payload(self, target_brand: str) -> str:
        settings = get_settings()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
        }
        return RetryingHttpClient.get_text(
            self._build_rss_url(),
            params={"q": self._build_query(target_brand), "sort": "new",
                    "limit": settings.scraper_max_items_per_source},
            headers=headers,
        )

    def _parse_rss_feed(self, xml_text: str, target_brand: str) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns) or root.findall(".//entry")
        settings = get_settings()
        items: list[ScrapedItem] = []

        for entry in entries[:settings.scraper_max_items_per_source]:
            title_el = entry.find("atom:title", ns) or entry.find("title")
            title = (title_el.text or "").strip() if title_el is not None else ""
            content_el = (entry.find("atom:content", ns) or entry.find("atom:summary", ns)
                          or entry.find("content") or entry.find("summary"))
            content_html = (content_el.text or "") if content_el is not None else ""
            content_text = normalize_whitespace(re.sub(r'<[^>]+>', ' ', content_html).strip())
            combined = "\n\n".join(p for p in [title, content_text] if p).strip()
            if not combined:
                continue

            link_el = entry.find("atom:link", ns) or entry.find("link")
            source_url = (link_el.get("href") or link_el.text) if link_el is not None else None
            external_id = None
            if source_url:
                parts = [p for p in source_url.rstrip("/").split("/") if p]
                external_id = parts[-1] if parts else None
            author_el = entry.find("atom:author/atom:name", ns) or entry.find("author/name")
            author = (author_el.text or "").strip() if author_el is not None else None
            updated_el = entry.find("atom:updated", ns) or entry.find("updated")
            published_at = None
            if updated_el is not None and updated_el.text:
                try:
                    published_at = datetime.fromisoformat(updated_el.text.replace("Z", "+00:00"))
                except ValueError:
                    pass
            category_el = entry.find("atom:category", ns) or entry.find("category")
            subreddit = category_el.get("term", "") if category_el is not None else ""

            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="post",
                external_id=external_id,
                author_name=author,
                source_url=source_url,
                published_at=published_at,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version="reddit-rss-v1",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=external_id,
                    source_url=source_url,
                    raw_text=combined,
                ),
                raw_payload_json=build_payload_snapshot(
                    {"title": title, "content": content_text, "author": author,
                     "source_url": source_url, "subreddit": subreddit}
                ),
                raw_text=combined,
                cleaned_text=combined,
                language="en",
                metadata_json={"subreddit": subreddit, "fetch_mode": "rss"},
            ))

        return items

    # ------------------------------------------------------------------
    # Tier 3: Stub data
    # ------------------------------------------------------------------

    def _build_stub_items(self, target_brand: str, fallback_reason: str | None = None) -> list[ScrapedItem]:
        fetched_at = datetime.now(timezone.utc)
        source_query = self._build_query(target_brand)

        stubs = [
            (f"reddit-stub-001", "post", "reddit_user_1",
             f"{target_brand} has too many stale listings and delayed callbacks. Enquired about 3 properties and all turned out to be already sold.",
             "indianrealestate"),
            (f"reddit-stub-002", "comment", "reddit_user_2",
             f"I enquired on {target_brand} but the agent never responded. Waited 5 days, complete waste of time.",
             "realestateindia"),
            (f"reddit-stub-003", "post", "reddit_user_3",
             f"{target_brand} app is super slow on my phone, takes 10 seconds to load listings. Very frustrating when you want to browse quickly.",
             "mumbai"),
            (f"reddit-stub-004", "comment", "reddit_user_4",
             f"Beware of fraud listings on {target_brand}. I was scammed for token money. No verification process.",
             "indianrealestate"),
            (f"reddit-stub-005", "post", "reddit_user_5",
             f"Prices on {target_brand} are not transparent. Hidden charges added at the end of booking.",
             "delhi"),
        ]

        items = []
        for ext_id, ctype, author, text, subreddit in stubs:
            url = f"https://reddit.com/r/{subreddit}/stub/{ext_id}"
            items.append(ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type=ctype,
                external_id=f"{target_brand.lower().replace(' ', '-')}-{ext_id}",
                author_name=author,
                source_url=url,
                fetched_at=fetched_at,
                source_query=source_query,
                parser_version="reddit-rss-v1-stub",
                dedupe_key=build_dedupe_key(
                    source_name=self.source_name,
                    external_id=f"{target_brand.lower().replace(' ', '-')}-{ext_id}",
                    source_url=url,
                    raw_text=text,
                ),
                raw_payload_json={"stub": True, "reason": fallback_reason},
                raw_text=text,
                cleaned_text=text,
                language="en",
                metadata_json={
                    "subreddit": subreddit,
                    "fetch_mode": "stub",
                    "fallback_reason": fallback_reason,
                },
            ))
        return items

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        settings = get_settings()

        if not settings.scraper_enable_live_fetch:
            logger.info("Reddit: live fetch disabled, using stub data")
            return self._build_stub_items(target_brand, "Live fetch disabled in settings")

        # Tier 1: PRAW (official API) — only if credentials configured
        if settings.reddit_api_enabled:
            items = self._scrape_via_praw(target_brand)
            if items:
                return items
            logger.warning("Reddit PRAW returned 0 items, trying PullPush fallback")

        # Tier 2: PullPush.io (Pushshift-compatible, no auth required)
        items = self._scrape_via_pullpush(target_brand)
        if items:
            return items
        logger.warning("Reddit PullPush returned 0 items, trying RSS fallback")

        # Tier 3: Reddit RSS feed
        try:
            xml_text = self._fetch_rss_payload(target_brand)
            items = self._parse_rss_feed(xml_text, target_brand)
            if items:
                logger.info("Reddit RSS: fetched %d items for '%s'", len(items), target_brand)
                return items
            logger.warning("Reddit RSS returned 0 parsable items")
        except Exception as exc:
            logger.warning("Reddit RSS failed: %s", exc)

        # Tier 4: Stub (only when explicitly enabled)
        if settings.scraper_fail_open_to_stub:
            logger.info("Reddit: falling back to stub data")
            return self._build_stub_items(target_brand, "All live tiers failed")

        logger.warning("Reddit: all live tiers failed for '%s', no stub fallback enabled", target_brand)
        return []
