from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = BASE_DIR / ".env"


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

    notion_enable_real_sync: bool = False
    notion_api_base_url: str = "https://api.notion.com/v1"
    notion_api_version: str = "2022-06-28"
    notion_api_key: str | None = None
    notion_timeout_seconds: float = 15.0
    notion_max_retries: int = 2
    notion_retry_backoff_seconds: float = 1.0
    notion_destination_mode: Literal["database", "page"] = "database"
    notion_database_id: str | None = None
    notion_parent_page_id: str | None = None
    notion_destination_label: str = "notion_database"
    notion_title_property_name: str = "Name"
    notion_status_property_name: str = "Status"
    notion_priority_property_name: str = "Priority"
    notion_brand_property_name: str = "Brand"
    notion_source_property_name: str = "Source"
    notion_decision_property_name: str = "Decision"
    notion_default_title_prefix: str = "REPI"

    embedding_provider: Literal["deterministic_hash"] = "deterministic_hash"
    embedding_model_name: str = "hash-embedding-v1"
    embedding_dimensions: int = 128
    retrieval_vector_distance: Literal["cosine"] = "cosine"
    retrieval_search_default_top_k: int = 5

    intelligence_mode: Literal["deterministic", "hybrid_llm"] = "deterministic"
    intelligence_enable_llm: bool = False
    intelligence_llm_provider: Literal["openai"] = "openai"
    intelligence_openai_model: str = "gpt-4o"
    intelligence_llm_timeout_seconds: float = 30.0
    intelligence_llm_max_retries: int = 2
    openai_api_key: str | None = None

    api_key_enabled: bool = False
    api_key_secret: str | None = None

    scraper_reddit_rss_enabled: bool = True

    observability_stale_run_seconds: int = 300
    observability_recent_failure_window_minutes: int = 60
    observability_recent_events_window_minutes: int = 60

    # Redis / ARQ
    redis_url: str = "redis://localhost:6379/0"
    arq_max_jobs: int = 10
    arq_job_timeout: int = 300  # seconds

    # JWT Auth
    jwt_secret_key: str = "change-me-in-production-use-256-bit-random-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # Database connection pooling
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
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