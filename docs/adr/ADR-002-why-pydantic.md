# ADR-002: Pydantic v2 for Schema Definition and Validation

**Status:** Accepted  
**Date:** 2026-07-20  
**Deciders:** Engineering Team  
**References:** `backend/app/schema.py`, `backend/app/api/models.py`

---

## Context

The system requires a schema definition framework that serves dual purposes:
1. **Structured output enforcement** — Instruct the LLM to produce output matching a specific schema (via `instructor` library)
2. **Runtime validation** — Validate the LLM's output before returning to the caller

The framework must support nested objects, enums, optional fields with defaults, and strict validation modes.

---

## Decision

Use **Pydantic v2** (via `pydantic` package) as the single schema definition and validation framework across the entire application stack.

### Usage in the System
- **Extraction schema** (`schema.py`): `TicketExtraction` with nested `Customer`, `Issue`, `Entities` models
- **API models** (`api/models.py`): Request/response models for all endpoints
- **Evaluation models** (`evaluation/models.py`): `EvaluationRecord` for tracking extraction quality
- **Configuration** (`settings.py`): `pydantic-settings` for validated environment configuration

---

## Consequences

### Positive
- **Single source of truth:** The same model class is used for LLM structured output, API validation, and database serialization
- **`instructor` compatibility:** The `instructor` library natively uses Pydantic models for response schema — no adapter layer needed
- **Rich error messages:** Pydantic `ValidationError` provides field-level error details that are fed into the repair loop
- **Strict mode:** `model_config = {"extra": "forbid"}` prevents hallucinated fields from passing validation
- **Serialization:** `.model_dump_json()` provides clean JSON serialization without boilerplate

### Negative
- **Performance overhead:** Pydantic validation adds ~1-3ms per extraction (negligible relative to 2-3s LLM latency)
- **Schema migration:** Changes to the Pydantic model require coordinated updates to prompts, database models, and frontend types
- **Nested complexity:** Deeply nested validation errors (4+ levels) produce verbose error messages that must be trimmed for the repair prompt

---

## Alternatives Considered

### dataclasses
- **Rejected.** No runtime validation, no enum enforcement, no serialization support. Would require a separate validation layer.

### JSON Schema
- **Rejected.** `instructor` does not support JSON Schema directly. Would need a Pydantic adapter anyway, adding indirection.

### msgspec
- **Rejected.** Faster than Pydantic but has incomplete `instructor` integration and smaller ecosystem.

### TypedDict
- **Rejected.** No runtime validation at all. Completely unsuitable for LLM output validation.

---

## Migration Path

The extraction schema is already at version 1.0. Schema evolution follows these principles:
- New fields must be `Optional[...]` with `None` default or `list[...]` with empty default
- Enum additions are additive only (never remove values)
- Schema version is recorded in extraction metadata for downstream consumers
