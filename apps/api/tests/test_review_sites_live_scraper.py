from app.core.config import get_settings
from app.scrapers.sources.review_sites import ReviewSitesScraper


def test_review_sites_scraper_live_payload_parsing(monkeypatch) -> None:
    settings = get_settings()
    original_live_fetch = settings.scraper_enable_live_fetch

    settings.scraper_enable_live_fetch = True

    html_payload = """
    <html>
      <body>
        <article class="review-card">
          <p data-service-review-text-typography="true">
            Poor callback quality and stale inventory on the platform.
          </p>
        </article>
      </body>
    </html>
    """

    def _mock_fetch_reviews_html(self, target_brand: str) -> str:
        assert target_brand == "Square Yards"
        return html_payload

    monkeypatch.setattr(ReviewSitesScraper, "_fetch_reviews_html", _mock_fetch_reviews_html)

    try:
        items = ReviewSitesScraper().scrape("Square Yards")
    finally:
        settings.scraper_enable_live_fetch = original_live_fetch

    assert len(items) == 1
    item = items[0]
    assert item.external_id == "square-yards-review-1"
    assert item.source_query is not None
    assert item.fetched_at is not None
    assert item.parser_version == "review-sites-v2-live-1"
    assert item.dedupe_key is not None
    assert item.raw_payload_json["review_index"] == 1
    assert item.metadata_json["fetch_mode"] == "live"
    assert item.metadata_json["site"] == "trustpilot"