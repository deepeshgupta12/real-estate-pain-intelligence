from app.core.config import get_settings
from app.scrapers.sources.youtube import YouTubeScraper


def test_youtube_scraper_live_payload_parsing(monkeypatch) -> None:
    settings = get_settings()
    original_live_fetch = settings.scraper_enable_live_fetch

    settings.scraper_enable_live_fetch = True

    search_html = """
    <html>
      <body>
        "videoId":"abcDEF12345"
      </body>
    </html>
    """

    watch_html = """
    <html>
      <head><title>Square Yards Review - YouTube</title></head>
      <body>
        "authorText":{"simpleText":"viewer_one"},"contentText":{"runs":[{"text":"Inventory"},{"text":" is outdated"}]}
      </body>
    </html>
    """

    def _mock_fetch_search_html(self, target_brand: str) -> str:
        assert target_brand == "Square Yards"
        return search_html

    def _mock_fetch_watch_html(self, video_id: str) -> str:
        assert video_id == "abcDEF12345"
        return watch_html

    monkeypatch.setattr(YouTubeScraper, "_fetch_search_html", _mock_fetch_search_html)
    monkeypatch.setattr(YouTubeScraper, "_fetch_watch_html", _mock_fetch_watch_html)

    try:
        items = YouTubeScraper().scrape("Square Yards")
    finally:
        settings.scraper_enable_live_fetch = original_live_fetch

    assert len(items) == 1
    item = items[0]
    assert item.external_id == "abcDEF12345:1"
    assert item.author_name == "viewer_one"
    assert item.source_query is not None
    assert item.fetched_at is not None
    assert item.parser_version == "youtube-v2-live-1"
    assert item.dedupe_key is not None
    assert item.raw_payload_json["video_id"] == "abcDEF12345"
    assert item.metadata_json["fetch_mode"] == "live"