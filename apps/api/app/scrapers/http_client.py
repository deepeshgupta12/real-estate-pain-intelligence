import time
from typing import Any

import httpx

from app.core.config import get_settings


class RetryingHttpClient:
    @staticmethod
    def get_json(
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        last_exception: Exception | None = None

        for attempt in range(settings.scraper_max_retries + 1):
            try:
                timeout = httpx.Timeout(settings.scraper_default_timeout_seconds)
                with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                    response = client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except Exception as exc:
                last_exception = exc
                if attempt >= settings.scraper_max_retries:
                    break
                sleep_seconds = settings.scraper_retry_backoff_seconds * (attempt + 1)
                time.sleep(sleep_seconds)

        raise RuntimeError(f"Failed to fetch JSON from {url}") from last_exception