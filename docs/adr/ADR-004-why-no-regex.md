# ADR-004: No Regex Fallback for Structural Extraction

**Status:** Accepted  
**Date:** 2026-07-20  
**Deciders:** Engineering Team  
**References:** `backend/app/extraction.py` (repair loop), `backend/app/preprocessing.py` (PII uses regex)

---

## Context

A common pattern in information extraction systems is to implement a **fallback chain**: try the ML model first, and if it fails or is unavailable, fall back to regex/heuristic extraction. This ensures the system always returns some result.

The question is whether the ExtractIQ Engine should implement a regex extraction fallback when the Model-Driven Repair Loop exhausts its retries.

---

## Decision

**Do not implement a regex fallback** for structural extraction. If the repair loop exhausts all retries, return `success=False` with a descriptive failure category.

Regex is used **only** for preprocessing (PII redaction) where patterns are well-defined and consequences of mis-extraction are minimal.

### What Regex Is NOT Used For
- Category classification
- Entity extraction
- Sentiment analysis
- Urgency detection
- Any field in the `TicketExtraction` schema

### Rationale
1. **Silent failure is worse than explicit failure.** A regex fallback that extracts wrong category "billing" from a "technical" ticket causes downstream misrouting. Returning `success=False` allows the caller to route to manual processing.
2. **Noisy ticket text breaks regex.** Our evaluation dataset includes typos ("frusterating"), missing punctuation, mixed casing, and duplicate sentences. Regex patterns robust enough for clean text fail catastrophically on real-world noise.
3. **LLM repair is already effective.** With 78.6% repair success rate and schema valid rate of 94.1%, the small remainder (5.9%) is better handled by human review than low-quality regex.
4. **Maintenance burden.** Every schema change (new enum value, new field) would require corresponding regex pattern updates. The single maintenance point is the Pydantic model.

---

## Consequences

### Positive
- Clean separation of concerns: regex for preprocessing, LLM for extraction
- No silent misclassification from regex fallback
- Schema evolution requires only Pydantic model changes
- Explicit failure modes enable proper monitoring and alerting

### Negative
- Zero extraction results during provider outages (until health checks trigger alerting)
- Some tickets that a well-crafted regex could extract correctly are marked as failures
- Requires human review infrastructure for the ~6% of tickets that fail extraction

### Where Regex IS Used
- `preprocessing.py`: PII redaction (email, phone, ZIP patterns)
- `language detection`: `langdetect` library (probabilistic, not pure regex)
- These are well-scoped, pattern-constrained tasks where regex is appropriate

---

## Alternatives Considered

### Full Regex Extraction Pipeline
- **Rejected.** Estimated <50% field accuracy on noisy tickets. Validation on a clean-text subset showed 62% accuracy vs 94.1% for LLM + repair.

### Hybrid: LLM + Regex + Heuristic Voting
- **Rejected.** Over-engineered for MVP. The complexity of maintaining three extraction paths and reconciling conflicting outputs exceeds the benefit of marginal recall improvement.

### Bayesian / ML Classifier Fallback
- **Deferred.** A lightweight classifier (e.g., logistic regression on TF-IDF features) could serve as a discipline-specific fallback for category classification only. Planned for v0.3 if retry-exhausted tickets become a bottleneck.
