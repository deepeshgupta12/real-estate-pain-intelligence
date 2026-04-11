from app.core.config import get_settings
from app.scrapers.sources.x_posts import XPostsScraper


def test_x_scraper_live_payload_parsing(monkeypatch) -> None:
    settings = get_settings()
    original_live_fetch = settings.scraper_enable_live_fetch

    settings.scraper_enable_live_fetch = True

    sample_payload = {
        "hits": [
            {
                "objectID": "hn-1",
                "title": "Square Yards complaint thread",
                "story_text": "Users mention duplicate listings and bad lead quality.",
                "author": "hn_user",
                "url": "https://news.ycombinator.com/item?id=1",
                "points": 15,
                "num_comments": 6,
                "created_at": "2026-04-11T09:00:00Z",
            }
        ]
    }

    def _mock_fetch_live_payload(self, target_brand: str) -> dict:
        assert target_brand == "Square Yards"
        return sample_payload

    monkeypatch.setattr(XPostsScraper, "_fetch_live_payload", _mock_fetch_live_payload)

    try:
        items = XPostsScraper().scrape("Square Yards")
    finally:
        settings.scraper_enable_live_fetch = original_live_fetch

    assert len(items) == 1
    item = items[0]
    assert item.external_id == "hn-1"
    assert item.author_name == "hn_user"
    assert item.source_query is not None
    assert item.fetched_at is not None
    assert item.parser_version == "x-alt-v2-live-1"
    assert item.dedupe_key is not None
    assert item.raw_payload_json["objectID"] == "hn-1"
    assert item.metadata_json["fetch_mode"] == "live"
    assert item.metadata_json["network"] == "hn_algolia_fallback"