from __future__ import annotations

import csv
import io
import json
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import EVALUATION_RECORDS_PATH
from app.evaluation.models import EvaluationRecord
from app.logging import get_logger, log_event

logger = get_logger(__name__)


class EvaluationRepository:
    """Persistent storage for evaluation records backed by a JSONL file.

    Thread-safe for sequential writes (append-only).  Malformed lines are
    silently skipped with a warning rather than crashing ``load()``.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path or EVALUATION_RECORDS_PATH)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        log_event(logger, event="repository_init", stage="evaluation", status="started", path=str(self._path))

    @property
    def path(self) -> Path:
        return self._path

    # ── Write ─────────────────────────────────────────────────────────────

    def save(self, record: EvaluationRecord) -> None:
        """Append a single evaluation record to the JSONL file."""
        self._append_lines([record])

    def append_batch(self, records: Sequence[EvaluationRecord]) -> None:
        """Atomically append multiple records to the JSONL file."""
        self._append_lines(records)

    def _append_lines(self, records: Sequence[EvaluationRecord]) -> None:
        lines = "\n".join(
            json.dumps(
                r.model_dump(mode="json") | {"_record_version": 2},
                default=str,
            )
            for r in records
        )
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(lines + "\n")
        log_event(logger, event="records_appended", stage="evaluation", status="success", level="DEBUG", n=len(records), path=str(self._path))

    # ── Read ──────────────────────────────────────────────────────────────

    def load(self) -> list[EvaluationRecord]:
        """Load all records from the JSONL file.

        Malformed lines are skipped with a warning.
        """
        if not self._path.exists():
            log_event(logger, event="records_loaded", stage="evaluation", status="success", n=0, path=str(self._path))
            return []
        records: list[EvaluationRecord] = []
        skipped = 0
        with open(self._path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    raw: dict[str, Any] = json.loads(line)
                    raw.pop("_record_version", None)
                    records.append(EvaluationRecord(**raw))
                except Exception:
                    skipped += 1
                    log_event(logger, event="malformed_line_skipped", stage="evaluation", status="failed", level="WARNING", line=line_no, reason="malformed line")
        log_event(logger, event="records_loaded", stage="evaluation", status="success", n=len(records), skipped=skipped)
        return records

    def load_recent(self, limit: int = 50) -> list[EvaluationRecord]:
        """Return the most recent *limit* records (by file order)."""
        all_records = self.load()
        return all_records[-limit:]

    # ── Delete ────────────────────────────────────────────────────────────

    def clear(self) -> None:
        """Delete the JSONL file entirely.  Idempotent."""
        self._path.unlink(missing_ok=True)
        log_event(logger, event="repository_cleared", stage="evaluation", status="success", path=str(self._path))

    # ── Export ────────────────────────────────────────────────────────────

    def export_json(self) -> str:
        """Export all records as a JSON array string."""
        records = self.load()
        data = [r.model_dump(mode="json") for r in records]
        return json.dumps(data, indent=2, default=str)

    def export_csv(self) -> str:
        """Export all records as a CSV string."""
        records = self.load()
        if not records:
            return ""
        output = io.StringIO()
        fields = list(records[0].model_dump(mode="json").keys())
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for r in records:
            writer.writerow(r.model_dump(mode="json"))
        return output.getvalue()

    def export_records_to_json(self, records: Sequence[EvaluationRecord]) -> str:
        """Export a specific list of records as a JSON array string."""
        data = [r.model_dump(mode="json") for r in records]
        return json.dumps(data, indent=2, default=str)

    # ── Statistics ────────────────────────────────────────────────────────

    def statistics(self) -> dict[str, Any]:
        """Return a snapshot of aggregate statistics over all records.

        Returns:
            Dict with keys: ``total``, ``schema_valid``, ``schema_valid_rate``,
            ``failed``, ``failure_rate``, ``repair_attempted``,
            ``repair_success_rate``, ``avg_latency_ms``, ``avg_retries``,
            ``total_field_accuracy``, ``last_updated``.
        """
        records = self.load()
        total = len(records)
        if total == 0:
            return {"total": 0}
        valid = sum(1 for r in records if r.schema_valid)
        failed = total - valid
        repaired = [r for r in records if r.repair_attempted]
        repair_success = sum(1 for r in repaired if r.repair_success)
        fa_values = [r.field_accuracy for r in records if r.field_accuracy is not None]
        return {
            "total": total,
            "schema_valid": valid,
            "schema_valid_rate": round(valid / total, 4),
            "failed": failed,
            "failure_rate": round(failed / total, 4),
            "repair_attempted": len(repaired),
            "repair_success_rate": round(repair_success / len(repaired), 4) if repaired else 0.0,
            "avg_latency_ms": round(sum(r.latency_ms for r in records) / total, 2),
            "avg_retries": round(sum(r.retry_count for r in records) / total, 4),
            "avg_field_accuracy": round(sum(fa_values) / len(fa_values), 4) if fa_values else 0.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def latest(self, n: int = 10) -> list[EvaluationRecord]:
        """Return the last *n* records (convenience alias for ``load_recent``)."""
        return self.load_recent(limit=n)

    def summary(self) -> dict[str, Any]:
        """Return a lightweight summary dict (deprecated — use ``statistics``)."""
        return self.statistics()
