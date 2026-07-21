from app.api.models import MetricsResponse
from app.database.database import SessionLocal
from app.database.repository import ExtractionRepository


class MetricsService:
    """Service for gathering extraction metrics from the database."""

    def __init__(self) -> None:
        self._repo = ExtractionRepository()

    def get_metrics(self) -> MetricsResponse:
        with SessionLocal() as session:
            session.expire_on_commit = False
            stats = self._repo.get_stats(db_session=session)
            failure_breakdown = self._repo.failure_breakdown(db_session=session)
            latency_history = self._repo.latency_history(db_session=session)
            success_history = self._repo.success_history(db_session=session)
            retry_history = self._repo.retry_history(db_session=session)

        total_requests = stats.total

        schema_valid_rate = round(stats.successful / total_requests * 100, 2) if total_requests > 0 else 0.0
        average_retry_count = round(stats.average_retry_count or 0.0, 2)
        average_processing_time = round(stats.average_processing_time or 0.0, 2)
        average_confidence = round(stats.average_confidence or 0.0, 1)

        return MetricsResponse(
            total_requests=total_requests,
            successful_extractions=stats.successful,
            failed_extractions=stats.failed,
            schema_valid_rate=schema_valid_rate,
            average_retry_count=average_retry_count,
            average_processing_time=average_processing_time,
            failure_breakdown=failure_breakdown,
            last_updated=stats.last_updated,
            latency_history=latency_history,
            success_history=success_history,
            retry_history=retry_history,
            average_confidence=average_confidence,
            needs_review_count=stats.needs_review_count,
            repair_count=stats.repair_count,
            repair_success_count=stats.repair_success_count,
            failure_rate=stats.failure_rate,
        )
