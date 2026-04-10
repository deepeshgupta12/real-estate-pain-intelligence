from app.scrapers.base import BaseSourceScraper
from app.scrapers.types import ScrapedItem


class RedditScraper(BaseSourceScraper):
    source_name = "reddit"

    def scrape(self, target_brand: str) -> list[ScrapedItem]:
        return [
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="post",
                external_id=f"reddit-{target_brand.lower().replace(' ', '-')}-001",
                author_name="reddit_user_1",
                source_url="https://reddit.com/example-thread-1",
                raw_text=f"{target_brand} has too many stale listings and delayed callbacks.",
                cleaned_text=f"{target_brand} has too many stale listings and delayed callbacks.",
                language="en",
                metadata_json={"subreddit": "indianrealestate"},
            ),
            ScrapedItem(
                source_name=self.source_name,
                platform_name=target_brand,
                content_type="comment",
                external_id=f"reddit-{target_brand.lower().replace(' ', '-')}-002",
                author_name="reddit_user_2",
                source_url="https://reddit.com/example-thread-2",
                raw_text=f"I enquired on {target_brand} but received irrelevant follow-up responses.",
                cleaned_text=f"I enquired on {target_brand} but received irrelevant follow-up responses.",
                language="en",
                metadata_json={"subreddit": "realestateindia"},
            ),
        ]