# Model Card — ExtractIQ Engine

**Model Card Version:** 1.0  
**Date:** 2026-07-20  
**Model Type:** Structured Information Extraction System (LLM-based with repair loop)  
**System Version:** 0.1.0

---

## Purpose

ExtractIQ Engine is a structured information extraction system designed to transform unstructured customer support ticket text into a standardized, schema-compliant JSON representation. It is purpose-built for enterprise customer support operations seeking to automate ticket categorization, routing, and analytics.

### Intended Use
- Automatic extraction of structured fields from customer support tickets
- Ticket categorization, routing, and triage in support desk workflows
- Analytics and reporting on support ticket patterns
- Quality assurance and compliance monitoring of support interactions

### Out-of-Scope Use
- Medical or healthcare information extraction (HIPAA compliance not validated)
- Legal document analysis or contract interpretation
- Real-time safety-critical decision making without human review
- Extraction from non-English text (only mixed English/French supported experimentally)
- Personally identifiable information (PII) storage — the system redacts PII, not stores it

---

## Supported Inputs

| Input | Format | Constraints |
|-------|--------|-------------|
| Raw ticket text | UTF-8 plain text | 10 - 10,000 characters |
| Ticket ID | String | Required, used for correlation |
| Language | Auto-detected | Primary: English; Experimental: bilingual (English/French) |

### Preprocessing Applied
- Whitespace normalization
- PII redaction (email, phone, ZIP code)
- Language detection
- Duplicate sentence deduplication (planned for v0.2)

---

## Supported Outputs

The system extracts a `TicketExtraction` object with the following structure:

| Field | Type | Description |
|-------|------|-------------|
| `ticket_id` | string | Unique ticket identifier (passed through) |
| `customer.name` | optional string | Customer name if explicitly mentioned |
| `customer.account_id` | optional string | Account or order ID if mentioned |
| `issue.category` | enum | billing, technical, shipping, account, product, other |
| `issue.subcategory` | optional string | Free-text subcategory |
| `issue.product_or_service` | optional string | Named product or service |
| `issue.urgency` | enum | low, medium, high, critical |
| `sentiment` | enum | frustrated, neutral, satisfied, angry |
| `entities.order_ids` | string list | All mentioned order identifiers |
| `entities.dates_mentioned` | string list | All mentioned dates |
| `entities.amounts_mentioned` | string list | All mentioned monetary amounts |
| `requested_action` | optional string | Explicit customer request |
| `resolution_status` | enum | unresolved, pending, resolved, escalated |

### Confidence Score
A floating-point value [0.10, 1.00] indicating the system's confidence in extraction accuracy, computed from retry count, missing fields, and repair status.

---

## Model Architecture

The system is not a single ML model but a **pipeline**:

1. **Preprocessing Layer:** Regex-based text normalization and PII redaction
2. **LLM Extraction Engine:** `zai-org/GLM-5.2` served via Featherless AI API (default), called through the `instructor` library for structured output enforcement. Groq's `llama-3.3-70b-versatile` is supported as an alternate provider.
3. **Model-Driven Repair Loop:** Up to 3 automatic repair attempts on schema validation failure, feeding exact Pydantic error messages back to the LLM
4. **Confidence Scorer:** Rule-based scoring from retry count, missing fields, and repair status
5. **Persistence Layer:** SQLite for extraction results, JSONL for evaluation records

---

## Known Limitations

### Accuracy Limitations
- **Enum boundary cases:** Not yet measured — category F1 requires golden annotation comparison
- **Entity extraction:** Not yet measured — field-level accuracy pending golden pipeline connection
- **Sentiment calibration:** Not yet measured — requires field-level accuracy analysis
- **Long input degradation:** Not yet measured — requires evaluation across ticket length distribution

### Operational Limitations
- **SQLite backend:** Not suitable for production concurrent access; PostgreSQL required for > 10 req/s
- **Single-worker architecture:** Repair loop runs synchronously; blocks worker during extraction
- **Provider dependency:** Extraction quality depends on Featherless AI API availability and latency (Groq available as alternate)
- **No authentication:** API endpoints currently unprotected; authentication required before production deployment
- **Rate limits:** Free-tier LLM provider accounts have daily token caps; production requires paid tier

### Language Limitations
- **English only** for reliable extraction; bilingual tickets (English + French) supported experimentally with degraded accuracy
- **Code-switching** within a single utterance is not handled
- **Non-Latin scripts** are not supported (Cyrillic, CJK, Arabic, etc.)

---

## Bias Considerations

### Training Data Bias
The underlying LLM (Llama-3.3-70B) was trained primarily on English internet text, which embeds cultural and linguistic biases common to that distribution. These biases may manifest as:
- Better extraction quality for North American naming conventions and address formats
- Lower accuracy for non-Western names and address structures
- Potential misclassification of culturally specific issues

### Evaluation Dataset Bias
Our evaluation dataset, while diverse, is:
- Primarily North American English customer support scenarios
- Over-representative of technology/SaaS support contexts
- Lacking representation from non-English-first customer bases

### Mitigations
1. Regular bias audits on extraction quality across demographic dimensions
2. Dataset expansion with international ticket samples planned for v0.3
3. Confidence score as a signal for potentially biased extractions (lower confidence for out-of-distribution inputs)
4. Human-in-the-loop for edge cases and low-confidence extractions

---

## Evaluation Metrics

### Verified (Measured from 37 Groq tickets)

| Metric | Score | Notes |
|--------|-------|-------|
| Schema valid rate | 91.9% | 34/37 tickets; no repair loop triggered |
| P50 latency | 0.71 s | Wall-clock time, single run |
| P95 latency | 3.72 s | Includes outliers from rate-limit retries |
| Mean retry count | 0.0 | All extractions succeeded on first attempt |

### Not Yet Measured

The following metrics are **not yet available** — they require connecting the golden annotation pipeline:

| Metric | Status | How to Enable |
|--------|--------|---------------|
| Field accuracy (macro) | Pending | Pass golden `TicketExtraction` to `EvaluationCollector.add()` |
| Category F1 (macro) | Pending | Record `expected_category` in evaluation runs |
| Repair success rate | Pending | Run evaluation on adversarial tickets that trigger schema violations |
| Cost per 1K tickets | Pending | Add token counting (`tiktoken`) and apply provider pricing |

Full methodology in `docs/reports/benchmark.md` and `docs/reports/metric_verification_report.md`.

---

## Failure Cases

### Failure Taxonomy (from 37-ticket Groq evaluation run)
| Category | Rate | Description |
|----------|------|-------------|
| Validation error | 5.4% | Schema-compliant JSON not produced after retries |
| Rate limit | 2.7% | Groq free-tier API rate limit exhausted |
| Other | 0.0% | No other failure modes observed in this run |

Note: Failure taxonomy is based on a single 37-ticket evaluation run. A larger, more diverse dataset is needed for statistical characterization.

### High-Impact Failure Modes
1. **Confident wrong category:** Not yet measured — requires golden category comparison
2. **PII leakage:** Not yet measured — requires targeted adversarial testing with non-standard PII formats
3. **Missing critical entity:** Not yet measured — requires field-level accuracy evaluation

Detailed analysis in `docs/reports/failure_analysis.md`.

---

## Future Improvements

| Improvement | Priority | ETA |
|-------------|----------|-----|
| PostgreSQL migration | P0 | v0.2 |
| Authentication & rate limiting | P0 | v0.2 |
| Asynchronous extraction with Celery | P1 | v0.2 |
| Chunked extraction for long tickets | P1 | v0.3 |
| Multi-label category support | P2 | v0.3 |
| ML-based PII detection | P2 | v0.3 |
| Provider failover | P2 | v0.3 |
| International language support | P3 | v0.4 |

---

## Responsible AI Considerations

### Transparency
- All extractions include a confidence score — users can threshold on this for their use case
- Repair attempts are fully logged with the error messages that triggered them
- The system is not a black box: every extraction decision is traceable to the repair log

### Fairness
- We commit to regular bias evaluation as the dataset expands
- Confidence scores serve as an uncertainty signal; users should review low-confidence extractions
- The system is designed to assist, not replace, human judgment in support workflows

### Privacy
- PII is redacted BEFORE any data reaches the LLM provider
- No raw ticket text is persisted to the LLM provider's training data
- Extraction results store only the structured, PII-free representation
- The `.env` file containing API keys has been rotated and is excluded from version control

### Accountability
- Every extraction is identified by a unique `request_id` for auditability
- The evaluation repository (`evaluation_records.jsonl`) maintains a permanent record of extraction quality
- The Model-Driven Repair Loop design explicitly acknowledges that the system makes mistakes and attempts to self-correct

---

## Model Versioning

| Component | Version | Date |
|-----------|---------|------|
| Extraction schema | 1.0 | 2026-07 |
| Confidence algorithm | 1.0 | 2026-07 |
| LLM: zai-org/GLM-5.2 (default) / llama-3.3-70b-versatile (alternate) | 5.2 / 3.3 | Latest |
| instructor library | 1.x | Latest |
| Repair loop logic | 1.0 | 2026-07 |

---

## Contact

For questions about this model card or the ExtractIQ Engine:
- GitHub Issues: https://github.com/shaikraihanbasha/extractiq-engine/issues
- Security: See `security.md`

---

*This model card follows the framework described in Mitchell et al., "Model Cards for Model Reporting" (FAccT 2019).*
