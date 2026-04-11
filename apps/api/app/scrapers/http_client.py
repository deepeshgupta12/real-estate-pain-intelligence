import time
from typing import Any

import httpx

from app.core.config import get_settings


class RetryingHttpClient:
    @staticmethod
    def _request(
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        settings = get_settings()
        last_exception: Exception | None = None

        for attempt in range(settings.scraper_max_retries + 1):
            try:
                timeout = httpx.Timeout(settings.scraper_default_timeout_seconds)
                with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                    response = client.request(
                        method=method,
                        url=url,
                        params=params,
                        headers=headers,
                    )
                    response.raise_for_status()
                    return response
            except Exception as exc:
                last_exception = exc
                if attempt >= settings.scraper_max_retries:
                    break
                sleep_seconds = settings.scraper_retry_backoff_seconds * (attempt + 1)
                time.sleep(sleep_seconds)

        raise RuntimeError(f"Failed to fetch resource from {url}") from last_exception

    @staticmethod
    def get_json(
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        response = RetryingHttpClient._request(
            "GET",
            url,
            params=params,
            headers=headers,
        )
        return response.json()

    @staticmethod
    def get_text(
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        response = RetryingHttpClient._request(
            "GET",
            url,
            params=params,
            headers=headers,
        )
        return response.text