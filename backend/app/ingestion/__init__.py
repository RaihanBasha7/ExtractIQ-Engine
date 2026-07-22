"""
Document ingestion orchestration.

Detects file type by extension and dispatches to the appropriate parser.
After parsing, runs intelligent document segmentation to detect individual tickets.
"""

from dataclasses import dataclass, field

from app.logging import get_logger

logger = get_logger(__name__)


_SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": "PDF",
    ".txt": "TXT",
    ".docx": "DOCX",
    ".csv": "CSV",
    ".json": "JSON",
}


@dataclass
class SegmentInfo:
    text: str
    index: int
    word_count: int = 0
    char_count: int = 0
    boundary_type: str = "auto"
    valid: bool = True
    validation_message: str | None = None


@dataclass
class IngestionResult:
    text: str
    file_type: str
    file_name: str
    file_size_bytes: int
    pages: int | None = None
    tickets_detected: int | None = None
    warnings: list[str] = field(default_factory=list)
    segments: list[SegmentInfo] = field(default_factory=list)
    segmentation_method: str | None = None


def detect_file_type(filename: str) -> str | None:
    ext = _get_ext(filename)
    return _SUPPORTED_EXTENSIONS.get(ext)


def _get_ext(filename: str) -> str:
    _, ext = _split_ext(filename)
    return ext


def _split_ext(filename: str) -> tuple[str, str]:
    idx = filename.rfind(".")
    if idx == -1 or idx == 0:
        return filename, ""
    return filename[:idx], filename[idx:].lower()


def ingest_file(file_path: str, file_name: str, file_size_bytes: int, **kwargs) -> IngestionResult:
    ext = _get_ext(file_name)
    file_type = _SUPPORTED_EXTENSIONS.get(ext)

    if file_type == "PDF":
        from app.ingestion.pdf_parser import parse_pdf

        result = parse_pdf(file_path, file_name, file_size_bytes, **kwargs)
    elif file_type == "DOCX":
        from app.ingestion.docx_parser import parse_docx

        result = parse_docx(file_path, file_name, file_size_bytes, **kwargs)
    elif file_type == "TXT":
        from app.ingestion.txt_parser import parse_txt

        result = parse_txt(file_path, file_name, file_size_bytes, **kwargs)
    elif file_type == "CSV":
        from app.ingestion.csv_parser import parse_csv

        result = parse_csv(file_path, file_name, file_size_bytes, **kwargs)
    elif file_type == "JSON":
        from app.ingestion.json_parser import parse_json

        result = parse_json(file_path, file_name, file_size_bytes, **kwargs)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Run intelligent segmentation on the extracted text
    if result.text.strip():
        try:
            from app.ingestion.segmenter import segment_document

            seg_result = segment_document(result.text, use_ai=True)
            result.segments = [
                SegmentInfo(
                    text=s.text,
                    index=s.index,
                    word_count=s.word_count,
                    char_count=s.char_count,
                    boundary_type=s.boundary_type,
                    valid=s.valid,
                    validation_message=s.validation_message,
                )
                for s in seg_result.segments
            ]
            result.segmentation_method = seg_result.method
            result.tickets_detected = len(seg_result.segments)
            for w in seg_result.warnings:
                if w not in result.warnings:
                    result.warnings.append(w)
        except Exception as exc:
            logger.warning("Document segmentation failed, falling back to line count: %s", exc)
            result.warnings.append(f"Segmentation engine error: {exc}")

    return result
