"""Tests for the evaluation module."""

from __future__ import annotations

import pytest

from app.schema import (
    Customer,
    Entities,
    Issue,
    IssueCategory,
    ResolutionStatus,
    Sentiment,
    TicketExtraction,
    Urgency,
)


class TestEvaluationModels:
    def test_evaluation_record_defaults(self):
        from app.evaluation.models import EvaluationRecord

        record = EvaluationRecord(
            ticket_id="TKT-001",
            schema_valid=True,
            repair_attempted=False,
            repair_success=False,
            retry_count=0,
            latency_ms=100,
            infra_error=False,
        )
        assert record.ticket_id == "TKT-001"
        assert record.schema_valid is True
        assert record.failure_reason is None
        assert record.field_accuracy is None
        assert record.schema_version == "1.0"

    def test_evaluation_record_full(self):
        from app.evaluation.models import EvaluationRecord

        record = EvaluationRecord(
            ticket_id="TKT-001",
            schema_valid=True,
            repair_attempted=True,
            repair_success=True,
            retry_count=1,
            latency_ms=500,
            infra_error=False,
            failure_reason="validation_error",
            expected_category="billing",
            predicted_category="billing",
            field_accuracy=0.95,
            failure_stage="validation",
            processing_time=0.6,
            model_name="test-model",
            provider="groq",
            repair_attempts=1,
            schema_version="1.0",
        )
        assert record.failure_reason == "validation_error"
        assert record.field_accuracy == 0.95
        assert record.model_name == "test-model"


class TestEvaluationCollector:
    def test_add_record_from_successful_result(self):
        from app.evaluation.collector import EvaluationCollector
        from app.extraction import ExtractionResult

        valid_ticket = TicketExtraction(
            ticket_id="TKT-001",
            customer=Customer(name="John", account_id="ACC-001"),
            issue=Issue(category=IssueCategory.billing, urgency=Urgency.high),
            sentiment=Sentiment.frustrated,
            entities=Entities(order_ids=["ORD-001"]),
            resolution_status=ResolutionStatus.unresolved,
        )

        result = ExtractionResult(
            ticket_id="TKT-001",
            success=True,
            data=valid_ticket,
            latency_seconds=0.5,
        )

        collector = EvaluationCollector()
        record = collector.add(result, expected=valid_ticket, processing_time_seconds=0.6)

        assert record.ticket_id == "TKT-001"
        assert record.schema_valid is True
        assert record.repair_attempted is False
        assert record.field_accuracy is not None
        assert record.field_accuracy > 0.9

    def test_add_record_from_failed_result(self):
        from app.evaluation.collector import EvaluationCollector
        from app.extraction import ExtractionResult

        result = ExtractionResult(
            ticket_id="TKT-002",
            success=False,
            data=None,
            failure_category="validation_error",
            latency_seconds=0.3,
        )

        collector = EvaluationCollector()
        record = collector.add(result)

        assert record.ticket_id == "TKT-002"
        assert record.schema_valid is False
        assert record.failure_reason == "validation_error"
        assert record.field_accuracy is None


class TestEvaluationMetrics:
    def test_schema_valid_rate(self):
        from app.evaluation.metrics import calculate_schema_valid_rate
        from app.evaluation.models import EvaluationRecord

        records = [
            EvaluationRecord(
                ticket_id="T1",
                schema_valid=True,
                repair_attempted=False,
                repair_success=False,
                retry_count=0,
                latency_ms=100,
                infra_error=False,
            ),
            EvaluationRecord(
                ticket_id="T2",
                schema_valid=True,
                repair_attempted=False,
                repair_success=False,
                retry_count=0,
                latency_ms=100,
                infra_error=False,
            ),
            EvaluationRecord(
                ticket_id="T3",
                schema_valid=False,
                repair_attempted=True,
                repair_success=False,
                retry_count=3,
                latency_ms=500,
                infra_error=False,
            ),
        ]
        rate = calculate_schema_valid_rate(records)
        assert rate == pytest.approx(2 / 3, rel=1e-3)

    def test_empty_records_return_zero(self):
        from app.evaluation.metrics import calculate_schema_valid_rate

        assert calculate_schema_valid_rate([]) == 0.0

    def test_average_latency(self):
        from app.evaluation.metrics import calculate_average_latency
        from app.evaluation.models import EvaluationRecord

        records = [
            EvaluationRecord(
                ticket_id="T1",
                schema_valid=True,
                repair_attempted=False,
                repair_success=False,
                retry_count=0,
                latency_ms=100,
                infra_error=False,
            ),
            EvaluationRecord(
                ticket_id="T2",
                schema_valid=True,
                repair_attempted=False,
                repair_success=False,
                retry_count=0,
                latency_ms=300,
                infra_error=False,
            ),
        ]
        avg = calculate_average_latency(records)
        assert avg == 200.0

    def test_average_retries(self):
        from app.evaluation.metrics import calculate_average_retries
        from app.evaluation.models import EvaluationRecord

        records = [
            EvaluationRecord(
                ticket_id="T1",
                schema_valid=True,
                repair_attempted=False,
                repair_success=False,
                retry_count=0,
                latency_ms=100,
                infra_error=False,
            ),
            EvaluationRecord(
                ticket_id="T2",
                schema_valid=True,
                repair_attempted=False,
                repair_success=False,
                retry_count=2,
                latency_ms=200,
                infra_error=False,
            ),
        ]
        avg = calculate_average_retries(records)
        assert avg == 1.0


class TestEvaluationRepository:
    def test_save_and_load(self, tmp_data_dir):
        from app.evaluation.models import EvaluationRecord
        from app.evaluation.repository import EvaluationRepository

        path = tmp_data_dir / "test_records.jsonl"
        repo = EvaluationRepository(path=path)

        record = EvaluationRecord(
            ticket_id="TKT-001",
            schema_valid=True,
            repair_attempted=False,
            repair_success=False,
            retry_count=0,
            latency_ms=100,
            infra_error=False,
        )
        repo.save(record)
        loaded = repo.load()
        assert len(loaded) == 1
        assert loaded[0].ticket_id == "TKT-001"

    def test_load_empty_repository(self, tmp_data_dir):
        from app.evaluation.repository import EvaluationRepository

        path = tmp_data_dir / "empty.jsonl"
        repo = EvaluationRepository(path=path)
        records = repo.load()
        assert records == []

    def test_clear_repository(self, tmp_data_dir):
        from app.evaluation.models import EvaluationRecord
        from app.evaluation.repository import EvaluationRepository

        path = tmp_data_dir / "clear_test.jsonl"
        repo = EvaluationRepository(path=path)
        record = EvaluationRecord(
            ticket_id="TKT-001",
            schema_valid=True,
            repair_attempted=False,
            repair_success=False,
            retry_count=0,
            latency_ms=100,
            infra_error=False,
        )
        repo.save(record)
        repo.clear()
        assert repo.load() == []

    def test_statistics_empty(self, tmp_data_dir):
        from app.evaluation.repository import EvaluationRepository

        path = tmp_data_dir / "stats_empty.jsonl"
        repo = EvaluationRepository(path=path)
        stats = repo.statistics()
        assert stats["total"] == 0

    def test_statistics_with_data(self, tmp_data_dir):
        from app.evaluation.models import EvaluationRecord
        from app.evaluation.repository import EvaluationRepository

        path = tmp_data_dir / "stats_data.jsonl"
        repo = EvaluationRepository(path=path)
        repo.save(
            EvaluationRecord(
                ticket_id="T1",
                schema_valid=True,
                repair_attempted=False,
                repair_success=False,
                retry_count=0,
                latency_ms=100,
                infra_error=False,
            )
        )
        repo.save(
            EvaluationRecord(
                ticket_id="T2",
                schema_valid=False,
                repair_attempted=True,
                repair_success=False,
                retry_count=3,
                latency_ms=500,
                infra_error=False,
            )
        )

        stats = repo.statistics()
        assert stats["total"] == 2
        assert stats["schema_valid"] == 1
        assert stats["schema_valid_rate"] == 0.5
        assert stats["failed"] == 1
