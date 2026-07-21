"""
JSON parser.

Supports:

- Array of objects with a text field
- Object with a text field or nested data

Auto-detects the text field by trying common keys.
"""

import json

from app.ingestion import IngestionResult
from app.logging import get_logger

logger = get_logger(__name__)


_TEXT_FIELD_HINTS = {"text", "ticket", "message", "description", "body", "content", "comment", "feedback", "input"}


def parse_json(file_path: str, file_name: str, file_size_bytes: int, **kwargs) -> IngestionResult:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON file", exc_info=exc, path=file_path)
        return IngestionResult(
            text="",
            file_type="JSON",
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            pages=0,
            tickets_detected=0,
            warnings=[f"Invalid JSON: {exc}"],
        )
    except Exception as exc:
        logger.error("Failed to read JSON file", exc_info=exc, path=file_path)
        return IngestionResult(
            text="",
            file_type="JSON",
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            pages=0,
            tickets_detected=0,
            warnings=[f"Failed to read file: {exc}"],
        )

    tickets = _extract_texts(data)
    merged = "\n".join(tickets)

    return IngestionResult(
        text=merged,
        file_type="JSON",
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        pages=1,
        tickets_detected=len(tickets),
    )


def _extract_texts(data) -> list[str]:
    if isinstance(data, list):
        texts: list[str] = []
        for item in data:
            if isinstance(item, dict):
                t = _extract_text_field(item)
                if t:
                    texts.append(t)
            elif isinstance(item, str):
                if item.strip():
                    texts.append(item.strip())
        return texts

    if isinstance(data, dict):
        # Single object — try text fields or nested data
        t = _extract_text_field(data)
        if not t:
            # Maybe it wraps an array
            for v in data.values():
                if isinstance(v, list):
                    return _extract_texts(v)
            return []
        return [t]

    if isinstance(data, str):
        return [data.strip()] if data.strip() else []

    return []


def _extract_text_field(obj: dict) -> str | None:
    # Try exact match on known field names
    for key in obj:
        if key.lower() in _TEXT_FIELD_HINTS:
            val = obj[key]
            if isinstance(val, str) and val.strip():
                return val.strip()
            if isinstance(val, (int, float)):
                return str(val)

    # Try any string field
    for key in obj:
        val = obj[key]
        if isinstance(val, str) and val.strip():
            return val.strip()

    return None
