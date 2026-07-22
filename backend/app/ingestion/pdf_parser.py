"""
PDF parser with OCR fallback.

Supports multi-page PDFs, page-by-page extraction, blank page skipping,
and graceful degradation if a page fails.
"""

from dataclasses import dataclass
from typing import Any

from app.ingestion import IngestionResult
from app.logging import get_logger

logger = get_logger(__name__)


@dataclass
class _PageResult:
    page_num: int
    text: str
    success: bool
    error: str | None = None
    used_ocr: bool = False


@dataclass
class _PdfHandle:
    source: Any
    library: str  # "pdfplumber" or "fitz"

    @property
    def page_count(self) -> int:
        if self.library == "pdfplumber":
            return len(self.source.pages)
        return int(self.source.page_count)

    def get_page_text(self, idx: int) -> str:
        if self.library == "pdfplumber":
            page = self.source.pages[idx]
            return page.extract_text() or ""
        page = self.source[idx]
        return page.get_text() or ""

    def close(self):
        try:
            self.source.close()
        except Exception:
            pass


def parse_pdf(file_path: str, file_name: str, file_size_bytes: int, **kwargs) -> IngestionResult:
    pages: list[_PageResult] = []
    warnings: list[str] = []

    handle = _try_open_pdf(file_path)

    if handle is None:
        text, ocr_used, ocr_warnings = _ocr_fallback(file_path)
        if text is None:
            warnings.extend(ocr_warnings)
            return IngestionResult(
                text="",
                file_type="PDF",
                file_name=file_name,
                file_size_bytes=file_size_bytes,
                pages=0,
                tickets_detected=0,
                warnings=warnings,
            )
        page_count = 1
        pages.append(_PageResult(page_num=1, text=text, success=True, used_ocr=ocr_used))
        warnings.extend(ocr_warnings)
    else:
        page_count = handle.page_count
        for i in range(page_count):
            try:
                text = handle.get_page_text(i)
                if text and text.strip():
                    pages.append(_PageResult(page_num=i + 1, text=text.strip(), success=True))
                else:
                    ocr_text = _ocr_page_fallback(file_path, i)
                    if ocr_text:
                        pages.append(_PageResult(page_num=i + 1, text=ocr_text, success=True, used_ocr=True))
                    else:
                        warnings.append(f"Page {i + 1} appears blank or contains only images. Skipping.")
            except Exception as exc:
                warnings.append(f"Page {i + 1} failed: {exc}. Skipping.")
                logger.warning("PDF page extraction failed: page=%d error=%s", i + 1, exc)

        handle.close()

    merged_text = _merge_pages(pages)
    tickets_detected = _count_tickets(merged_text)

    return IngestionResult(
        text=merged_text,
        file_type="PDF",
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        pages=page_count,
        tickets_detected=tickets_detected,
        warnings=warnings,
    )


def _try_open_pdf(file_path: str) -> _PdfHandle | None:
    try:
        import pdfplumber

        pdf = pdfplumber.open(file_path)
        if len(pdf.pages) > 0:
            return _PdfHandle(source=pdf, library="pdfplumber")
        pdf.close()
    except Exception:
        logger.debug("pdfplumber failed, trying PyMuPDF", exc_info=True)

    try:
        import fitz

        doc = fitz.open(file_path)
        if doc.page_count > 0:
            return _PdfHandle(source=doc, library="fitz")
        doc.close()
    except Exception:
        logger.debug("PyMuPDF also failed", exc_info=True)

    return None


def _ocr_page_fallback(file_path: str, page_idx: int) -> str | None:
    try:
        import pytesseract
        from pdf2image import convert_from_path

        images = convert_from_path(file_path, first_page=page_idx + 1, last_page=page_idx + 1)
        if not images:
            return None
        text = pytesseract.image_to_string(images[0])
        return text.strip() if text.strip() else None
    except ImportError:
        logger.debug("OCR libraries not available (pdf2image / pytesseract)")
        return None
    except Exception as exc:
        logger.warning("OCR failed on page %d", page_idx + 1, exc_info=exc)
        return None


def _ocr_fallback(file_path: str):
    try:
        import pytesseract
        from pdf2image import convert_from_path

        images = convert_from_path(file_path)
        texts: list[str] = []
        for img in images:
            t = pytesseract.image_to_string(img).strip()
            if t:
                texts.append(t)
        if texts:
            return "\n\n".join(texts), True, []
        return None, False, ["No text found via OCR."]
    except ImportError:
        return None, False, ["Page contains scanned image. OCR unavailable."]
    except Exception as exc:
        return None, False, [f"OCR processing error: {exc}"]


def _merge_pages(pages: list[_PageResult]) -> str:
    if not pages:
        return ""
    blocks = [p.text for p in pages if p.text.strip()]
    return "\n\n".join(blocks)


def _count_tickets(text: str) -> int:
    if not text.strip():
        return 0
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return max(1, len(lines))
