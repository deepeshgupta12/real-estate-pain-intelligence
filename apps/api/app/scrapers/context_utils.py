"""
Shared utilities for context-aware scraping.

session_notes stores user research context in the format:
    "[CONTEXT: Website & Mobile App, Complaints & Escalations] custom note here"

This module parses that string and maps prebuilt context labels to their
associated search keywords so scrapers can augment queries.
"""
import re

# Maps prebuilt context chip labels → search keywords.
# Kept in sync with PREBUILT_CONTEXTS in run-setup-panel.tsx.
CONTEXT_KEYWORD_MAP: dict[str, list[str]] = {
    "Website & Mobile App": ["website", "mobile app", "app crash", "login", "loading", "bug"],
    "Listings": ["listing", "property listing", "fake listing", "wrong price", "photos"],
    "Projects & Builders": ["project", "builder", "construction", "delivery", "possession", "quality"],
    "Sales Process & Agents": ["agent", "broker", "sales", "commission", "response time", "pushy"],
    "Post-Sales Process": ["possession", "registry", "loan", "handover", "documentation", "NOC"],
    "Complaints & Escalations": ["complaint", "refund", "cheated", "fraud", "legal", "scam"],
}


def extract_context_keywords(session_notes: str | None) -> list[str]:
    """
    Parse session_notes and return a flat, deduplicated list of search keywords.

    Handles two sources of keywords:
    1. Prebuilt context chips: "[CONTEXT: Website & Mobile App, Listings]"
       → looked up in CONTEXT_KEYWORD_MAP.
    2. Free-form custom text after the [CONTEXT: ...] tag is split on
       spaces/commas and the longest tokens are appended.

    Returns an empty list when session_notes is None or contains no context.
    """
    if not session_notes:
        return []

    keywords: list[str] = []
    seen: set[str] = set()

    def add(kw: str) -> None:
        k = kw.strip().lower()
        if k and k not in seen:
            seen.add(k)
            keywords.append(kw.strip())

    # --- Extract prebuilt chip labels ---
    chip_match = re.match(r"^\[CONTEXT:\s*([^\]]+)\]", session_notes)
    if chip_match:
        chip_labels = [lbl.strip() for lbl in chip_match.group(1).split(",")]
        for label in chip_labels:
            for kw in CONTEXT_KEYWORD_MAP.get(label, []):
                add(kw)

    # --- Extract meaningful tokens from the free-form tail ---
    # Strip the [CONTEXT:...] prefix if present, then tokenise the rest
    tail = re.sub(r"^\[CONTEXT:[^\]]+\]\s*", "", session_notes).strip()
    if tail:
        # Split on whitespace/punctuation, keep tokens ≥ 4 chars (skip stop words)
        tokens = re.split(r"[\s,;.]+", tail)
        stopwords = {"the", "and", "for", "with", "from", "that", "this", "have",
                     "focus", "about", "will", "should", "context"}
        for tok in tokens:
            tok = tok.strip("\"'()[]")
            if len(tok) >= 4 and tok.lower() not in stopwords:
                add(tok)

    return keywords
