from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ScrapedItem(BaseModel):
    source_name: str = Field(..., min_length=1, max_length=100)
    platform_name: str = Field(..., min_length=1, max_length=100)
    content_type: str = Field(..., min_length=1, max_length=50)
    external_id: str | None = None
    author_name: str | None = None
    source_url: str | None = None
    published_at: datetime | None = None
    raw_text: str = Field(..., min_length=1)
    cleaned_text: str | None = None
    language: str | None = None
    is_relevant: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)