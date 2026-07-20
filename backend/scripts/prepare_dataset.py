"""
Builds data/tickets_sample.jsonl — a real, noisy 60-ticket sample from the raw CSV.

Why 60, not 50: the PRD/problem statement requires 50+ samples; a small buffer covers
any tickets that turn out to be empty/unusable after cleaning.

Run:
    python scripts/prepare_dataset.py
"""

import csv
import json
import random
from pathlib import Path

RAW_CSV = Path(__file__).resolve().parent.parent / "data" / "raw_customer_support_tickets.csv"
OUT_JSONL = Path(__file__).resolve().parent.parent / "data" / "tickets_sample.jsonl"

SAMPLE_SIZE = 60
SEED = 42


def build_raw_text(row: dict) -> str:
    """
    Reconstruct a realistic, noisy raw support message the way it would actually arrive —
    combining subject + description + a name/email, which our preprocessing step must
    then clean/redact. This intentionally keeps the messiness (placeholder tokens like
    {product_purchased}, inconsistent punctuation) rather than pre-cleaning it.
    """
    parts = [
        f"From: {row['Customer Name']} <{row['Customer Email']}>",
        f"Subject: {row['Ticket Subject']}",
        "",
        row["Ticket Description"].replace("{product_purchased}", row["Product Purchased"]),
    ]
    return "\n".join(p for p in parts if p is not None)


def main():
    with open(RAW_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Filter out rows with unusably short descriptions
    rows = [r for r in rows if r.get("Ticket Description") and len(r["Ticket Description"]) > 40]

    random.seed(SEED)
    sample = random.sample(rows, SAMPLE_SIZE)

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSONL, "w", encoding="utf-8") as out:
        for row in sample:
            record = {
                "ticket_id": row["Ticket ID"],
                "raw_text": build_raw_text(row),
                # Ground-truth-ish reference fields kept for optional field-level accuracy checks
                # (PRD Section 5: "Measure field-level accuracy against hand-labeled ground truth").
                # These are NOT passed to the LLM — only used for post-hoc comparison if you choose to hand-verify.
                "_reference": {
                    "ticket_type": row.get("Ticket Type"),
                    "priority": row.get("Ticket Priority"),
                    "status": row.get("Ticket Status"),
                },
            }
            out.write(json.dumps(record) + "\n")

    print(f"Wrote {SAMPLE_SIZE} real tickets to {OUT_JSONL}")


if __name__ == "__main__":
    main()
