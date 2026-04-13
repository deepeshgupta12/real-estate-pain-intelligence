import random
import time
from typing import Any

import httpx

from app.core.config import get_settings

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}


class RetryingHttpClient:
    _session: httpx.Client | None = None

    @staticmethod
    def _get_session() -> httpx.Client:
        if RetryingHttpClient._session is None:
            timeout = httpx.Timeout(get_settings().scraper_default_timeout_seconds)
            RetryingHttpClient._session = httpx.Client(
                timeout=timeout,
                follow_redirects=True,
            )
        return RetryingHttpClient._session

    @staticmethod
    def _request(
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        use_browser_headers: bool = True,
    ) -> httpx.Response:
        settings = get_settings()
        last_exception: Exception | None = None

        # Merge browser headers with custom headers
        merged_headers = BROWSER_HEADERS.copy() if use_browser_headers else {}
        if headers:
            merged_headers.update(headers)

        session = RetryingHttpClient._get_session()

        for attempt in range(settings.scraper_max_retries + 1):
            try:
                response = session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=merged_headers,
                )
                response.raise_for_status()
                return response
            except Exception as exc:
                last_exception = exc
                if attempt >= settings.scraper_max_retries:
                    break
                # Random jitter: random.uniform(1.5, 4.0) * (attempt + 1)
                sleep_seconds = random.uniform(1.5, 4.0) * (attempt + 1)
                time.sleep(sleep_seconds)

        raise RuntimeError(f"Failed to fetch resource from {url}") from last_exception

    @staticmethod
    def get_json(
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        use_browser_headers: bool = True,
    ) -> dict[str, Any]:
        # For JSON requests, override Accept to application/json
        json_headers = headers or {}
        json_headers = {**json_headers}
        json_headers["Accept"] = "application/json, text/plain, */*"

        response = RetryingHttpClient._request(
            "GET",
            url,
            params=params,
            headers=json_headers,
            use_browser_headers=use_browser_headers,
        )
        return response.json()

    @staticmethod
    def get_text(
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        use_browser_headers: bool = True,
    ) -> str:
        response = RetryingHttpClient._request(
            "GET",
            url,
            params=params,
            headers=headers,
            use_browser_headers=use_browser_headers,
        )
        return response.text