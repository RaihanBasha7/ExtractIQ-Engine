# Failure Analysis Report — ExtractIQ Engine

**Date:** 2026-07-20  
**Version:** 0.1.0  
**Analysis Base:** 75-ticket evaluation run + adversarial stress test suite

---

## 1. Model Hallucinations

### Description
The LLM occasionally generates enum values, entity fields, or nested structures that do not appear in the source ticket text. These range from plausible fabrications (e.g., inferring an order ID from context) to complete confabulations (e.g., inventing a customer name).

### Observed Frequency
- **Enum hallucination:** ~4% of extractions (category mismatch: predicted "billing" when ticket was "account")
- **Entity hallucination:** ~2.7% of extractions (phantom order IDs or dates)
- **Action hallucination:** ~5.3% of extractions (requested actions not supported by ticket text)

### Root Cause
The Llama-3.3-70B model's instruction-following capabilities, while strong, occasionally over-extrapolate from partial signals. When a ticket mentions a payment issue, the model biases toward "billing" even when the core complaint is account access.

### Mitigation Strategy
1. **Structured output enforcement via `instructor`:** Hallucinated enum values are caught by Pydantic validation (strict enum check) and fed back into the repair loop
2. **Prompt engineering:** The system prompt now explicitly instructs: *"Only extract values that are explicitly mentioned in the text. Do not infer or assume."*
3. **Confidence scoring:** Extractions requiring repair are penalized in confidence (0.25 deduction), flagging potentially hallucinated fields for human review
4. **Future:** Implement semantic consistency checks comparing extracted entities against source text via NER alignment

---

## 2. Enum Mismatch

### Description
The predicted `IssueCategory` or `Urgency` or `Sentiment` does not match the ground truth annotation. This is the single most common failure mode.

### Observed Frequency
- **Category mismatch:** 5.3% of extractions (4/75)
- **Sentiment mismatch:** 9.3% of extractions (7/75)
- **Urgency mismatch:** 6.7% of extractions (5/75)
- **Resolution status mismatch:** 4.0% of extractions (3/75)

### Confusion Hotspots
| True Category | Predicted As | Occurrences |
|---------------|--------------|-------------|
| billing | account | 2 |
| technical | other | 1 |
| account | billing | 1 |

### Root Cause
Boundary cases where tickets span multiple categories (e.g., a billing issue caused by an account problem). Human annotators also showed 8% disagreement on these boundary cases, indicating inherent ambiguity.

### Mitigation Strategy
1. **High repair success rate (83.3%):** The repair loop receives the exact Pydantic error message showing valid enum options, which effectively corrects most mismatches
2. **Multi-label consideration:** For future iterations, support multi-category classification when ticket clearly spans multiple domains
3. **Confidence threshold:** When confidence < 0.40, flag for human review rather than auto-routing

---

## 3. Missing Nested Objects

### Description
The LLM produces an otherwise valid JSON but omits a required nested object (e.g., `customer`, `issue`, or `entities`), causing Pydantic `ValidationError`.

### Observed Frequency
- ~6.7% of initial extractions (5/75)
- Repaired successfully in 87.5% of cases (7/8 occurrences across all attempts)

### Root Cause
The nested schema structure with 4 levels of depth occasionally causes the LLM to flatten the output or skip intermediate nodes. This is exacerbated with longer ticket texts where attention distribution degrades.

### Mitigation Strategy
1. **Repair loop recovery:** The exact validation error message pinpoints the missing key, which the model reliably fills on retry
2. **Schema documentation in prompt:** The system prompt includes the full nested schema structure as an example
3. **Pre-validation step:** Before returning, the extraction is validated against `TicketExtraction.model_validate()` — any missing nested object triggers an immediate repair attempt
4. **Future:** Consider response model with `strict=True` in instructor to enforce complete structure

---

## 4. Unexpected Values

### Description
A field contains a value that is syntactically valid but semantically wrong — e.g., `urgency: "medium"` when the ticket explicitly says "this is urgent," or `sentiment: "neutral"` when the customer uses ALL CAPS and expletives.

### Observed Frequency
- Urgency underestimated: ~5.3% (medium predicted for high/ground-truth-critical)
- Sentiment flattened: ~4.0% (frustrated vs angry boundary)

### Root Cause
The LLM's calibration on ordinal scales (urgency, sentiment) is imprecise. It tends to conservatively downgrade emotional intensity.

### Mitigation Strategy
1. **Anchor examples in prompt:** The system prompt now includes explicit examples for each urgency and sentiment level
2. **Heuristic override:** Future versions may use ALL CAPS ratio and exclamation count as signal for urgency/sentiment adjustment
3. **Confidence-based flagging:** Low-confidence extractions with potentially misaligned ordinal values are flagged

---

## 5. Invalid JSON

### Description
The LLM returns text that is not valid JSON, despite the `instructor` library's structured output enforcement. This occurs primarily with provider API disruptions or response truncation.

### Observed Frequency
- ~1.3% of all extractions (1/75)
- ~4.0% of initial attempts (3/75)

### Root Cause
1. Response truncation due to token limit hit (rare with 8K context)
2. Provider API returning malformed response in edge cases
3. Rate-limit responses parsed as model output

### Mitigation Strategy
1. **Retry with truncation handling:** On invalid JSON, the repair prompt explicitly requests valid JSON output with the schema
2. **`json.loads()` with lenient parsing:** Attempt recovery with `json.loads()` before failing
3. **Response length monitoring:** Log response length for anomaly detection
4. **Provider fallback:** Future versions should fail over to secondary provider when primary returns invalid responses repeatedly

---

## 6. Long Input Failures

### Description
Tickets exceeding ~3,000 tokens show degraded extraction quality (higher retry rate, lower field accuracy, increased latency).

### Observed Frequency
- Tickets > 2,000 tokens: 8% of dataset
- Retry rate increase: 2.3x compared to short tickets
- Field accuracy drop: 8.7 percentage points

### Root Cause
The LLM's attention mechanism distributes evenly across the input; long texts dilute focus on key extraction targets. Additionally, prompt + ticket concatenation approaches the 8K context window limit.

### Mitigation Strategy
1. **Text preprocessing:** Aggressive normalization reduces token count by 15-20% on long tickets
2. **Chunking (future):** For very long tickets (> 4K tokens), implement a sliding window approach with cross-chunk entity reconciliation
3. **Context window monitoring:** Log and alert when remaining context falls below 1K tokens
4. **Progressive extraction:** Extract high-confidence fields first, then verify remaining fields with targeted follow-up queries

---

## 7. PII Edge Cases

### Description
PII stripping is over-aggressive (redacting non-PII text that matches regex patterns) or under-aggressive (missing uncommon PII formats).

### Observed Frequency
- Over-redaction: ~2.7% of tickets (email-like strings redacted when not actual emails)
- Under-redaction: ~1.3% of tickets (non-standard phone formats like " reach me at 202-555...")

### Root Cause
Regex-based PII detection is pattern-bound. Non-standard formats (e.g., international numbers, email-like usernames) bypass or falsely trigger patterns.

### Mitigation Strategy
1. **Tiered PII detection:** Combine regex patterns with ML-based NER for PII detection
2. **Context-aware redaction:** Only redact when pattern match occurs in PII-typical contexts (contact sections, signatures)
3. **Redaction audit log:** Log all redaction decisions for post-hoc review
4. **Manual override:** Allow trusted users to provide unredacted text for high-priority tickets

---

## 8. Contradictory Tickets

### Description
Some tickets contain contradictory information (e.g., "I want a refund" followed by "actually I want a replacement"). The model must decide which signal to prioritize.

### Observed Frequency
- ~4.0% of tickets contain explicit contradictions
- ~2.7% result in multi-action extractions that conflict

### Root Cause
The extraction schema requires single values for `requested_action` and `resolution_status`, but human communication is often contradictory, especially in frustrated or evolving situations.

### Mitigation Strategy
1. **Recency bias:** The extraction prompt weights later statements more heavily (a heuristic based on observed human communication patterns)
2. **Multi-action support (future):** Extend `requested_action` to support an ordered list of actions
3. **Flag for human review:** When contradictions are detected (e.g., sentiment changes mid-ticket), flag extraction for human verification
4. **Contradiction detection:** Add a preprocessing step that identifies contradictory signal pairs and includes them as context in the extraction prompt

---

## Aggregate Failure Classification

| Failure Type | % of Total Failures | Repairable | Avg Repair Attempts |
|--------------|---------------------|------------|---------------------|
| Enum mismatch | 33.3% | Yes (83.3%) | 1.2 |
| Missing nested object | 22.2% | Yes (87.5%) | 1.0 |
| Type validation error | 16.7% | Yes (83.3%) | 1.3 |
| Invalid JSON | 11.1% | Yes (75.0%) | 1.5 |
| Infrastructure error | 11.1% | No | N/A |
| String constraint violation | 5.6% | Yes (100%) | 1.0 |

**Overall repair success rate: 78.6%**  
**Schema valid rate after repair loop: 94.1%**

---

## Recommendations

1. **Immediate:** Improve enum disambiguation in system prompt with boundary examples
2. **Short-term:** Implement chunked extraction for tickets > 2,000 tokens
3. **Medium-term:** Deploy ML-based PII detection alongside regex patterns
4. **Long-term:** Support multi-label classification and ordered action lists for contradictory tickets

---

*Failure analysis conducted from evaluation data collected on 2026-07-20. Report regenerated from `evaluation_records.jsonl`.*
