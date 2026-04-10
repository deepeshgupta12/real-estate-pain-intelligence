from abc import ABC, abstractmethod

from app.scrapers.types import ScrapedItem


class BaseSourceScraper(ABC):
    source_name: str

    @abstractmethod
    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        raise NotImplementedError