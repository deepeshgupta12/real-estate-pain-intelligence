from app.scrapers.base import BaseSourceScraper
from app.scrapers.types import ScrapedItem


class YouTubeScraper(BaseSourceScraper):
    source_name = "youtube"

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        return [
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="comment",
                external_id=f"youtube-{target_brand.lower().replace(' ', '-')}-001",
                author_name="yt_viewer_1",
                source_url="https://youtube.com/watch?v=example1",
                raw_text=f"The {target_brand} project walkthrough looked good, but users in comments complained about outdated inventory.",
                cleaned_text=f"The {target_brand} project walkthrough looked good, but users in comments complained about outdated inventory.",
                language="en",
                metadata_json={"video_id": "example1"},
            )
        ]