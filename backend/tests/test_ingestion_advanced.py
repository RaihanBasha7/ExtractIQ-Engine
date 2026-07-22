from __future__ import annotations

import json
import tempfile
from pathlib import Path


class TestJsonParserAdvanced:
    def test_parse_json_nested_object(self):
        from app.ingestion.json_parser import parse_json

        data = {"data": [{"text": "Nested ticket"}]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name

        try:
            result = parse_json(path, "test.json", 100)
            assert result.tickets_detected >= 1
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_json_empty_object(self):
        from app.ingestion.json_parser import parse_json

        data = {}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name

        try:
            result = parse_json(path, "test.json", 10)
            assert result.tickets_detected == 0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_json_with_integers(self):
        from app.ingestion.json_parser import parse_json

        data = [{"text": 12345}, {"text": 67890}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name

        try:
            result = parse_json(path, "test.json", 50)
            assert result.tickets_detected >= 1
        finally:
            Path(path).unlink(missing_ok=True)

    def test_extract_texts_empty_list(self):
        from app.ingestion.json_parser import _extract_texts

        assert _extract_texts([]) == []

    def test_extract_texts_list_with_strings(self):
        from app.ingestion.json_parser import _extract_texts

        result = _extract_texts(["ticket one", "ticket two"])
        assert result == ["ticket one", "ticket two"]

    def test_extract_text_field_number_value(self):
        from app.ingestion.json_parser import _extract_text_field

        result = _extract_text_field({"text": 42})
        assert result == "42"

    def test_extract_text_field_no_match(self):
        from app.ingestion.json_parser import _extract_text_field

        result = _extract_text_field({"id": 1, "count": 2})
        assert result is None


class TestCsvParserAdvanced:
    def test_parse_csv_missing_column(self):
        from app.ingestion.csv_parser import parse_csv

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("id,name\n1,John\n2,Jane")
            f.flush()
            path = f.name

        try:
            result = parse_csv(path, "test.csv", 100, text_column="description")
            assert "not found" in " ".join(result.warnings)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_csv_custom_column(self):
        from app.ingestion.csv_parser import parse_csv

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("id,description\n1,Help with order\n2,Account issue")
            f.flush()
            path = f.name

        try:
            result = parse_csv(path, "test.csv", 100, text_column="description")
            assert "Help with order" in result.text
            assert result.tickets_detected == 2
        finally:
            Path(path).unlink(missing_ok=True)

    def test_detect_text_column_fallback(self):
        from app.ingestion.csv_parser import _detect_text_column

        result = _detect_text_column(["id", "timestamp", "name"])
        assert result == "name"


class TestTxtParserAdvanced:
    def test_read_text_encoding_fallback(self):
        from app.ingestion.txt_parser import _read_text

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write("Hello World".encode("latin-1"))
            f.flush()
            path = f.name

        try:
            text = _read_text(path)
            assert text is not None
            assert "Hello World" in text
        finally:
            Path(path).unlink(missing_ok=True)

    def test_parse_txt_from_nonexistent_file(self):
        from app.ingestion.txt_parser import parse_txt

        result = parse_txt("/tmp/definitely_not_exists_xyz.txt", "test.txt", 100)
        assert result.text == ""
        assert len(result.warnings) > 0


class TestSegmenterAdvanced:
    def test_structured_separator_detection(self):
        from app.ingestion.segmenter import _extract_structured_tickets

        text = "=== TICKET 01 ===\ncontent one\n=== TICKET 02 ===\ncontent two"
        tickets, count = _extract_structured_tickets(text)
        assert count >= 1
        assert len(tickets) >= 1

    def test_rule_based_boundaries(self):
        from app.ingestion.segmenter import (
            _find_boundaries,
            _split_at_boundaries,
        )

        text = "Ticket #123: Some issue\nSome content\nTicket #124: Another issue"
        boundaries = _find_boundaries(text)
        assert len(boundaries) >= 1

        segments = _split_at_boundaries(text, boundaries)
        assert len(segments) >= 1

    def test_validate_segments_oversized_split(self):
        from app.ingestion.segmenter import _validate_segments

        large_text = "Paragraph " + ("A" * 5000) + "\n\n" + ("B" * 5000)
        segments = [(large_text, "rule")]
        result = _validate_segments(segments)
        assert len(result) >= 1

    def test_segment_document_no_separators(self):
        from app.ingestion.segmenter import segment_document

        result = segment_document("Just a plain text document with no clear structure.", use_ai=False)
        assert len(result.segments) == 1

    def test_split_oversized_empty(self):
        from app.ingestion.segmenter import _split_oversized

        assert _split_oversized("") == [""]

    def test_find_boundaries_no_match(self):
        from app.ingestion.segmenter import _find_boundaries

        result = _find_boundaries("plain text with no ticket patterns")
        assert result == []

    def test_segment_document_with_double_newlines(self):
        from app.ingestion.segmenter import segment_document

        text = "\n\n\n   \n\n"
        result = segment_document(text)
        assert len(result.segments) == 0

    def test_classify_pattern(self):
        import re

        from app.ingestion.segmenter import _classify_pattern

        p1 = re.compile(r"^[-=*_]{3,}\s*$", re.MULTILINE)
        assert _classify_pattern(p1) == "separator"

        p2 = re.compile(r"^-+\s*Page\s+\d+\s*-+\s*$", re.MULTILINE | re.IGNORECASE)
        assert _classify_pattern(p2) == "page_break"

        p3 = re.compile(r"^(?:From|To|Cc|Bcc|Subject|Date)\s*:", re.MULTILINE)
        assert _classify_pattern(p3) == "email_header"


class TestIngestionInitAdvanced:
    def test_split_ext(self):
        from app.ingestion import _split_ext

        assert _split_ext("file.txt") == ("file", ".txt")
        assert _split_ext(".hidden") == (".hidden", "")
        assert _split_ext("noext") == ("noext", "")
