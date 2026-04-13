import logging
import random
import time
from typing import Any

import httpx

from app.scrapers.circuit_breaker import CircuitBreaker, classify_http_error
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
        circuit_breaker_name: str | None = None,
    ) -> httpx.Response:
        settings = get_settings()
        last_exception: Exception | None = None

        circuit_breaker = None
        if circuit_breaker_name:
            circuit_breaker = CircuitBreaker.get(circuit_breaker_name)
            if not circuit_breaker.is_allowed():
                raise RuntimeError(
                    f"Circuit breaker [{circuit_breaker_name}] is OPEN — request blocked"
                )

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
                if circuit_breaker:
                    circuit_breaker.record_success()
                return response
            except Exception as exc:
                last_exception = exc
                if circuit_breaker:
                    if isinstance(exc, httpx.HTTPStatusError):
                        error_type = classify_http_error(exc.response.status_code)
                        circuit_breaker.record_failure(error_type)
                    else:
                        circuit_breaker.record_failure("REQUEST_ERROR")
                if attempt >= settings.scraper_max_retries:
                    break
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
        circuit_breaker_name: str | None = None,
    ) -> dict[str, Any]:
        json_headers = headers or {}
        json_headers = {**json_headers}
        json_headers["Accept"] = "application/json, text/plain, */*"

        response = RetryingHttpClient._request(
            "GET",
            url,
            params=params,
            headers=json_headers,
            use_browser_headers=use_browser_headers,
            circuit_breaker_name=circuit_breaker_name,
        )
        return response.json()

    @staticmethod
    def get_text(
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        use_browser_headers: bool = True,
        circuit_breaker_name: str | None = None,
    ) -> str:
        response = RetryingHttpClient._request(
            "GET",
            url,
            params=params,
            headers=headers,
            use_browser_headers=use_browser_headers,
            circuit_breaker_name=circuit_breaker_name,
        )
        return response.text