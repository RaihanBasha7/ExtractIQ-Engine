"""Tests for database operations."""

from __future__ import annotations

from sqlalchemy.orm import Session


class TestExtractionRepository:
    def test_insert_extraction(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        result = repo.save(
            ticket_id="TKT-001",
            structured_json={"ticket_id": "TKT-001"},
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=0.5,
            db_session=db_session,
        )
        assert result.ticket_id == "TKT-001"
        assert result.schema_valid is True
        assert result.retry_count == 0

    def test_retrieve_extraction(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        repo.save(
            ticket_id="TKT-001",
            structured_json={"test": "data"},
            schema_valid=True,
            retry_count=1,
            failure_category=None,
            latency_seconds=0.5,
            db_session=db_session,
        )
        results = repo.get_by_ticket_id("TKT-001", db_session=db_session)
        assert len(results) == 1
        assert results[0].schema_valid is True

    def test_retrieve_nonexistent_ticket(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        results = repo.get_by_ticket_id("NONEXISTENT", db_session=db_session)
        assert results == []

    def test_count_extractions(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        assert repo.count(db_session=db_session) == 0

        repo.save(
            ticket_id="TKT-001",
            structured_json=None,
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=0.1,
            db_session=db_session,
        )
        repo.save(
            ticket_id="TKT-002",
            structured_json=None,
            schema_valid=False,
            retry_count=3,
            failure_category="validation_error",
            latency_seconds=0.5,
            db_session=db_session,
        )
        assert repo.count(db_session=db_session) == 2

    def test_successful_count(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        repo.save(
            ticket_id="TKT-001",
            structured_json=None,
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=0.1,
            db_session=db_session,
        )
        repo.save(
            ticket_id="TKT-002",
            structured_json=None,
            schema_valid=False,
            retry_count=0,
            failure_category="error",
            latency_seconds=0.1,
            db_session=db_session,
        )
        assert repo.successful_count(db_session=db_session) == 1
        assert repo.failed_count(db_session=db_session) == 1


class TestMetricsAggregation:
    def test_average_retry_count(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        assert repo.average_retry_count(db_session=db_session) is None

        repo.save(
            ticket_id="TKT-001",
            structured_json=None,
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=0.1,
            db_session=db_session,
        )
        repo.save(
            ticket_id="TKT-002",
            structured_json=None,
            schema_valid=True,
            retry_count=2,
            failure_category=None,
            latency_seconds=0.2,
            db_session=db_session,
        )
        avg = repo.average_retry_count(db_session=db_session)
        assert avg == 1.0

    def test_average_processing_time(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        repo.save(
            ticket_id="TKT-001",
            structured_json=None,
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=1.0,
            db_session=db_session,
        )
        repo.save(
            ticket_id="TKT-002",
            structured_json=None,
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=3.0,
            db_session=db_session,
        )
        avg = repo.average_processing_time(db_session=db_session)
        assert avg == 2.0

    def test_failure_breakdown(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        repo.save(
            ticket_id="TKT-001",
            structured_json=None,
            schema_valid=False,
            retry_count=3,
            failure_category="validation_error",
            latency_seconds=0.5,
            db_session=db_session,
        )
        repo.save(
            ticket_id="TKT-002",
            structured_json=None,
            schema_valid=False,
            retry_count=2,
            failure_category="validation_error",
            latency_seconds=0.3,
            db_session=db_session,
        )
        repo.save(
            ticket_id="TKT-003",
            structured_json=None,
            schema_valid=False,
            retry_count=1,
            failure_category="timeout",
            latency_seconds=0.1,
            db_session=db_session,
        )
        breakdown = repo.failure_breakdown(db_session=db_session)
        assert breakdown["validation_error"] == 2
        assert breakdown["timeout"] == 1

    def test_get_stats(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        repo.save(
            ticket_id="TKT-001",
            structured_json=None,
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=0.5,
            db_session=db_session,
        )
        repo.save(
            ticket_id="TKT-002",
            structured_json=None,
            schema_valid=False,
            retry_count=2,
            failure_category="error",
            latency_seconds=1.5,
            db_session=db_session,
        )
        stats = repo.get_stats(db_session=db_session)
        assert stats.total == 2
        assert stats.successful == 1
        assert stats.failed == 1
        assert stats.average_processing_time == 1.0


class TestHistoryRetrieval:
    def test_list_history_empty(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        items = repo.list_history(db_session=db_session)
        assert items == []

    def test_list_history_with_data(self, db_session: Session):
        from app.database.repository import ExtractionRepository, RawTicketRepository

        raw_repo = RawTicketRepository()
        ext_repo = ExtractionRepository()

        raw_repo.save(ticket_id="TKT-001", raw_text="Help", cleaned_text="Help", language="en", db_session=db_session)
        ext_repo.save(
            ticket_id="TKT-001",
            structured_json={"key": "val"},
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=0.5,
            db_session=db_session,
        )

        items = ext_repo.list_history(db_session=db_session)
        assert len(items) == 1
        assert items[0]["ticket_id"] == "TKT-001"
        assert items[0]["schema_valid"] is True

    def test_history_pagination(self, db_session: Session):
        from app.database.repository import ExtractionRepository, RawTicketRepository

        raw_repo = RawTicketRepository()
        ext_repo = ExtractionRepository()

        for i in range(5):
            raw_repo.save(
                ticket_id=f"TKT-{i:03d}",
                raw_text=f"Text {i}",
                cleaned_text=f"Text {i}",
                language="en",
                db_session=db_session,
            )
            ext_repo.save(
                ticket_id=f"TKT-{i:03d}",
                structured_json=None,
                schema_valid=True,
                retry_count=0,
                failure_category=None,
                latency_seconds=0.1,
                db_session=db_session,
            )

        items = ext_repo.list_history(limit=2, offset=0, db_session=db_session)
        assert len(items) == 2

    def test_count_history(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        assert repo.count_history(db_session=db_session) == 0
        repo.save(
            ticket_id="TKT-001",
            structured_json=None,
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=0.1,
            db_session=db_session,
        )
        assert repo.count_history(db_session=db_session) == 1

    def test_latency_history(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        repo.save(
            ticket_id="TKT-001",
            structured_json=None,
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=1.0,
            db_session=db_session,
        )
        history = repo.latency_history(db_session=db_session)
        assert len(history) == 1
        assert history[0]["latency"] == 1000

    def test_success_history(self, db_session: Session):
        from app.database.repository import ExtractionRepository

        repo = ExtractionRepository()
        repo.save(
            ticket_id="TKT-001",
            structured_json=None,
            schema_valid=True,
            retry_count=0,
            failure_category=None,
            latency_seconds=0.5,
            db_session=db_session,
        )
        history = repo.success_history(db_session=db_session)
        assert len(history) == 1
        assert history[0]["rate"] == 100.0


class TestRawTicketRepository:
    def test_save_raw_ticket(self, db_session: Session):
        from app.database.repository import RawTicketRepository

        repo = RawTicketRepository()
        ticket = repo.save(
            ticket_id="TKT-001",
            raw_text="Raw help text",
            cleaned_text="help text",
            language="en",
            db_session=db_session,
        )
        assert ticket.ticket_id == "TKT-001"
        assert ticket.raw_text == "Raw help text"
        assert ticket.cleaned_text == "help text"

    def test_get_by_ticket_id(self, db_session: Session):
        from app.database.repository import RawTicketRepository

        repo = RawTicketRepository()
        repo.save(ticket_id="TKT-001", raw_text="text", cleaned_text="text", language="en", db_session=db_session)
        ticket = repo.get_by_ticket_id("TKT-001", db_session=db_session)
        assert ticket is not None
        assert ticket.ticket_id == "TKT-001"

    def test_get_nonexistent(self, db_session: Session):
        from app.database.repository import RawTicketRepository

        repo = RawTicketRepository()
        ticket = repo.get_by_ticket_id("NONEXISTENT", db_session=db_session)
        assert ticket is None
