from app.scrapers.base import BaseSourceScraper
from app.scrapers.types import ScrapedItem


class XPostsScraper(BaseSourceScraper):
    source_name = "x"

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        return [
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="post",
                external_id=f"x-{target_brand.lower().replace(' ', '-')}-001",
                author_name="x_user_1",
                source_url="https://x.com/example/status/1",
                raw_text=f"People are saying {target_brand} has too many duplicate property listings.",
                cleaned_text=f"People are saying {target_brand} has too many duplicate property listings.",
                language="en",
                metadata_json={"network": "x"},
            )
        ]