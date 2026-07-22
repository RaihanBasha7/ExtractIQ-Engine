from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.database.models import ExtractionResult, RawTicket
from app.logging import get_logger, log_event

logger = get_logger(__name__)


@contextmanager
def _resolve_session(session: Session | None) -> Iterator[Session]:
    """Yield the provided session or create+commit a new one.

    Mode A (default, session is None):
        Creates a new Session, yields it, commits after the caller finishes,
        then closes it. Objects returned by the repository remain usable after
        the session closes (expire_on_commit is disabled).

    Mode B (external session provided):
        Yields the caller-owned session without committing or closing.
        The caller is responsible for commit/rollback and cleanup.
    """
    if session is not None:
        yield session
    else:
        s = SessionLocal()
        s.expire_on_commit = False
        try:
            yield s
            s.commit()
        except BaseException:
            s.rollback()
            raise
        finally:
            s.close()


class RawTicketRepository:
    def save(
        self,
        ticket_id: str,
        raw_text: str,
        cleaned_text: str,
        language: str,
        db_session: Session | None = None,
    ) -> RawTicket:
        with _resolve_session(db_session) as session:
            try:
                ticket = RawTicket(
                    ticket_id=ticket_id,
                    raw_text=raw_text,
                    cleaned_text=cleaned_text,
                    language=language,
                )
                session.add(ticket)
                session.flush()
                session.refresh(ticket)
                log_event(
                    logger, event="raw_ticket_saved", stage="preprocessing", status="success", ticket_id=ticket_id
                )
                return ticket
            except Exception:
                log_event(
                    logger,
                    event="raw_ticket_save_failed",
                    stage="preprocessing",
                    status="failed",
                    level="ERROR",
                    exc_info=True,
                    ticket_id=ticket_id,
                )
                raise

    def get_by_ticket_id(
        self,
        ticket_id: str,
        db_session: Session | None = None,
    ) -> RawTicket | None:
        with _resolve_session(db_session) as session:
            return session.query(RawTicket).filter(RawTicket.ticket_id == ticket_id).first()

    def list_all(
        self,
        db_session: Session | None = None,
    ) -> list[RawTicket]:
        with _resolve_session(db_session) as session:
            return session.query(RawTicket).order_by(RawTicket.created_at.desc()).all()


class ExtractionRepository:
    def save(
        self,
        ticket_id: str,
        structured_json: dict | None,
        schema_valid: bool,
        retry_count: int,
        failure_category: str | None,
        latency_seconds: float,
        repair_attempts_json: list | None = None,
        confidence_score: float = 0.0,
        validation_status: str = "failed",
        repair_attempts_count: int = 0,
        final_status: str = "NEEDS_REVIEW",
        needs_review_reason: str | None = None,
        db_session: Session | None = None,
    ) -> ExtractionResult:
        with _resolve_session(db_session) as session:
            try:
                result = ExtractionResult(
                    ticket_id=ticket_id,
                    structured_json=structured_json,
                    schema_valid=schema_valid,
                    retry_count=retry_count,
                    failure_category=failure_category,
                    latency_seconds=latency_seconds,
                    repair_attempts_json=repair_attempts_json,
                    confidence_score=confidence_score,
                    validation_status=validation_status,
                    repair_attempts_count=repair_attempts_count,
                    final_status=final_status,
                    needs_review_reason=needs_review_reason,
                )
                session.add(result)
                session.flush()
                session.refresh(result)
                log_event(
                    logger,
                    event="extraction_result_saved",
                    stage="extraction",
                    status="success",
                    ticket_id=ticket_id,
                    action="save_result",
                )
                return result
            except Exception:
                log_event(
                    logger,
                    event="extraction_result_save_failed",
                    stage="extraction",
                    status="failed",
                    level="ERROR",
                    exc_info=True,
                    ticket_id=ticket_id,
                    action="save_result",
                )
                raise

    def get_by_ticket_id(
        self,
        ticket_id: str,
        db_session: Session | None = None,
    ) -> list[ExtractionResult]:
        with _resolve_session(db_session) as session:
            return (
                session.query(ExtractionResult)
                .filter(ExtractionResult.ticket_id == ticket_id)
                .order_by(ExtractionResult.created_at.desc())
                .all()
            )

    def list_all(
        self,
        db_session: Session | None = None,
    ) -> list[ExtractionResult]:
        with _resolve_session(db_session) as session:
            return session.query(ExtractionResult).order_by(ExtractionResult.created_at.desc()).all()

    def count(
        self,
        db_session: Session | None = None,
    ) -> int:
        with _resolve_session(db_session) as session:
            return session.query(ExtractionResult).count()

    def successful_count(
        self,
        db_session: Session | None = None,
    ) -> int:
        with _resolve_session(db_session) as session:
            return session.query(ExtractionResult).filter(ExtractionResult.schema_valid.is_(True)).count()

    def failed_count(
        self,
        db_session: Session | None = None,
    ) -> int:
        with _resolve_session(db_session) as session:
            return session.query(ExtractionResult).filter(ExtractionResult.schema_valid.is_(False)).count()

    def average_retry_count(
        self,
        db_session: Session | None = None,
    ) -> float | None:
        with _resolve_session(db_session) as session:
            return session.query(func.avg(ExtractionResult.retry_count)).scalar()

    def average_processing_time(
        self,
        db_session: Session | None = None,
    ) -> float | None:
        with _resolve_session(db_session) as session:
            return session.query(func.avg(ExtractionResult.latency_seconds)).scalar()

    def failure_breakdown(
        self,
        db_session: Session | None = None,
    ) -> dict[str, int]:
        with _resolve_session(db_session) as session:
            rows = (
                session.query(
                    ExtractionResult.failure_category,
                    func.count(ExtractionResult.id),
                )
                .filter(ExtractionResult.failure_category.isnot(None))
                .group_by(ExtractionResult.failure_category)
                .all()
            )
            return {row[0]: row[1] for row in rows}

    def last_updated(
        self,
        db_session: Session | None = None,
    ) -> datetime | None:
        with _resolve_session(db_session) as session:
            return session.query(func.max(ExtractionResult.created_at)).scalar()

    def list_history(
        self,
        limit: int = 50,
        offset: int = 0,
        db_session: Session | None = None,
    ) -> list[dict]:
        with _resolve_session(db_session) as session:
            rows = (
                session.query(
                    ExtractionResult.id,
                    ExtractionResult.ticket_id,
                    ExtractionResult.structured_json,
                    ExtractionResult.schema_valid,
                    ExtractionResult.retry_count,
                    ExtractionResult.repair_attempts_json,
                    ExtractionResult.failure_category,
                    ExtractionResult.latency_seconds,
                    ExtractionResult.confidence_score,
                    ExtractionResult.validation_status,
                    ExtractionResult.repair_attempts_count,
                    ExtractionResult.final_status,
                    ExtractionResult.needs_review_reason,
                    ExtractionResult.created_at,
                    RawTicket.raw_text,
                )
                .outerjoin(RawTicket, ExtractionResult.ticket_id == RawTicket.ticket_id)
                .order_by(ExtractionResult.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "ticket_id": r.ticket_id,
                    "structured_json": r.structured_json,
                    "schema_valid": r.schema_valid,
                    "retry_count": r.retry_count,
                    "repair_attempts": r.repair_attempts_json or [],
                    "failure_category": r.failure_category,
                    "latency_seconds": r.latency_seconds,
                    "confidence_score": r.confidence_score or 0.0,
                    "validation_status": r.validation_status or "failed",
                    "repair_attempts_count": r.repair_attempts_count or 0,
                    "final_status": r.final_status or "NEEDS_REVIEW",
                    "needs_review_reason": r.needs_review_reason,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "raw_text": r.raw_text or "",
                }
                for r in rows
            ]

    def count_history(
        self,
        db_session: Session | None = None,
    ) -> int:
        with _resolve_session(db_session) as session:
            return session.query(ExtractionResult).count()

    def latency_history(
        self,
        db_session: Session | None = None,
    ) -> list[dict]:
        with _resolve_session(db_session) as session:
            rows = (
                session.query(
                    ExtractionResult.latency_seconds,
                    ExtractionResult.created_at,
                )
                .order_by(ExtractionResult.created_at.asc())
                .all()
            )
            return [
                {"t": r.created_at.isoformat() if r.created_at else "", "latency": round(r.latency_seconds * 1000)}
                for r in rows
            ]

    def success_history(
        self,
        db_session: Session | None = None,
    ) -> list[dict]:
        with _resolve_session(db_session) as session:
            rows = (
                session.query(
                    ExtractionResult.schema_valid,
                    ExtractionResult.created_at,
                )
                .order_by(ExtractionResult.created_at.asc())
                .all()
            )
            return [
                {"t": r.created_at.isoformat() if r.created_at else "", "rate": 100.0 if r.schema_valid else 0.0}
                for r in rows
            ]

    def retry_history(
        self,
        db_session: Session | None = None,
    ) -> list[dict]:
        with _resolve_session(db_session) as session:
            rows = (
                session.query(
                    ExtractionResult.retry_count,
                    ExtractionResult.created_at,
                )
                .order_by(ExtractionResult.created_at.asc())
                .all()
            )
            return [{"t": r.created_at.isoformat() if r.created_at else "", "retries": r.retry_count} for r in rows]

    def get_stats(
        self,
        db_session: Session | None = None,
    ) -> "ExtractionStats":
        with _resolve_session(db_session) as session:
            row = session.query(
                func.count(ExtractionResult.id).label("total"),
                func.sum(case((ExtractionResult.schema_valid.is_(True), 1), else_=0)).label("successful"),
                func.sum(case((ExtractionResult.schema_valid.is_(False), 1), else_=0)).label("failed"),
                func.avg(ExtractionResult.retry_count).label("avg_retry"),
                func.avg(ExtractionResult.latency_seconds).label("avg_time"),
                func.max(ExtractionResult.created_at).label("last_updated"),
                func.avg(ExtractionResult.confidence_score).label("avg_confidence"),
                func.sum(case((ExtractionResult.final_status == "NEEDS_REVIEW", 1), else_=0)).label("needs_review"),
                func.sum(case((ExtractionResult.retry_count > 0, 1), else_=0)).label("repair_count"),
                func.sum(case((ExtractionResult.final_status == "REPAIRED", 1), else_=0)).label("repair_success_count"),
            ).first()
            total = row.total or 0
            needs_review = row.needs_review or 0
            return ExtractionStats(
                total=total,
                successful=row.successful or 0,
                failed=row.failed or 0,
                average_retry_count=row.avg_retry,
                average_processing_time=row.avg_time,
                last_updated=row.last_updated,
                average_confidence=row.avg_confidence,
                needs_review_count=needs_review,
                repair_count=row.repair_count or 0,
                repair_success_count=row.repair_success_count or 0,
                failure_rate=round((needs_review / total * 100), 1) if total > 0 else 0.0,
            )


@dataclass
class ExtractionStats:
    total: int
    successful: int
    failed: int
    average_retry_count: float | None
    average_processing_time: float | None
    last_updated: datetime | None
    average_confidence: float | None = None
    needs_review_count: int = 0
    repair_count: int = 0
    repair_success_count: int = 0
    failure_rate: float = 0.0
