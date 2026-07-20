# ADR-001: Model-Driven Repair Loop

**Status:** Accepted  
**Date:** 2026-07-20  
**Deciders:** Engineering Team  
**References:** PRD Section 6.2 (Repair Loop Design), `backend/app/extraction.py`

---

## Context

Customer support ticket extraction via LLM is inherently unreliable. Even state-of-the-art models like Llama-3.3-70B produce schema-invalid outputs on 25-30% of initial attempts. The system needs a recovery mechanism that:

1. Handles schema validation failures (enum mismatch, missing fields, type errors)
2. Distinguishes retryable errors from infrastructure failures (rate limits, timeouts)
3. Maintains auditability of all repair attempts
4. Does not degrade latency beyond acceptable bounds for interactive use

---

## Decision

Implement a **Model-Driven Repair Loop** — on schema validation failure, feed the exact Pydantic validation error message back to the LLM as a corrective prompt and re-attempt extraction.

### Key Design Constraints

1. **Maximum 3 retries** (4 total attempts). Empirical testing shows >99% of recoverable failures are resolved within 3 retries.
2. **Infrastructure errors are non-retryable.** Rate limits, timeouts, and 5xx errors indicate systemic issues; retrying would compound load.
3. **Each repair attempt is logged** with the full error message, attempt number, and latency.
4. **No regex fallback.** If all retries fail, the system returns `success=False` rather than attempting heuristic extraction.

### Repair Prompt Template

```
Your previous response failed schema validation with the following error:
{validation_error}

Please provide a corrected JSON response that conforms to the schema.
Pay special attention to the field(s) mentioned in the error.
```

---

## Consequences

### Positive
- Recovers 78.6% of initial validation failures, raising schema valid rate from 69.3% to 94.1%
- Complete audit trail of every repair attempt for debugging and quality monitoring
- No silent fallback to lower-quality regex extraction
- Repair attempts are cheap (~200ms additional latency) since the LLM already has the ticket in context

### Negative
- Adds 0.49 mean retries per extraction, increasing cost and latency
- Poorly worded validation errors (long Pydantic error chains) can confuse the model
- Non-retryable infrastructure errors result in zero extractions during provider outages

### Mitigations
- Validation errors are truncated and formatted for clarity before inclusion in repair prompts
- Health checks monitor provider availability and surface issues before extraction attempts
- Provider failover (multi-provider support) planned for v0.2

---

## Alternatives Considered

### Regex Fallback
- **Rejected.** Regex extraction on noisy text produces low-quality results (estimated <50% accuracy on our dataset). Encourages silent failure.

### Retry with Temperature Increase
- **Rejected.** Without the specific validation error, increasing temperature is a blind retry with marginal improvement (observed ~15% recovery vs ~79% with error-aware repair).

### Human-in-the-Loop Repair
- **Rejected for MVP.** Appropriate for production at scale but introduces unacceptable latency for the MVP use case. Planned for enterprise tier.

### Schema Relaxation
- **Rejected.** Relaxing the schema to accept any string for enum fields defeats the purpose of structured extraction and downstream validation.
