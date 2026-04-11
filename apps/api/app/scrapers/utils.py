import hashlib
import json
import re
from html import unescape
from typing import Any


def normalize_whitespace(text: str) -> str:
    normalized = text.replace("\n", " ").replace("\r", " ").strip()
    return re.sub(r"\s+", " ", normalized)


def strip_html_tags(text: str) -> str:
    text_without_tags = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(unescape(text_without_tags))


def slugify_identifier(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def build_dedupe_key(
    source_name: str,
    external_id: str | None,
    source_url: str | None,
    raw_text: str,
) -> str:
    if external_id:
        base = f"{source_name}:{external_id}"
    elif source_url:
        base = f"{source_name}:{source_url}"
    else:
        base = f"{source_name}:{normalize_whitespace(raw_text)}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def build_payload_snapshot(payload: dict[str, Any], max_chars: int = 12000) -> dict[str, Any]:
    try:
        serialized = json.dumps(payload, ensure_ascii=False)
    except TypeError:
        serialized = json.dumps({"unserializable_payload": True}, ensure_ascii=False)

    if len(serialized) <= max_chars:
        return payload

    truncated = serialized[:max_chars]
    return {
        "snapshot_truncated": True,
        "snapshot_text": truncated,
    }