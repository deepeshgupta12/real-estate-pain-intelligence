from abc import ABC, abstractmethod

from app.scrapers.types import ScrapedItem


class BaseSourceScraper(ABC):
    source_name: str
    parser_version: str = "v1"

    @abstractmethod
    def scrape(self, target_brand: str, context: str | None = None) -> list[ScrapedItem]:
        """Scrape evidence for *target_brand*.

        Args:
            target_brand: The brand name to search for (e.g. "Square Yards").
            context: Optional research context string parsed from session_notes.
                     Contains focus keywords that should be injected into search
                     queries to bias results toward the user's area of interest.
                     When None (or empty), broad scraping is performed without
                     topic filtering.

        Returns:
            List of ScrapedItem instances.
        """
        raise NotImplementedError
