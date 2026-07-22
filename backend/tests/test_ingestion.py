from __future__ import annotations

import json
import tempfile
from pathlib import Path


class TestIngestionInit:
    def test_detect_file_type(self):
        from app.ingestion import detect_file_type

        assert detect_file_type("test.pdf") == "PDF"
        assert detect_file_type("test.txt") == "TXT"
        assert detect_file_type("test.docx") == "DOCX"
        assert detect_file_type("test.csv") == "CSV"
        assert detect_file_type("test.json") == "JSON"
        assert detect_file_type("test.unknown") is None

    def test_ingest_file_unsupported(self):
        from app.ingestion import ingest_file

        import pytest

        with pytest.raises(ValueError, match="Unsupported file type"):
            ingest_file("test.xyz", "test.xyz", 100)


class TestTxtParser:
    def test_parse_txt_simple(self):
        from app.ingestion.txt_parser import parse_txt

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello World\nThis is a test")
            f.flush()
            path = f.name

        try:
            result = parse_txt(path, "test.txt", 50)
            assert result.file_type == "TXT"
            assert "Hello World" in result.text
            assert result.pages == 1
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_txt_empty(self):
        from app.ingestion.txt_parser import parse_txt

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            f.flush()
            path = f.name

        try:
            result = parse_txt(path, "test.txt", 0)
            assert result.text == ""
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_txt_too_large(self):
        from app.ingestion.txt_parser import parse_txt

        result = parse_txt("nonexistent.txt", "large.txt", 100 * 1024 * 1024)
        assert result.text == ""
        assert "too large" in " ".join(result.warnings).lower()

    def test_read_text_utf8(self):
        from app.ingestion.txt_parser import _read_text

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False) as f:
            f.write("Hello UTF-8: \u00f1o\u00f1o")
            f.flush()
            path = f.name

        try:
            text = _read_text(path)
            assert text is not None
            assert "\u00f1o\u00f1o" in text
        finally:
            Path(path).unlink(missing_ok=True)

    def test_count_tickets(self):
        from app.ingestion.txt_parser import _count_tickets

        assert _count_tickets("line1\nline2\nline3") == 3
        assert _count_tickets("") == 0
        assert _count_tickets("   ") == 0
        assert _count_tickets("single") == 1


class TestCsvParser:
    def test_parse_csv_basic(self):
        from app.ingestion.csv_parser import parse_csv

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("text,id\nHello World,1\nTest Message,2")
            f.flush()
            path = f.name

        try:
            result = parse_csv(path, "test.csv", 100)
            assert result.file_type == "CSV"
            assert "Hello World" in result.text
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_csv_empty_text_column(self):
        from app.ingestion.csv_parser import parse_csv

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("text,id\n,1\n,2")
            f.flush()
            path = f.name

        try:
            result = parse_csv(path, "test.csv", 100)
            assert result.tickets_detected == 0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_detect_text_column(self):
        from app.ingestion.csv_parser import _detect_text_column

        assert _detect_text_column(["id", "text", "value"]) == "text"
        assert _detect_text_column(["id", "message", "value"]) == "message"
        assert _detect_text_column(["id", "name"]) == "name"


class TestJsonParser:
    def test_parse_json_array(self):
        from app.ingestion.json_parser import parse_json

        data = [{"text": "Ticket one"}, {"text": "Ticket two"}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name

        try:
            result = parse_json(path, "test.json", 200)
            assert result.file_type == "JSON"
            assert "Ticket one" in result.text
            assert result.tickets_detected == 2
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_json_object(self):
        from app.ingestion.json_parser import parse_json

        data = {"message": "Single ticket"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name

        try:
            result = parse_json(path, "test.json", 100)
            assert result.tickets_detected == 1
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_json_invalid(self):
        from app.ingestion.json_parser import parse_json

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not json{")
            f.flush()
            path = f.name

        try:
            result = parse_json(path, "test.json", 50)
            assert any("Invalid JSON" in w or "Failed to parse" in w for w in result.warnings)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_extract_texts_from_list(self):
        from app.ingestion.json_parser import _extract_texts

        result = _extract_texts([{"text": "A"}, {"text": "B"}])
        assert result == ["A", "B"]

    def test_extract_texts_from_dict(self):
        from app.ingestion.json_parser import _extract_texts

        result = _extract_texts({"text": "Hello"})
        assert result == ["Hello"]

    def test_extract_texts_nested_list(self):
        from app.ingestion.json_parser import _extract_texts

        result = _extract_texts({"data": [{"text": "Nested"}]})
        assert result == ["Nested"]

    def test_extract_text_field_fallback(self):
        from app.ingestion.json_parser import _extract_text_field

        result = _extract_text_field({"unknown": "value"})
        assert result == "value"


class TestSegmenter:
    def test_segment_document_empty(self):
        from app.ingestion.segmenter import segment_document

        result = segment_document("")
        assert len(result.segments) == 0
        assert result.method == "single"

    def test_segment_document_single(self):
        from app.ingestion.segmenter import segment_document

        result = segment_document("A single ticket text with enough content to be meaningful.")
        assert len(result.segments) == 1

    def test_find_structured_separators(self):
        from app.ingestion.segmenter import _find_structured_separators

        text = "=== TICKET 01 ===\nContent here\n=== TICKET 02 ===\nMore content"
        blocks = _find_structured_separators(text)
        assert len(blocks) >= 1

    def test_validate_segments_merges_small(self):
        from app.ingestion.segmenter import _validate_segments

        segments = [("Small chunk of text", "rule"), ("Another small piece", "rule")]
        result = _validate_segments(segments)
        assert len(result) >= 1

    def test_line_break_fallback_single_block(self):
        from app.ingestion.segmenter import _line_break_fallback

        result = _line_break_fallback("Just a single block of text that is long enough to not be merged.")
        assert len(result) == 1
