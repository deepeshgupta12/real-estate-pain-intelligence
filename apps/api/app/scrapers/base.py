from abc import ABC, abstractmethod

from app.scrapers.types import ScrapedItem


class BaseSourceScraper(ABC):
    source_name: str
    parser_version: str = "v1"

    @abstractmethod
    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        raise NotImplementedError