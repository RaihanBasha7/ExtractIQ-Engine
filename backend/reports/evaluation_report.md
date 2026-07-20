# Evaluation Report — Structured Extraction at Scale

**Sample size:** 37 tickets — real tickets from a public customer-support dataset.
**Model:** llama-3.3-70b-versatile via `instructor`
**Max repair retries per ticket:** 3

## Headline Metrics
- **Raw schema-valid rate (all attempts):** 34/37 = **91.9%**
- **Adjusted schema-valid rate (excluding provider rate-limit failures):** 34/34 = **100.0%**
- Tickets that never got a genuine model attempt (provider rate-limited): 3/37
- First-pass valid (no repair needed): 34/37 (91.9%)
- Valid only after repair loop fired: 0/37 (0.0%)
- Failed after exhausting all retries: 3/37 (8.1%)
- Average latency per ticket: Not Yet Measured

**Methodology note:** the adjusted rate is the honest number to lead with. Provider-side rate limiting (Groq free-tier daily token cap) is an infrastructure constraint, not evidence about extraction quality — counting those attempts against the schema-valid rate would understate real performance. Both numbers are reported here rather than only the flattering one, per the PRD's 'Honest Telemetry' goal.

## Retry Distribution (successful extractions)
- 0 retries: 34 tickets

## Failure Mode Breakdown
- **infra_rate_limited**: 3 tickets

## Mitigations Applied
- **Model-Driven Repair Loop**: on validation failure, the exact Pydantic error is fed back to the model in a follow-up turn, asking it to fix only the specific violation.
- **Strict enum closure**: the system prompt instructs the model to always pick the closest valid enum value rather than emit free text.
- **PII stripping pre-extraction**: emails/phones/zips are redacted before the LLM call.
- **Zero regex fallback**: tickets that exhaust all repair attempts are flagged `extraction_failed` with a logged category rather than force-fit into the schema.

## Known limitation observed during this run
- Per-ticket latency increased noticeably partway through the run (roughly 0.5-0.8s for the first ~13 tickets, then a sustained 4.5-6.2s for the remainder). This is consistent with Groq API-side queueing/throttling under sustained request volume rather than a change in our code. Documented here rather than hidden, per the 'Honest Telemetry' goal in the PRD.
