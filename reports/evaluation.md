# Evaluation Report — ExtractIQ Engine

**Authors:** Engineering Team  
**Date:** 2026-07-20  
**Version:** 0.1.0  
**Status:** Technical Report — Methodology Documented; Metrics Incomplete

---

## Abstract

We present a structured evaluation methodology for ExtractIQ Engine, a production-oriented system for extracting structured information from noisy customer support ticket text. The system combines an LLM-based extraction engine with a Model-Driven Repair Loop that iteratively corrects schema validation errors by feeding Pydantic validation errors back to the model.

**Status:** Schema-valid extraction rate is measurable (91.9% on 37 tickets). Field accuracy, category F1, token usage, and cost analysis are **not yet computed** — the golden annotation pipeline has not been connected to the evaluation harness.

---

## 1. Introduction

Customer support ticket classification and structured data extraction is a critical component of enterprise service desk operations. Modern LLMs offer unprecedented capability for understanding unstructured text, but their output is inherently non-deterministic and frequently violates strict schema constraints required for downstream automated processing.

We introduce ExtractIQ Engine, a system that addresses this gap through three key design decisions: (1) structured output enforcement via the `instructor` library, (2) a Model-Driven Repair Loop that treats schema validation errors as first-class signals for iterative correction, and (3) a confidence scoring mechanism that quantifies extraction reliability.

This report describes the evaluation methodology and presents **currently measurable** results. Sections marked with **Not Yet Measured** describe the intended approach but lack the required data at this time.

---

## 2. Dataset

### 2.1 Source and Composition

The evaluation dataset comprises:
- **10 annotated tickets** with golden JSON output (`backend/tests/golden/*.json`)
- **37 real Groq extractions** with no ground truth comparison
- **15 adversarial stress tickets** extracted via Featherless AI

### 2.2 Category Distribution

**Not Yet Measured.** Category labels are present in the 10 golden tickets (2 billing, 4 technical, 2 shipping, 1 account, 1 product) but were not recorded in evaluation runs. Full category distribution requires connecting golden data to the evaluation harness.

### 2.3 Adversarial Subsets

15 adversarial stress tickets designed to probe system limitations:

| Stress Type | Count | Description |
|-------------|-------|-------------|
| Very noisy | 3 | ALL CAPS, repeated phrases, tangents, frustrated |
| Broken/gibberish | 3 | Non-lexical text, base64 images, incoherent |
| Mixed language | 3 | Code-switching between English and French |
| Multi-issue | 3 | Multiple distinct problems in one ticket |
| Long ticket | 3 | > 1,000 words with complex timelines |

### 2.4 Annotation Process

10 tickets were annotated with schema-compliant JSON:

- **Rater profile:** Engineering team member with domain knowledge of customer support operations
- **Annotation tool:** Structured JSON template with per-field validation
- **Inter-rater agreement:** **Not computed** — only one annotator produced golden files
- **Number of annotated tickets:** 10 (target: 75+ for statistical significance)

---

## 3. Evaluation Methodology

### 3.1 Metrics

We report the following metrics where data is available:

**Schema Compliance:**
- **Schema Valid Rate (SVR):** Proportion of extractions passing `TicketExtraction.model_validate()` without error
- **Measured:** 91.9% on 37 Groq tickets

**Field Accuracy:**
- **Status: Not Yet Measured.** The `_compute_field_accuracy` function in `collector.py` is implemented and tested.
- **Procedure:** Compare extracted fields against golden annotation using exact match (scalar) and set equality (list)
- **Prerequisite:** Pass golden `TicketExtraction` as `expected` parameter to `EvaluationCollector.add()`

**Repair Efficacy:**
- **Status: Not Yet Measured.** The repair loop was not triggered during the 37-ticket Groq run.
- **Procedure:** Compare schema-valid rate before and after repair loop across all tickets

**Latency:**
- Wall-clock time from API request receipt to response dispatch
- **Measured:** P50=0.71s, P90=3.62s on 37 Groq tickets

**Classification Metrics:**
- **Status: Not Yet Measured.** Requires golden category labels.
- **Procedure:** Compare `predicted_category` against `expected_category`; compute macro F1

### 3.2 Procedure

1. Each ticket is submitted to the `/v1/extract` endpoint via programmatic API call
2. The system performs extraction with up to 3 automatic repair attempts
3. The raw extraction result, all repair attempts, latency, and metadata are recorded
4. Schema validity is computed immediately via Pydantic validation
5. Field-level accuracy: **not yet computed** (requires golden data connection)
6. Results are aggregated and reported

### 3.3 Hardware

| Component | Specification |
|-----------|---------------|
| CPU | Intel Xeon Platinum 8375C, 4 vCPUs @ 2.90 GHz |
| RAM | 16 GB |
| Storage | 256 GB SSD |
| Network | 1 Gbps |
| OS | Ubuntu 22.04 LTS |
| Python | 3.12.4 |

---

## 4. Results

### 4.1 Schema Compliance

**Measured from 37 Groq tickets:**

| Metric | Value |
|--------|-------|
| Initial SVR (attempt 1) | 91.9% |
| Final SVR (after repair) | 91.9% (no repairs triggered) |
| Improvement | 0 pp |

Note: The repair loop was not exercised in this run. The "Initial SVR" equals the "Final SVR" because all 34 successful extractions succeeded on the first attempt. To measure repair loop efficacy, a dataset with schema-violating edge cases is required.

### 4.2 Field Accuracy

**Not Yet Measured.** This section describes the intended methodology and will be populated once the golden annotation pipeline is connected.

**Intended approach:**

| Field | Accuracy | Precision | Recall | F1 |
|-------|----------|-----------|--------|----|
| ticket_id | — | — | — | — |
| customer.name | — | — | — | — |
| customer.account_id | — | — | — | — |
| issue.category | — | — | — | — |
| issue.subcategory | — | — | — | — |
| issue.product_or_service | — | — | — | — |
| issue.urgency | — | — | — | — |
| sentiment | — | — | — | — |
| entities.order_ids | — | — | — | — |
| entities.dates_mentioned | — | — | — | — |
| entities.amounts_mentioned | — | — | — | — |
| requested_action | — | — | — | — |
| resolution_status | — | — | — | — |
| **Macro average** | — | — | — | — |

**How to compute:**

```python
from app.evaluation.collector import EvaluationCollector
from app.evaluation.repository import EvaluationRepository
from app.schema import TicketExtraction
import json

collector = EvaluationCollector()
golden = TicketExtraction(**json.load(open("tests/golden/billing_ticket_expected_output.json")))
result = extract_ticket(...)  # Run extraction
record = collector.add(result, expected=golden)
record.field_accuracy  # Now populated
```

### 4.3 Classification Results

**Not Yet Measured.** No expected_category values exist in the evaluation records. The method for computing category classification metrics is:

| Category | Precision | Recall | F1 |
|----------|-----------|--------|----|
| billing | — | — | — |
| technical | — | — | — |
| shipping | — | — | — |
| account | — | — | — |
| product | — | — | — |
| other | — | — | — |

### 4.4 Repair Loop Analysis

**Not Yet Measured.** The repair loop was not triggered in the 37-ticket Groq run.

**Intended analysis:**

| Attempt | Success Count | Cumulative SVR |
|---------|---------------|----------------|
| Attempt 1 (initial) | — | — |
| Attempt 2 (1st repair) | — | — |
| Attempt 3 (2nd repair) | — | — |
| Attempt 4 (3rd repair) | — | — |

**Repair Success by Error Type:** Requires logging repair outcomes per validation error type.

### 4.5 Latency

**Measured from 37 Groq tickets:**

| Metric | Value |
|--------|-------|
| P50 | 0.71 s |
| P90 | 3.62 s |
| P95 | 3.72 s |
| Mean | 1.47 s |
| Std Dev | 1.55 s |
| Min | 0.12 s |
| Max | 6.24 s |

Note: These values are from a single run on 37 relatively short tickets. Larger, more complex tickets may exhibit higher latencies. A 75+ ticket benchmark across diverse ticket lengths is needed for robust latency characterization.

### 4.6 Cost Analysis

**Not Yet Measured.** Cost computation requires:
1. Token counting (not yet implemented — recommend `tiktoken`)
2. Per-provider pricing model
3. Amortization over repair attempts

**Intended approach:**

| Component | Per Ticket | Per 1K Tickets |
|-----------|------------|----------------|
| Initial LLM call | — | — |
| Repair calls (avg) | — | — |
| Infrastructure | — | — |
| **Total** | — | — |

---

## 5. Discussion

### 5.1 Schema Compliance

The 91.9% schema-valid rate demonstrates that the `instructor` library, combined with Pydantic validation, produces mostly compliant output from zero-shot LLM extraction. The three failures were due to model misinterpretation of the schema (validation errors) and a rate limit hit.

### 5.2 Repair Loop

The repair loop was not exercised in this evaluation run. Common causes for this include:
- The evaluated tickets were straightforward enough for the LLM to handle in one attempt
- The `instructor` library's structured output enforcement reduces schema violations
- A dedicated adversarial test set is needed to exercise the repair path

### 5.3 Latency

P50 of 0.71s is well within interactive-use bounds. The P90 of 3.62s is acceptable but may benefit from optimistic UI updates or progress indicators.

---

## 6. Limitations

1. **Dataset size:** 37 evaluation tickets is insufficient for statistical significance in percentile measurements.
2. **No golden comparison:** Field accuracy and category F1 cannot be reported until the golden annotation pipeline is connected.
3. **Single-provider evaluation:** Results are from Groq's `llama-3.3-70b-versatile`. Performance with other providers is not evaluated.
4. **Limited language support:** The dataset is overwhelmingly English.
5. **No human baseline:** We do not compare against human extraction accuracy.
6. **Zero-shot only:** No few-shot prompting was used.

---

## 7. Future Work

1. **Connect golden pipeline:** Implement comparison against `backend/tests/golden/*.json`
2. **Scaled evaluation:** Expand to 500+ tickets
3. **Multi-provider comparison:** Benchmark across Groq, OpenAI, Anthropic, Featherless
4. **Human baseline:** Collect human extraction accuracy on a subset
5. **Ablation studies:** Measure contribution of repair loop, prompt design, schema strictness
6. **Few-shot evaluation:** Assess improvement from in-domain examples

---

## 8. Conclusion

ExtractIQ Engine achieves 91.9% schema-valid extraction rate on a 37-ticket benchmark with 0.71s median latency. Field-level accuracy, category F1, token usage, and cost analysis remain **not yet measured** pending connection of the golden annotation pipeline. The evaluation infrastructure is in place and well-tested; the remaining work is to wire the golden dataset into `EvaluationCollector.add()` calls and re-run the evaluation.

---

## References

1. Pydantic v2 Documentation. https://docs.pydantic.dev/latest/
2. instructor Library. https://github.com/instructor-ai/instructor
3. Groq API Documentation. https://console.groq.com/docs
4. Llama 3 Model Card. Meta AI, 2024.
5. Mitchell et al., "Model Cards for Model Reporting." FAccT 2019.
6. Ribeiro et al., "Beyond Accuracy: Behavioral Testing of NLP Models with CheckList." ACL 2020.
