import datetime

from sqlalchemy import Boolean, Float, Integer, String, Text, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class RawTicket(Base):
    __tablename__ = "raw_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now(datetime.timezone.utc),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<RawTicket(ticket_id={self.ticket_id!r})>"


class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    structured_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    schema_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repair_attempts_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    failure_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latency_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    validation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="failed")
    repair_attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    final_status: Mapped[str] = mapped_column(String(20), nullable=False, default="NEEDS_REVIEW")
    needs_review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now(datetime.timezone.utc),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<ExtractionResult(ticket_id={self.ticket_id!r}, status={self.final_status})>"
