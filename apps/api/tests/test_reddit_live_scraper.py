from app.core.config import get_settings
from app.scrapers.sources.reddit import RedditScraper


def test_reddit_scraper_live_payload_parsing(monkeypatch) -> None:
    settings = get_settings()
    original_live_fetch = settings.scraper_enable_live_fetch

    settings.scraper_enable_live_fetch = True

    sample_payload = {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "abc123",
                        "author": "reddit_live_user",
                        "subreddit": "indianrealestate",
                        "title": "Square Yards listing quality issue",
                        "selftext": "Users are seeing stale inventory and duplicate property cards.",
                        "permalink": "/r/indianrealestate/comments/abc123/example/",
                        "score": 12,
                        "num_comments": 4,
                        "created_utc": 1712800000,
                    }
                }
            ]
        }
    }

    def _mock_fetch_live_payload(self, target_brand: str) -> dict:
        assert target_brand == "Square Yards"
        return sample_payload

    monkeypatch.setattr(RedditScraper, "_fetch_live_payload", _mock_fetch_live_payload)

    try:
        items = RedditScraper().scrape("Square Yards")
    finally:
        settings.scraper_enable_live_fetch = original_live_fetch

    assert len(items) == 1
    item = items[0]
    assert item.external_id == "abc123"
    assert item.source_query is not None
    assert item.fetched_at is not None
    assert item.parser_version == "reddit-v2-live-1"
    assert item.dedupe_key is not None
    assert item.raw_payload_json["id"] == "abc123"
    assert item.metadata_json["fetch_mode"] == "live"