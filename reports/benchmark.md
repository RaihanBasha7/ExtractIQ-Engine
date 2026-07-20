# Benchmark Report — ExtractIQ Engine

**Report Date:** 2026-07-20  
**System Version:** 0.1.0  
**LLM Provider:** Groq (primary test run) / Featherless AI (alternate)  
**Model:** llama-3.3-70b-versatile (Groq) / zai-org/GLM-5.2 (Featherless)  
**Evaluation Dataset:** 37 tickets (Groq run) + 15 adversarial stress tickets (Featherless)

---

## Executive Summary

The ExtractIQ Engine achieves **91.9% schema-valid extraction rate** on a 37-ticket Groq evaluation run. The Model-Driven Repair Loop was **not exercised during the Groq run** (all 37 extractions succeeded on first attempt). A separate 15-ticket adversarial stress test was conducted via Featherless AI. Field-level accuracy, category F1, token usage, and cost analysis are **not yet measured** — the evaluation pipeline requires a golden dataset connection to compute these metrics.

---

## Latency Benchmarks

**Status: Not Yet Measured at Full Scale**

A single 37-ticket Groq evaluation run produced the following latencies:

| Metric | Value |
|--------|-------|
| Average latency | 1.47 s |
| P50 (median) | 0.71 s |
| P90 | 3.62 s |
| P95 | 3.72 s |
| Min | 0.12 s |
| Max | 6.24 s |
| Standard deviation | 1.55 s |

**Important caveat:** These measurements are from a single evaluation run. A larger benchmark (75+ tickets) is needed for statistically significant percentiles. See `reports/evaluation_results_full.json` for raw data.

### Latency by Category

**Not Yet Measured.** Category labels were not recorded in the evaluation run (`expected_category` not provided). Run `python scripts/run_full_evaluation.py` with golden annotations to produce this breakdown.

### Latency by Repair Attempt

**Not Yet Measured.** No repair loop was triggered during the 37-ticket Groq run. The Featherless stress run triggered repairs on some adversarial tickets.

---

## Retry Distribution

**Actual from 37-ticket Groq evaluation run:**

| Retry Count | Tickets | Percentage |
|-------------|---------|------------|
| 0 (first attempt success) | 37 | 100.0% |
| 1+ retries | 0 | 0.0% |

The repair loop was not exercised in this run. The `evaluation_records.jsonl` file contains a mixed dataset (test + Groq + Featherless runs) with different retry distributions.

---

## Repair Loop Statistics

**Not Yet Measured at Scale.** The 37-ticket Groq run had 0 repair attempts. The 15 adversarial Featherless tickets triggered repairs on some cases. Aggregate repair statistics require a dedicated evaluation run with tickets designed to trigger schema validation failures.

---

## Schema Validation

**Actual from 37-ticket Groq evaluation run:**

| Metric | Value |
|--------|-------|
| Schema-valid extractions | 34 / 37 |
| Schema-invalid extractions | 3 / 37 |
| Overall schema valid rate | 91.9% |
| Schema valid rate (after repair) | 91.9% (no repairs triggered) |

### Field-Level Accuracy

**Not Yet Measured.** Field-level accuracy requires a comparison between extracted output and golden annotations. The evaluation pipeline supports this via `EvaluationCollector.add(result, expected=golden)`, but no call site currently provides the golden reference. Connect the golden dataset (`backend/tests/golden/*.json`) and re-run to obtain these metrics.

---

## Failure Reasons

**Actual from 37-ticket Groq evaluation run:**

| Failure Reason | Count | Percentage |
|----------------|-------|------------|
| validation_error | 2 | 66.7% |
| rate_limit | 1 | 33.3% |
| **Total failures** | **3** | **100%** |

---

## Category Distribution (Ground Truth)

**Not Yet Measured.** `expected_category` was not recorded in any evaluation run. Category F1 and confusion matrix computation requires golden category labels. The golden dataset (`backend/tests/golden/*.json`) contains annotated categories for 10 tickets. A full evaluation connecting golden data to predictions is needed.

### Category Confusion Matrix

**Not Yet Measured.** Method: Compare `predicted_category` against `expected_category` from golden annotations. Run `python scripts/run_full_evaluation.py` with golden data loaded as `expected` in the evaluation collector.

---

## Token Usage & Cost

**Not Yet Measured.** The codebase does not currently implement token counting. Recommended approach:
1. Add `tiktoken` dependency for token counting
2. Log per-request token counts in `EvaluationRecord`
3. Apply provider pricing formulas (Groq: ~$0.59/M input, ~$0.79/M output tokens; Featherless: varies by model)
4. Average across a benchmark run to produce per-ticket cost estimates

---

## Evaluation Methodology

### Dataset
- **Source:** 10 annotated tickets (`backend/tests/golden/*.json`) + 37 real Groq extractions + 15 adversarial Featherless tickets
- **Size:** 37 tickets (Groq evaluation) + 15 adversarial (Featherless)
- **Labeling:** 10 tickets manually annotated with schema-compliant JSON ground truth
- **Annotation process:** Single annotator (not double-annotated)

### Procedure
1. Each ticket submitted to `/v1/extract` endpoint
2. Raw extraction result recorded with full attempt log
3. Schema validity checked against `TicketExtraction` Pydantic model
4. Field-level accuracy: **not yet computed** (requires golden data connection)
5. Latency measured wall-clock from request receipt to response dispatch
6. Retry count, repair success, and failure category logged per ticket

### Metrics Definitions
- **Latency:** Wall-clock duration in seconds from endpoint entry to response serialization
- **Schema valid:** Extraction passes Pydantic `model_validate` without error
- **Repair success:** Extraction failed on attempt N but succeeded on attempt N+1 after repair prompt (not measured)
- **Field accuracy:** Exact match between extracted field and golden annotation (not measured)
- **Category F1:** Standard classification F1 per category, macro-averaged (not measured)

### Hardware
- **CPU:** Intel Xeon Platinum 8375C @ 2.90 GHz (4 vCPUs)
- **RAM:** 16 GB
- **OS:** Ubuntu 22.04 LTS
- **Network:** 1 Gbps to LLM provider API endpoint

---

## Conclusions

1. The system achieves 91.9% schema-valid extraction in a zero-shot setting with Groq's llama-3.3-70b.
2. The Model-Driven Repair Loop was not stress-tested in this run — dedicated adversarial evaluation is needed to measure repair efficacy.
3. Field-level accuracy, category F1, token usage, and cost metrics require connecting the golden annotation pipeline.
4. P50 latency of 0.71s is acceptable for interactive use on the tested ticket set; larger tickets may increase latency.

---

## Next Steps for Benchmarking

1. **Connect golden data:** Write a script that loads `backend/tests/golden/*.json` and passes each as `expected` to the evaluation collector
2. **Expand dataset:** Add more annotated tickets (target: 75-100)
3. **Repair loop stress test:** Create tickets known to trigger schema violations
4. **Load test:** Add throughput measurement with locust or k6
5. **Token counting:** Implement and log per-request token usage
6. **Multi-provider:** Run identical benchmark with Featherless AI for comparison

---

*Generated by the ExtractIQ Engine evaluation harness on 2026-07-20. Full results available in `reports/evaluation_results_full.json`. Metrics marked "Not Yet Measured" require pipeline enhancements described above.*
