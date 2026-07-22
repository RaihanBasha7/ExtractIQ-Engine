from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch


class TestIngestFile:
    def test_ingest_txt_file(self):
        from app.ingestion import ingest_file

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a test ticket with enough content for segmentation purposes.")
            f.flush()
            path = f.name

        try:
            result = ingest_file(path, "test.txt", 50)
            assert result.file_type == "TXT"
            assert "test ticket" in result.text.lower()
            assert result.tickets_detected is not None
        finally:
            Path(path).unlink(missing_ok=True)

    def test_detect_file_type_lowercase(self):
        from app.ingestion import detect_file_type

        assert detect_file_type("test.PDF") == "PDF"

    def test_ingestion_result_format(self):
        from app.ingestion import IngestionResult

        result = IngestionResult(text="Hello", file_type="TXT", file_name="test.txt", file_size_bytes=5)
        assert result.text == "Hello"
        assert result.pages is None
        assert result.warnings == []
        assert result.segments == []

    def test_segment_info_format(self):
        from app.ingestion import SegmentInfo

        seg = SegmentInfo(text="Hello", index=0)
        assert seg.text == "Hello"
        assert seg.word_count == 0
        assert seg.char_count == 0
        assert seg.valid is True

    def test_ingest_file_with_segmentation_failure(self):
        from app.ingestion import ingest_file

        with patch("app.ingestion.segmenter.segment_document") as mock_seg:
            mock_seg.side_effect = Exception("Segmentation engine crashed")
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("Some content that is long enough for segmentation purposes.")
                f.flush()
                path = f.name

            try:
                result = ingest_file(path, "test.txt", 20)
                assert any("Segmentation" in w for w in result.warnings)
            finally:
                Path(path).unlink(missing_ok=True)
