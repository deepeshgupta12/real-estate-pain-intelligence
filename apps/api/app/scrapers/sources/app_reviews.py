from app.scrapers.base import BaseSourceScraper
from app.scrapers.types import ScrapedItem


class AppReviewsScraper(BaseSourceScraper):
    source_name = "app_reviews"

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        return [
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="review",
                external_id=f"app-review-{target_brand.lower().replace(' ', '-')}-001",
                author_name="app_user_1",
                source_url=None,
                raw_text=f"The {target_brand} app feels slow and the leads shown do not match intent.",
                cleaned_text=f"The {target_brand} app feels slow and the leads shown do not match intent.",
                language="en",
                metadata_json={"store": "google_play"},
            )
        ]