from app.scrapers.base import BaseSourceScraper
from app.scrapers.types import ScrapedItem


class ReviewSitesScraper(BaseSourceScraper):
    source_name = "review_sites"

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        return [
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="review",
                external_id=f"review-{target_brand.lower().replace(' ', '-')}-001",
                author_name="review_user_1",
                source_url="https://example-review-site.com/review/1",
                raw_text=f"Review-site feedback suggests {target_brand} has poor response quality after enquiry.",
                cleaned_text=f"Review-site feedback suggests {target_brand} has poor response quality after enquiry.",
                language="en",
                metadata_json={"site": "example-review-site"},
            )
        ]