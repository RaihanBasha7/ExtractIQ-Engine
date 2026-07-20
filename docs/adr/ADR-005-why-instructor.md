# ADR-005: Instructor Library for Structured LLM Output

**Status:** Accepted  
**Date:** 2026-07-20  
**Deciders:** Engineering Team  
**References:** `backend/app/extraction.py`, `backend/app/schema.py`

---

## Context

The core technical challenge of the ExtractIQ Engine is reliably producing structured JSON output from an unstructured LLM. Without structured output enforcement, the LLM may:
- Return valid JSON that does not conform to the expected schema
- Return JSON with incorrect field names or nesting
- Return hallucinated fields not in the schema
- Return plain text when JSON was requested

The system needs a mechanism that:
1. Enforces the Pydantic schema at the LLM API call level
2. Provides error messages that distinguish schema violations from API failures
3. Supports retry with error context
4. Is provider-agnostic (supports both Groq and OpenAI-compatible APIs)

---

## Decision

Use the **`instructor`** library (via `instructor.from_groq()` and `instructor.from_openai()`) for structured output extraction from LLM calls.

### How It Works
Instructor patches the LLM client to:
1. Send the Pydantic schema as a JSON schema in the API request
2. Request JSON mode or function-calling mode depending on provider capabilities
3. Parse the response into the Pydantic model
4. Raise a `ValidationError` (with field-level detail) on schema violation

### Provider Support
```python
# Groq (primary)
client = instructor.from_groq(Groq(api_key=...))

# OpenAI-compatible (Featherless AI, fallback)
client = instructor.from_openai(OpenAI(api_key=..., base_url=...))
```

---

## Consequences

### Positive
- **Provider abstraction:** The same extraction logic works with Groq, OpenAI, Azure OpenAI, Anthropic, and other providers via the appropriate instructor patch
- **Schema-native:** Works directly with Pydantic models — no intermediate schema representation
- **Error granularity:** `ValidationError` from instructor contains field-level details that feed directly into the repair loop
- **Streaming support:** Instructor supports streaming mode for lower-latency extraction
- **Active maintenance:** Well-maintained library with 5K+ GitHub stars and regular releases

### Negative
- **Dependency risk:** Instructor is a third-party library. Breaking changes in the instructor API would require extraction logic updates.
- **Provider-specific behavior:** Function-calling mode (used by Groq) and JSON mode (used by OpenAI) have subtly different behavior. The extraction quality can vary slightly between providers even with the same model.
- **Limited customization:** Instructor's internal prompt construction is opaque. Debugging extraction failures requires understanding both instructor internals and LLM behavior.

### Edge Cases
1. **Response too short:** Instructor may parse a truncated response as valid JSON, passing validation with missing data
2. **Provider non-support:** Some providers/models do not support function calling. Instructor's fallback to JSON mode may produce lower-quality results.
3. **Type coercion:** Instructor may coerce types (e.g., string "123" to int 123) in ways that surprise downstream consumers

---

## Alternatives Considered

### Manual JSON Mode (no library)
- **Rejected.** Without instructor, the system would need to:
  1. Construct the JSON schema manually
  2. Parse the LLM response with `json.loads()`
  3. Validate with Pydantic separately
  4. Construct error messages for retry manually
  This duplicates instructor's functionality with more code and less reliability.

### LangChain Output Parsers
- **Rejected.** LangChain's `PydanticOutputParser` provides similar functionality but introduces the entire LangChain dependency tree for a single feature. Instructor is more lightweight and focused.

### OpenAI Structured Outputs (beta)
- **Rejected for MVP.** OpenAI's native structured outputs (response_format) are provider-locked and still in beta. Instructor abstracts over this capability when available, with fallback for providers that don't support it.

### Custom JSON Repair Logic
- **Rejected.** Building custom logic to repair malformed JSON (e.g., trailing commas, unquoted keys, missing closing braces) is fragile and poorly tested. Instructor + Pydantic provides battle-tested validation.

---

## Usage Pattern

```python
from instructor import from_groq
from groq import Groq

client = from_groq(Groq(api_key=settings.GROQ_API_KEY))

try:
    extraction = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        response_model=TicketExtraction,
        messages=[{"role": "user", "content": prompt}],
    )
except ValidationError as e:
    # Feed into repair loop
    ...
```

This pattern is used consistently across all extraction paths in `backend/app/extraction.py`.
