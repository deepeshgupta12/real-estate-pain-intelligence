from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Real Estate Pain Point Intelligence API"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    api_v1_prefix: str = "/api/v1"
    app_version: str = "0.2.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5460/repi_db"

    scraper_enable_live_fetch: bool = False
    scraper_fail_open_to_stub: bool = True
    scraper_default_timeout_seconds: float = 10.0
    scraper_max_retries: int = 2
    scraper_retry_backoff_seconds: float = 1.0
    scraper_max_items_per_source: int = 10
    scraper_user_agent: str = "repi-bot/0.2 (+https://localhost)"

    scraper_reddit_base_url: str = "https://www.reddit.com"
    scraper_youtube_search_base_url: str = "https://www.youtube.com/results"
    scraper_youtube_watch_base_url: str = "https://www.youtube.com/watch"
    scraper_itunes_search_base_url: str = "https://itunes.apple.com/search"
    scraper_apple_reviews_base_url: str = "https://itunes.apple.com/rss/customerreviews"
    scraper_public_social_search_base_url: str = "https://hn.algolia.com/api/v1/search"
    scraper_review_sites_base_url: str = "https://www.trustpilot.com/review"

    export_output_dir: str = "./generated_exports"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()