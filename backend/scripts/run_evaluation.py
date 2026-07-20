"""
Evaluation Harness (MVP) — PRD Section 5 & Section 13 (Success Metrics).

Runs the full pipeline (preprocess -> extract with repair loop) across every
ticket in data/tickets_sample.jsonl, and produces:
  - reports/evaluation_results.json   (raw per-ticket results)
  - reports/evaluation_report.md      (human-readable summary — this IS your
                                        "short report explaining failure modes
                                        and mitigations" deliverable)

Requires GROQ_API_KEY set in .env — this makes real Groq calls.

Run:
    python scripts/run_evaluation.py
"""

import json
import sys
import time
from collections import Counter
from pathlib import Path

# Ensure the project root (parent of scripts/) is on sys.path so `app` resolves
# regardless of how this script is invoked (by path, by module, from any cwd).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import GROQ_MODEL
from app.database.database import create_database
from app.database.repository import ExtractionRepository, RawTicketRepository
from app.extraction import extract_ticket, _get_client
from app.preprocessing import preprocess

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "tickets_sample.jsonl"
RESULTS_PATH = Path(__file__).resolve().parent.parent / "reports" / "evaluation_results.json"
REPORT_PATH = Path(__file__).resolve().parent.parent / "reports" / "evaluation_report.md"


def load_tickets():
    with open(DATA_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main():
    tickets = load_tickets()
    client = _get_client()

    results = []
    print(f"Running extraction on {len(tickets)} real tickets...\n")

    for i, ticket in enumerate(tickets, 1):
        pre = preprocess(ticket["raw_text"])
        result = extract_ticket(ticket["ticket_id"], pre.clean_text, client=client)

        raw_repo = RawTicketRepository()
        ext_repo = ExtractionRepository()
        raw_repo.save(
            ticket_id=ticket["ticket_id"],
            raw_text=ticket["raw_text"],
            cleaned_text=pre.clean_text,
            language=pre.language,
        )
        ext_repo.save(
            ticket_id=ticket["ticket_id"],
            structured_json=result.data.model_dump() if result.data else None,
            schema_valid=result.success,
            retry_count=result.retry_count,
            failure_category=result.failure_category,
            latency_seconds=result.latency_seconds,
        )

        status = "PASS" if result.success else f"FAIL ({result.failure_category})"
        print(f"[{i}/{len(tickets)}] ticket_id={ticket['ticket_id']} -> {status} "
              f"(retries={result.retry_count}, {result.latency_seconds:.2f}s)")

        results.append({
            "ticket_id": ticket["ticket_id"],
            "success": result.success,
            "retry_count": result.retry_count,
            "failure_category": result.failure_category,
            "latency_seconds": result.latency_seconds,
            "attempts": [
                {"attempt": a.attempt_number, "success": a.success, "error": a.error}
                for a in result.attempts
            ],
            "output": result.data.model_dump() if result.data else None,
        })

        time.sleep(0.2)  # light pacing to stay comfortably under Groq free-tier rate limits

    # ---- Aggregate metrics ----
    total = len(results)
    valid = sum(r["success"] for r in results)
    schema_valid_rate = valid / total if total else 0

    first_pass = sum(1 for r in results if r["success"] and r["retry_count"] == 0)
    repaired = sum(1 for r in results if r["success"] and r["retry_count"] > 0)
    failed = total - valid

    retry_counts = Counter(r["retry_count"] for r in results if r["success"])
    failure_categories = Counter(r["failure_category"] for r in results if not r["success"])
    avg_latency = sum(r["latency_seconds"] for r in results) / total if total else 0

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # ---- Human-readable report (the PRD-required failure-mode writeup) ----
    lines = [
        "# Evaluation Report — Constrained Structured Extraction at Scale",
        "",
        f"**Sample size:** {total} real customer support tickets "
        f"(source: public GitHub dataset, genuine tickets — not synthetic)",
        f"**Model:** {GROQ_MODEL} via `instructor`",
        f"**Max repair retries per ticket:** 3",
        "",
        "## Headline Metrics",
        f"- **Schema-valid rate:** {valid}/{total} = **{schema_valid_rate:.1%}**",
        f"- First-pass valid (no repair needed): {first_pass}/{total} ({first_pass/total:.1%})" if total else "",
        f"- Valid after repair loop: {repaired}/{total} ({repaired/total:.1%})" if total else "",
        f"- Failed after exhausting retries: {failed}/{total} ({failed/total:.1%})" if total else "",
        f"- Average latency per ticket: {avg_latency:.2f}s",
        "",
        "## Retry Distribution (successful extractions)",
    ]
    for retries in sorted(retry_counts):
        lines.append(f"- {retries} {'retry' if retries == 1 else 'retries'}: {retry_counts[retries]} tickets")

    lines += ["", "## Failure Mode Breakdown"]
    if failure_categories:
        for cat, count in failure_categories.most_common():
            lines.append(f"- **{cat}**: {count} tickets")
    else:
        lines.append("- No unrecovered failures in this run.")

    lines += [
        "",
        "## Mitigations Applied",
        "- **Model-Driven Repair Loop**: on validation failure, the exact Pydantic error is "
        "fed back to the model in a follow-up turn (not a generic retry), asking it to fix "
        "only the specific violation.",
        "- **Strict enum closure**: the system prompt instructs the model to always pick the "
        "closest valid enum value rather than emit free text, reducing `enum_mismatch` failures.",
        "- **PII stripping pre-extraction**: emails/phones/zips are redacted before the LLM call, "
        "which also reduces spurious entity hallucination in `entities.*`.",
        "- **Zero regex fallback**: tickets that exhaust all repair attempts are flagged "
        "`extraction_failed` with a logged category rather than force-fit into the schema.",
        "",
        "## Notes for Round 2 write-up",
        "- This report is generated fresh on every run of `scripts/run_evaluation.py` — "
        "regenerate before the demo so numbers are current.",
        "- `_reference` fields in `tickets_sample.jsonl` (ticket_type/priority/status from the "
        "original dataset) can be used for a lightweight field-level accuracy spot-check, "
        "though they aren't a 1:1 ground-truth match for this schema.",
    ]

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"Schema-valid rate: {schema_valid_rate:.1%}  ({valid}/{total})")
    print(f"Report written to: {REPORT_PATH}")
    print(f"Raw results written to: {RESULTS_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
