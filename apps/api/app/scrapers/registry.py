from app.scrapers.base import BaseSourceScraper
from app.scrapers.sources import (
    AppReviewsScraper,
    RedditScraper,
    ReviewSitesScraper,
    XPostsScraper,
    YouTubeScraper,
)


class ScraperRegistry:
    _registry: dict[str, type[BaseSourceScraper]] = {
        RedditScraper.source_name: RedditScraper,
        YouTubeScraper.source_name: YouTubeScraper,
        AppReviewsScraper.source_name: AppReviewsScraper,
        XPostsScraper.source_name: XPostsScraper,
        ReviewSitesScraper.source_name: ReviewSitesScraper,
    }

    @classmethod
    def get_scraper(cls, source_name: str) -> BaseSourceScraper:
        if source_name not in cls._registry:
            raise ValueError(f"No scraper registered for source '{source_name}'")
        return cls._registry[source_name]()

    @classmethod
    def list_supported_sources(cls) -> list[str]:
        return sorted(cls._registry.keys())