"""
CSV parser.

Treats every row as an independent ticket. Allows selecting which column
contains ticket text. Defaults to the first text-like column.
"""

import csv
import io

from app.ingestion import IngestionResult
from app.logging import get_logger

logger = get_logger(__name__)


_TEXT_COLUMN_HINTS = {"text", "ticket", "message", "description", "body", "content", "comment", "feedback"}


def parse_csv(file_path: str, file_name: str, file_size_bytes: int, **kwargs) -> IngestionResult:
    text_column: str | None = kwargs.get("text_column")

    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            raw = f.read()
    except Exception as exc:
        logger.error("Failed to read CSV file %s: %s", file_path, exc)
        return IngestionResult(
            text="",
            file_type="CSV",
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            pages=0,
            tickets_detected=0,
            warnings=[f"Failed to read file: {exc}"],
        )

    try:
        reader = csv.DictReader(io.StringIO(raw))
        if not reader.fieldnames:
            raise ValueError("No columns found in CSV")
    except Exception as exc:
        logger.error("Failed to parse CSV %s: %s", file_path, exc)
        return IngestionResult(
            text="",
            file_type="CSV",
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            pages=0,
            tickets_detected=0,
            warnings=[f"Failed to parse CSV: {exc}"],
        )

    column = text_column or _detect_text_column(reader.fieldnames)
    if column not in reader.fieldnames:
        warnings = [f"Text column '{column}' not found. Available: {', '.join(reader.fieldnames)}"]
        return IngestionResult(
            text="",
            file_type="CSV",
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            pages=0,
            tickets_detected=0,
            warnings=warnings,
        )

    tickets: list[str] = []
    for row in reader:
        val = row.get(column, "")
        if val.strip():
            tickets.append(val.strip())

    merged = "\n".join(tickets)

    return IngestionResult(
        text=merged,
        file_type="CSV",
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        pages=1,
        tickets_detected=len(tickets),
    )


def _detect_text_column(fieldnames: list[str]) -> str:
    for hint in _TEXT_COLUMN_HINTS:
        for original, lower in zip(fieldnames, [c.lower() for c in fieldnames]):
            if lower == hint:
                return original

    # Fallback: return the first string-like column
    for col in fieldnames:
        lower = col.lower()
        if lower not in ("id", "ticket_id", "timestamp", "date", "category", "label"):
            return col

    return fieldnames[0]
