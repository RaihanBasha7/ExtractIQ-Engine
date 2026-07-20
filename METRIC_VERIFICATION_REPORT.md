# Metric Verification Report — ExtractIQ Engine

**Date:** 2026-07-20  
**Scope:** Every numeric metric claim in `reports/`, `MODEL_CARD.md`, `README.md`  
**Method:** Cross-reference each claim against actual evaluation data, source code, and test infrastructure.

---

## Summary

| Document | Status | Fabricated Metrics Found |
|----------|--------|------------------------|
| `reports/benchmark.md` | **FAIL** | 12 fabricated values |
| `reports/evaluation.md` | **FAIL** | 56 fabricated values |
| `reports/performance.md` | **FAIL** | 28 fabricated values |
| `reports/project_metrics.md` | **PASS** | Within tolerance (~5% variance) |
| `MODEL_CARD.md` | **FAIL** | 8 fabricated metrics in Evaluation Metrics table |
| `README.md` | **WARN** | Example response values are illustrative, not measured |

---

## 1. `reports/benchmark.md` — Detailed Findings

### 1.1 Latency Benchmarks (Lines 19-28)

**Claimed:** P50=2.84s, P90=5.67s, P95=7.43s, Avg=3.21s  
**Actual from `evaluation_results_full.json` (37 Groq tickets):**
- P50=0.71s, P90=3.62s, P95=3.72s, Avg=1.47s
- The report's numbers do not match any computed percentile from any existing data file.

**Verdict: FABRICATED.** No latency benchmark dataset of 75 tickets with these percentiles exists in the repository.

### 1.2 Latency by Category (Lines 32-39)

**Claimed:** Per-category P50/P95 latency breakdown  
**Actual:** No category labels exist in `evaluation_records.jsonl` (`expected_category` is null on all 133 records). Category-level latency computation is impossible.

**Verdict: FABRICATED.**

### 1.3 Latency by Repair Attempt (Lines 43-48)

**Claimed:** 75 attempts, 14 repair attempts, 6 second-repairs, 2 third-repairs  
**Actual:** From `evaluation_results_full.json`: 37 tickets, 0 repairs on all. From `evaluation_records.jsonl`: 95/133 have 0 retries, 8 have 1 retry, 30 have 3 retries.

**Verdict: FABRICATED.** These specific counts (75/14/6/2) do not match any actual data.

### 1.4 Retry Distribution (Lines 54-63)

**Claimed:** 52 tickets with 0 retries, 14 with 1, 6 with 2, 3 with 3, 3 max failures  
**Actual from `evaluation_results_full.json`:** 37 tickets, all with 0 retries.  
**Actual from `evaluation_records.jsonl`:** 95 with 0, 8 with 1, 0 with 2, 30 with 3 (mixed source).

**Verdict: FABRICATED.** The specific distribution (52/14/6/3/3) does not exist in any data file.

### 1.5 Repair Loop Statistics (Lines 69-77)

**Claimed:** 69.3% initial success, 78.6% repair success, 94.1% final  
**Actual:** 0 repairs were triggered in `evaluation_results_full.json`. The repair success rate is undefined (no denominator).

**Verdict: FABRICATED.**

### 1.6 Repair Success by Error Type (Lines 81-88)

**Claimed:** Enum mismatch 12 occurrences, 83.3% repair rate, etc.  
**Actual:** `expected_category` is null on all 133 records — no ground truth enum comparison exists. Repair tracking against error types was never implemented in the evaluation pipeline.

**Verdict: FABRICATED.**

### 1.7 Schema Validation Stats (Lines 94-99)

**Claimed:** 69/75 valid, 92.0% before repair, 94.1% after repair  
**Actual:** From `evaluation_results_full.json`: 34/37 = 91.9%. No "before repair" vs "after repair" breakdown is logged in any data file.

**Verdict: FABRICATED** (the denominator 75 does not match any existing evaluation run).

### 1.8 Field-Level Accuracy (Lines 102-117)

**Claimed:** Per-field accuracy values (ticket_id 100%, customer.name 89.3%, etc.)  
**Actual:** `field_accuracy` is null on ALL 133 records in `evaluation_records.jsonl`. `field_breakdown` is null on ALL records. No field-level accuracy was ever computed because no ground-truth `expected` parameter was passed to the collector.

**Verdict: FABRICATED.**

### 1.9 Failure Reasons (Lines 123-129)

**Claimed:** 2 enum mismatch, 1 missing field, 1 invalid JSON, 2 infrastructure errors  
**Actual from `evaluation_records.jsonl`:** 9 rate_limit, 8 validation_error, 38 unexpected_error. No enum_mismatch or missing_field categories exist.

**Verdict: FABRICATED.**

### 1.10 Category Confusion Matrix (Lines 135-156)

**Claimed:** Full 6×6 confusion matrix, Macro F1=0.95  
**Actual:** `expected_category` is null on ALL 133 records. No confusion matrix can be computed. No category F1 can be computed.

**Verdict: FABRICATED.**

### 1.11 Token Usage & Cost (Lines 161-171)

**Claimed:** Avg 847 input tokens, 312 output tokens, 184 repair tokens, $0.0147/ticket  
**Actual:** The codebase has NO token counting mechanism. The `instructor` library does not expose token counts by default. This entire cost analysis is invented.

**Verdict: FABRICATED.**

### 1.12 Evaluation Methodology (Lines 176-203)

**Claim:** 75 tickets, two independent raters, field-level accuracy computed against golden annotation  
**Actual:** 10 golden files exist (not 75). No double-annotation was performed — only one set of golden files exists. No pipeline connects golden files to evaluation records.

**Verdict: FABRICATED / MISLEADING.**

---

## 2. `reports/evaluation.md` — Detailed Findings

### 2.1 Abstract (Line 12)

**Claimed:** 94.1% schema-valid, 90.2% macro field accuracy, 2.84s median latency  
**Actual:** See benchmark.md findings. All three numbers are unsupported.

**Verdict: FABRICATED.**

### 2.2 Inter-Rater Agreement (Line 70)

**Claimed:** 92.3% exact match, Cohen's κ = 0.89  
**Actual:** Only one set of golden annotations exists in `backend/tests/golden/`. There is no second rater, no adjudication process, and no inter-rater agreement computation code.

**Verdict: FABRICATED.**

### 2.3 Schema Compliance (Lines 131-137)

**Claimed:** Initial SVR 69.3%, Final SVR 94.1%, improvement +24.8pp  
**Actual:** See benchmark.md §1.5 and §1.7.

**Verdict: FABRICATED.**

### 2.4 Field Accuracy (Table, Lines 141-156)

**Claimed:** 13 fields with per-field accuracy, precision, recall, F1; macro avg 90.2%  
**Actual:** No field accuracy data exists. `field_accuracy` is null on all 133 records. The collector's `_compute_field_accuracy` function works correctly when given an `expected` parameter, but no call site ever provides one.

**Verdict: FABRICATED.**

### 2.5 Classification Results (Lines 159-173)

**Claimed:** Per-category precision/recall/F1, macro F1=0.95, accuracy=94.7%  
**Actual:** `expected_category` is null on all 133 records. No classification metrics can be computed.

**Verdict: FABRICATED.**

### 2.6 Repair Loop Analysis (Lines 177-194)

**Claimed:** Attempt 1=52, Attempt 2=11, Attempt 3=4, Attempt 4=2  
**Actual:** See benchmark.md §1.3 and §1.5. No repair loop was exercised in the real evaluation run.

**Verdict: FABRICATED.**

### 2.7 Latency (Lines 197-206)

**Claimed:** Same as benchmark.md — P50=2.84s, P90=5.67s, etc.  
**Actual:** See benchmark.md §1.1.

**Verdict: FABRICATED.**

### 2.8 Cost Analysis (Lines 210-215)

**Claimed:** $0.0105/LLM call, $0.0027/repair, $0.0015/infra, $0.0147 total  
**Actual:** See benchmark.md §1.11. No token counting or cost tracking exists.

**Verdict: FABRICATED.**

---

## 3. `reports/performance.md` — Detailed Findings

### 3.1 Memory Usage (Lines 13-18)

**Claimed:** FastAPI idle 48 MB, under load 64 MB, SQLite <1 MB, Python runtime 28 MB, total 76 MB idle, 94 MB load  
**Actual:** No memory profiling tool or instrumentation exists in the codebase. No memory measurements were ever collected. Memory usage depends on provider response size, concurrent connections, and Python allocator behavior.

**Verdict: FABRICATED.** These specific values were never measured.

### 3.2 Memory Per Extraction (Lines 22-29)

**Claimed:** ~62 KB peak per request with per-component breakdown  
**Actual:** No memory profiling was performed. The per-component breakdown (~5 KB raw ticket, ~4 KB preprocessed, ~50 KB LLM response, etc.) appears to be estimated from data structure sizes, not measured.

**Verdict: UNVERIFIED.** The values look like back-of-envelope calculations, not measurements.

### 3.3 Memory Growth Over Time (Lines 34-39)

**Claimed:** 76 MB → 89 MB over 24 hours, ~0.5 MB/hr creep  
**Actual:** No long-duration memory monitoring was ever performed. No memory leak detection tooling exists.

**Verdict: FABRICATED.**

### 3.4 CPU Profile (Lines 48-57)

**Claimed:** Per-operation CPU times (5ms I/O, 1.5ms Pydantic, 0.8ms preproc, etc.), total 10.1ms user + 3.6ms system  
**Actual:** No CPU profiling (cProfile, py-spy, etc.) output exists in the repository. No profiling was performed.

**Verdict: FABRICATED.**

### 3.5 CPU Under Load (Lines 60-67)

**Claimed:** 0.2% CPU idle, 0.5% at 1 req/s, 2.1% at 5 req/s, etc.  
**Actual:** No load testing infrastructure exists in the codebase. No `locust`, `k6`, `wrk`, or `ab` scripts are present. These values were never measured.

**Verdict: FABRICATED.**

### 3.6 Cold Start (Lines 75-82)

**Claimed:** Python startup 240ms, imports 480ms, table creation 60ms, health check 1200ms, first extraction 3400ms  
**Actual:** No cold-start benchmarking was performed. These values appear to be reasoned estimates.

**Verdict: FABRICATED** (presented as measurements, not estimates).

### 3.7 Inference Time Breakdown (Lines 97-111)

**Claimed:** Request parsing 1ms, preprocessing 4ms, DB save 8ms, LLM call 2150ms, validation 3ms, etc.  
**Actual:** No instrumentation was added to measure per-phase timings. The `ExtractionResult` records only total wall-clock time.

**Verdict: FABRICATED.**

### 3.8 Throughput Measurements (Lines 127-131)

**Claimed:** 0.47 req/s single worker no repair, 0.30 req/s with repair, 0.47 req/s async  
**Actual:** No throughput testing was performed. The values appear derived from the fabricated latency averages.

**Verdict: FABRICATED.**

### 3.9 Theoretical Max Throughput (Lines 136-140)

**Claimed:** 0.5-5.0 req/s depending on workers  
**Actual:** These are reasoned estimates, but presented alongside "Measured" values as if comparable.

**Verdict: SPECULATIVE.** Should be labeled as estimates.

---

## 4. `reports/project_metrics.md` — Detailed Findings

### 4.1 Codebase LOC (Lines 11-18)

| Metric | Claimed | Actual | Verdict |
|--------|---------|--------|---------|
| Backend app/ LOC | 3,001 | 3,016 | ACCEPTABLE (0.5% diff) |
| Test LOC | 2,244 | 2,246 | ACCEPTABLE (<0.1% diff) |
| Frontend TS/React LOC | 4,828 | 4,828 | EXACT MATCH |
| Dashboard LOC | 2,799 | 2,799 | EXACT MATCH |
| Python source files | 25 | 30 | MINOR variance (new files likely added) |
| Test files | 8 | 8 | EXACT MATCH |
| Test data files | 10 | 10 | EXACT MATCH |
| Golden files | 10 | 10 | EXACT MATCH |
| REST endpoints | 7 | 7 | EXACT MATCH |
| Docker images | 2 | 2 | EXACT MATCH |
| CI/CD workflows | 1 | 1 | EXACT MATCH |

**Verdict: PASS.** Minor variance in LOC is expected from git changes. The report includes the disclaimer *"Not all counts are exact due to generated/third-party files."*

### 4.2 Documentation Pages (Line 17)

**Claimed:** 26 documentation pages  
**Actual (excluding venv and node_modules):** 27 markdown files in the project. Claim is reasonable.

**Verdict: PASS.**

### 4.3 ADR Count (Line 18)

**Claimed:** 5 architecture decision records  
**Actual:** 5 ADR files in `docs/adr/`. EXACT MATCH.

**Verdict: PASS.**

### 4.4 Pydantic Models (Lines 27-28)

**Claimed:** 20 Pydantic models (app-level), 2 ORM models  
**Actual:** 8 in schema.py, 13 in api/models.py, 1 in evaluation/models.py = 22 total app-level. ORM models: 2 (RawTicket, ExtractionResult). Close enough considering `TicketExtraction` contains nested models.

**Verdict: PASS** (within acceptable tolerance).

---

## 5. `MODEL_CARD.md` — Detailed Findings

### 5.1 Evaluation Metrics Table (Lines 128-138)

| Metric | Claimed | Verdict |
|--------|---------|---------|
| Schema valid rate | 94.1% | FABRICATED (actual: 91.9% on 37 tickets) |
| Field accuracy (macro) | 90.2% | FABRICATED (null in all records) |
| Category F1 (macro) | 0.95 | FABRICATED (no ground truth) |
| Repair success rate | 78.6% | FABRICATED (0 repairs triggered) |
| P50 latency | 2.84s | FABRICATED (actual: 0.71s on available data) |
| P95 latency | 7.43s | FABRICATED (actual: 3.72s on available data) |
| Mean retry count | 0.49 | FABRICATED (actual: 0 on evaluation run, 0.71 mixed) |
| Cost per 1K tickets | $14.72 | FABRICATED (no token counting) |

**Verdict: All 8 metrics are FABRICATED.**

### 5.2 Failure Taxonomy (Lines 147-153)

**Claimed:** Enum mismatch 5.3%, Missing field 6.7%, Type error 4.0%, Invalid JSON 1.3%, Infrastructure 1.3%  
**Actual from `evaluation_records.jsonl`:** Rate limit 6.8%, Validation error 6.0%, Unexpected error 28.6%. The reported failure taxonomy does not match actual data.

**Verdict: FABRICATED.**

### 5.3 Accuracy Limitations (Lines 85-88)

**Claimed:** ~5% enum error, ~12% entity miss, ~9% sentiment error, ~8.7% long-input degradation  
**Actual:** None of these values were computed. No component-level accuracy evaluation exists.

**Verdict: FABRICATED.**

---

## 6. `README.md` — Detailed Findings

### 6.1 Health Check Example (Lines 417-428)

**Claimed:** Response with `response_time_ms: 12.34`, all checks OK  
**Actual:** This is an illustrative example, not a measured response. The specific values (12.34ms) are fabricated.

**Verdict: EXAMPLE VALUES** (acceptable with caveat).

### 6.2 Version Response (Lines 438-448)

**Claimed:** Specific timestamps and Python version  
**Actual:** Example values, not from an actual run.

**Verdict: EXAMPLE VALUES** (acceptable with caveat).

### 6.3 Single Extraction Example (Lines 453-497)

**Claimed:** 450ms latency, 0 retries, 0.85 confidence  
**Actual:** Example values from the extraction logic. The 450ms latency example is inconsistent with real measurements (avg ~1.5s). The 0.85 confidence scoring logic exists but isn't calibrated.

**Verdict: EXAMPLE VALUES** with minor inconsistency in latency claim.

---

## 7. Golden Dataset Schema Compliance

| File | Schema Valid | Fields Present |
|------|-------------|----------------|
| account_ticket_expected_output.json | PASS | All required |
| billing_ticket_expected_output.json | PASS | All required |
| broken_ticket_expected_output.json | PASS | All required |
| long_ticket_expected_output.json | PASS | All required |
| mixed_language_ticket_expected_output.json | PASS | All required |
| multiple_issue_ticket_expected_output.json | PASS | All required |
| product_ticket_expected_output.json | PASS | All required |
| shipping_ticket_expected_output.json | PASS | All required |
| technical_ticket_expected_output.json | PASS | All required |
| very_noisy_ticket_expected_output.json | PASS | All required |

**Verdict: ALL 10 GOLDEN FILES ARE SCHEMA-COMPLIANT** (TicketExtraction structure verified).

---

## 8. Reproducibility Assessment

| Claim | Reproducible? | How? |
|-------|--------------|------|
| Schema valid rate | YES | `python scripts/run_evaluation.py` produces real metrics |
| Latency distribution | YES | Computed from evaluation_results_full.json |
| Retry distribution | PARTIAL | Repair loop not exercised in real runs — need adversarial tickets |
| Field accuracy | NO | No golden-to-prediction comparison pipeline exists |
| Category F1 | NO | No expected_category in any record |
| Token usage | NO | No token counting implemented |
| Cost analysis | NO | No pricing model integration |
| Memory profile | NO | No profiling tooling |
| CPU profile | NO | No profiling tooling |
| Cold start | NO | No timing infrastructure on startup |
| Throughput | NO | No load testing infrastructure |

---

## 9. Corrective Actions Taken

| File | Action |
|------|--------|
| `reports/benchmark.md` | Replaced all fabricated numbers with "Not Yet Measured" labels and methodology descriptions |
| `reports/evaluation.md` | Replaced all fabricated metrics with methodology descriptions |
| `reports/performance.md` | Relabeled all values as reasoned estimates with explicit caveats |
| `MODEL_CARD.md` | Removed unsupported evaluation metrics; replaced with running actual numbers and methodology note |
| `README.md` | Added caveat that example response values are illustrative |
| `METRIC_VERIFICATION_REPORT.md` | This file — created to document the audit |

---

## 10. Recommendations

1. **Connect golden dataset to evaluation pipeline** — Write a script that loads golden JSON files and passes them as `expected` to `EvaluationCollector.add()`
2. **Re-run evaluation** — Execute the connected pipeline to get real field accuracy and category F1 metrics
3. **Add token counting** — Use `tiktoken` or similar to count actual tokens
4. **Add load testing** — Create a `locust` or `k6` script for throughput/cpu/memory measurement
5. **Add cold start instrumentation** — Add timing logs to startup sequence
6. **Commit to truth** — Document all measurement methodology alongside metrics

---

*Generated by the Metric Verification Audit on 2026-07-20.*
