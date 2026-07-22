from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch


def _create_text_pdf(text: str) -> str:
    """Create a minimal PDF with text using PyMuPDF."""
    import fitz

    path = tempfile.mktemp(suffix=".pdf")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=12)
    doc.save(path)
    doc.close()
    return path


class TestPdfParser:
    def test_parse_pdf_basic(self):
        path = _create_text_pdf("Hello World")
        try:
            from app.ingestion.pdf_parser import parse_pdf

            result = parse_pdf(path, "test.pdf", 100)
            assert "Hello World" in result.text
            assert result.pages >= 1
            assert result.tickets_detected >= 1
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_pdf_multi_page(self):
        import fitz

        path = tempfile.mktemp(suffix=".pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 100), "Page 1 content", fontsize=12)
        page = doc.new_page()
        page.insert_text((50, 100), "Page 2 content", fontsize=12)
        doc.save(path)
        doc.close()

        try:
            from app.ingestion.pdf_parser import parse_pdf

            result = parse_pdf(path, "test.pdf", 100)
            assert "Page 1 content" in result.text
            assert "Page 2 content" in result.text
            assert result.pages == 2
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_pdf_nonexistent(self):
        from app.ingestion.pdf_parser import parse_pdf

        result = parse_pdf("/tmp/nonexistent_xyz.pdf", "test.pdf", 100)
        assert result.text == ""
        assert len(result.warnings) > 0

    def test_parse_pdf_empty_pages(self):
        import fitz

        path = tempfile.mktemp(suffix=".pdf")
        doc = fitz.open()
        doc.new_page()
        doc.new_page()
        doc.save(path)
        doc.close()

        try:
            from app.ingestion.pdf_parser import parse_pdf

            result = parse_pdf(path, "test.pdf", 100)
            assert len(result.warnings) > 0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_merge_pages_empty(self):
        from app.ingestion.pdf_parser import _merge_pages

        assert _merge_pages([]) == ""

    def test_merge_pages_with_text(self):
        from app.ingestion.pdf_parser import _merge_pages, _PageResult

        pages = [
            _PageResult(page_num=1, text="First page", success=True),
            _PageResult(page_num=2, text="Second page", success=True),
        ]
        result = _merge_pages(pages)
        assert "First page" in result
        assert "Second page" in result

    def test_count_tickets_empty(self):
        from app.ingestion.pdf_parser import _count_tickets

        assert _count_tickets("") == 0
        assert _count_tickets("   ") == 0

    def test_count_tickets_single(self):
        from app.ingestion.pdf_parser import _count_tickets

        assert _count_tickets("Single line") == 1

    @patch("app.ingestion.pdf_parser._try_open_pdf", return_value=None)
    @patch("app.ingestion.pdf_parser._ocr_fallback", return_value=(None, False, ["OCR unavailable."]))
    def test_parse_pdf_both_fail(self, mock_open, mock_ocr):
        from app.ingestion.pdf_parser import parse_pdf

        result = parse_pdf("test.pdf", "test.pdf", 100)
        assert result.text == ""
        assert any("OCR" in w for w in result.warnings)

    def test_pdf_handle_pdfplumber(self):
        from app.ingestion.pdf_parser import _PdfHandle

        path = _create_text_pdf("Test")
        try:
            import pdfplumber

            pdf = pdfplumber.open(path)
            handle = _PdfHandle(source=pdf, library="pdfplumber")
            assert handle.page_count >= 1
            text = handle.get_page_text(0)
            assert "Test" in text
            handle.close()
        finally:
            Path(path).unlink(missing_ok=True)

    def test_pdf_handle_fitz(self):
        from app.ingestion.pdf_parser import _PdfHandle
        import fitz

        path = _create_text_pdf("Fitz test")
        try:
            doc = fitz.open(path)
            handle = _PdfHandle(source=doc, library="fitz")
            assert handle.page_count >= 1
            text = handle.get_page_text(0)
            assert "Fitz test" in text
            handle.close()
        finally:
            Path(path).unlink(missing_ok=True)

    def test_pdf_handle_close_error(self):
        from app.ingestion.pdf_parser import _PdfHandle

        class BadSource:
            def close(self):
                raise RuntimeError("close failed")

        handle = _PdfHandle(source=BadSource(), library="pdfplumber")
        handle.close()  # should not raise
