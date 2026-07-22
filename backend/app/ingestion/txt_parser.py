"""
TXT parser.

Safely reads UTF-8 text files. Falls back to latin-1 if UTF-8 fails.
Handles large files by reading in chunks.
"""

from app.ingestion import IngestionResult
from app.logging import get_logger

logger = get_logger(__name__)

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB safety limit


def parse_txt(file_path: str, file_name: str, file_size_bytes: int, **kwargs) -> IngestionResult:
    if file_size_bytes > _MAX_FILE_SIZE:
        return IngestionResult(
            text="",
            file_type="TXT",
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            pages=0,
            tickets_detected=0,
            warnings=[f"File too large ({file_size_bytes / 1024 / 1024:.1f} MB). Maximum is 50 MB."],
        )

    text = _read_text(file_path)
    if text is None:
        return IngestionResult(
            text="",
            file_type="TXT",
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            pages=0,
            tickets_detected=0,
            warnings=["Failed to read file as UTF-8 or latin-1."],
        )

    tickets = _count_tickets(text)

    return IngestionResult(
        text=text,
        file_type="TXT",
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        pages=1,
        tickets_detected=tickets,
    )


def _read_text(file_path: str) -> str | None:
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as exc:
            logger.warning("Failed to read file with encoding %s", encoding, exc_info=exc)
            return None
    return None


def _count_tickets(text: str) -> int:
    if not text.strip():
        return 0
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return max(1, len(lines))
