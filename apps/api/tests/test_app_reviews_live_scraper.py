from app.core.config import get_settings
from app.scrapers.sources.app_reviews import AppReviewsScraper


def test_app_reviews_scraper_live_payload_parsing(monkeypatch) -> None:
    settings = get_settings()
    original_live_fetch = settings.scraper_enable_live_fetch

    settings.scraper_enable_live_fetch = True

    lookup_payload = {
        "results": [
            {
                "trackId": 123456,
                "trackName": "Square Yards",
                "trackViewUrl": "https://apps.apple.com/app/id123456",
            }
        ]
    }

    reviews_payload = {
        "feed": {
            "entry": [
                {
                    "id": {"label": "review-1"},
                    "author": {"name": {"label": "reviewer_one"}},
                    "title": {"label": "Very slow"},
                    "content": {"label": "App is slow and listings feel outdated."},
                    "im:rating": {"label": "2"},
                    "updated": {"label": "2026-04-11T10:00:00Z"},
                    "link": {"attributes": {"href": "https://apps.apple.com/review/1"}},
                }
            ]
        }
    }

    def _mock_fetch_app_lookup_payload(self, target_brand: str) -> dict:
        assert target_brand == "Square Yards"
        return lookup_payload

    def _mock_fetch_reviews_payload(self, app_id: int) -> dict:
        assert app_id == 123456
        return reviews_payload

    monkeypatch.setattr(AppReviewsScraper, "_fetch_app_lookup_payload", _mock_fetch_app_lookup_payload)
    monkeypatch.setattr(AppReviewsScraper, "_fetch_reviews_payload", _mock_fetch_reviews_payload)

    try:
        items = AppReviewsScraper().scrape("Square Yards")
    finally:
        settings.scraper_enable_live_fetch = original_live_fetch

    assert len(items) == 1
    item = items[0]
    assert item.external_id == "review-1"
    assert item.author_name == "reviewer_one"
    assert item.source_query is not None
    assert item.fetched_at is not None
    assert item.parser_version == "app-reviews-v2-live-1"
    assert item.dedupe_key is not None
    assert item.raw_payload_json["review_id"] == "review-1"
    assert item.metadata_json["fetch_mode"] == "live"
    assert item.metadata_json["store"] == "apple_app_store"