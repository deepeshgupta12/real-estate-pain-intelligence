import time
from typing import Any

import httpx

from app.core.config import get_settings


class NotionClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        if not self.settings.notion_api_key:
            raise RuntimeError("NOTION_API_KEY is required for real Notion sync")

        return {
            "Authorization": f"Bearer {self.settings.notion_api_key}",
            "Notion-Version": self.settings.notion_api_version,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_exception: Exception | None = None
        url = f"{self.settings.notion_api_base_url.rstrip('/')}/{path.lstrip('/')}"

        for attempt in range(self.settings.notion_max_retries + 1):
            try:
                timeout = httpx.Timeout(self.settings.notion_timeout_seconds)
                with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                    response = client.request(
                        method=method,
                        url=url,
                        headers=self._headers(),
                        json=payload,
                    )

                    if response.is_error:
                        response_text: str
                        try:
                            response_text = response.text
                        except Exception:
                            response_text = "<unable to read response body>"

                        raise RuntimeError(
                            f"Failed Notion request for path {path}: "
                            f"status={response.status_code}, body={response_text}"
                        )

                    return response.json()

            except Exception as exc:
                last_exception = exc
                if attempt >= self.settings.notion_max_retries:
                    break
                sleep_seconds = self.settings.notion_retry_backoff_seconds * (attempt + 1)
                time.sleep(sleep_seconds)

        if last_exception is not None:
            raise RuntimeError(str(last_exception)) from last_exception

        raise RuntimeError(f"Failed Notion request for path {path}")

    def create_database_page(
        self,
        *,
        database_id: str,
        properties: dict[str, Any],
        children: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties,
            "children": children,
        }
        return self._request("POST", "/pages", payload)

    def create_child_page(
        self,
        *,
        parent_page_id: str,
        title: str,
        children: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": title,
                        },
                    }
                ]
            },
            "children": children,
        }
        return self._request("POST", "/pages", payload)