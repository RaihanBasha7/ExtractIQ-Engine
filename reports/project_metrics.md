# Project Metrics — ExtractIQ Engine

**Generated:** 2026-07-20  
**Version:** 0.1.0

---

## Codebase Overview

| Metric | Value |
|--------|-------|
| Total backend LOC (app/) | 3,001 |
| Total test LOC | 2,244 |
| Frontend TypeScript/React LOC | 4,828 |
| Dashboard (Streamlit) LOC | 2,799 |
| Documentation pages | 26 |
| Architecture Decision Records | 5 |
| **Total codebase (excl. vendor)** | **~12,872** |

---

## API & Schema

| Metric | Value |
|--------|-------|
| REST endpoints | 7 |
| Pydantic models (app-level) | 20 |
| ORM models (database) | 2 |
| Enum definitions | 4 |
| Schema definition files | 4 |

### Endpoint Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/version` | Version info |
| POST | `/v1/extract` | Single extraction |
| POST | `/v1/extract/batch` | Batch extraction |
| GET | `/v1/metrics` | Aggregated metrics |
| GET | `/v1/history` | Extraction history |
| GET | `/v1/system` | Combined health + metrics |

### Schema Models

| File | Models |
|------|--------|
| `app/schema.py` | TicketExtraction, Customer, Issue, Entities, IssueCategory, Urgency, Sentiment, ResolutionStatus |
| `app/api/models.py` | ExtractRequest, ExtractResponse, ExtractBatchRequest, ExtractBatchResponse, HealthResponse, HealthCheckDetail, VersionResponse, MetricsResponse, HistoryItem, HistoryResponse, HistoryQueryParams, SystemResponse, RepairAttemptDetail |
| `app/api/error_models.py` | ErrorResponse |
| `app/database/models.py` | RawTicket, ExtractionResult |
| `app/evaluation/models.py` | EvaluationRecord |

---

## Test Infrastructure

| Metric | Value |
|--------|-------|
| Test files | 8 |
| Test tickets (text files) | 10 |
| Golden output files | 10 |
| Test conftest fixtures | 12+ |
| Pytest markers | unit, integration, slow, asyncio |

### Test Files

| File | Lines | Coverage |
|------|-------|----------|
| `test_api.py` | 273 | All endpoints, error handling, request IDs |
| `test_schema.py` | 288 | Enum validation, nested objects, serialization |
| `test_repair_loop.py` | 283 | Repair log, error parsing, retry counting |
| `test_database.py` | 208 | CRUD, metrics aggregation, pagination |
| `test_utilities.py` | 304 | Preprocessing, PII, confidence, logging |
| `test_error_handling.py` | 208 | Invalid bodies, 500s, timeouts |
| `test_integration_mocked.py` | 215 | Full pipeline with mocked LLM |
| `test_evaluation.py` | 228 | Evaluation models, collector, metrics |

### Test Dataset

| Ticket | Category | Special Characteristics |
|--------|----------|------------------------|
| `billing_ticket.txt` | billing | Duplicate charge, refund request, frustrated |
| `technical_ticket.txt` | technical | 503 error, escalation request |
| `shipping_ticket.txt` | shipping | Package not delivered, refund request |
| `product_ticket.txt` | product | Manufacturing defect, warranty claim |
| `account_ticket.txt` | account | Cannot login, account locked |
| `mixed_language_ticket.txt` | shipping | English + French code-switching |
| `broken_ticket.txt` | technical | Gibberish, base64 image, incoherent |
| `very_noisy_ticket.txt` | technical | ALL CAPS, frustrated, UX complaints |
| `multiple_issue_ticket.txt` | billing | 4 distinct issues in one ticket |
| `long_ticket.txt` | technical | 8-ticket history, complex timeline |

---

## Documentation

| Document | Location | Pages (est.) |
|----------|----------|-------------|
| Architecture | `docs/architecture.md` | 8 |
| API Reference | `docs/api.md` | 9 |
| Deployment Guide | `docs/deployment.md` | 7 |
| Workflow Guide | `docs/workflow.md` | 5 |
| API Examples | `docs/api_examples.md` | 7 |
| Security Guide | `docs/security.md` | 6 |
| Observability Guide | `docs/observability.md` | 6 |
| Model Card | `MODEL_CARD.md` | 5 |
| Roadmap | `ROADMAP.md` | 4 |
| ADR-001: Repair Loop | `docs/adr/ADR-001-repair-loop.md` | 2 |
| ADR-002: Why Pydantic | `docs/adr/ADR-002-why-pydantic.md` | 2 |
| ADR-003: SQLite for MVP | `docs/adr/ADR-003-sqlite-for-mvp.md` | 2 |
| ADR-004: Why No Regex | `docs/adr/ADR-004-why-no-regex.md` | 2 |
| ADR-005: Why Instructor | `docs/adr/ADR-005-why-instructor.md` | 2 |
| README | `README.md` | 15 |

---

## Evaluation Reports

| Report | Location | Description |
|--------|----------|-------------|
| Benchmark Report | `reports/benchmark.md` | Latency, retries, cost, methodology |
| Failure Analysis | `reports/failure_analysis.md` | Error taxonomy, root causes, mitigations |
| Performance Report | `reports/performance.md` | Memory, CPU, cold start, throughput |
| Evaluation Report | `reports/evaluation.md` | Full technical evaluation writeup |
| Project Metrics | `reports/project_metrics.md` | This file |

---

## Infrastructure

| Component | Support |
|-----------|---------|
| Docker | Multi-stage Dockerfile |
| Docker Compose | Backend + frontend services |
| CI/CD | GitHub Actions (lint → test → build) |
| Pre-commit | black, isort, flake8, mypy |
| Environment config | pydantic-settings, .env.example |

### Docker

| Service | Dockerfile | Base Image | Port |
|---------|------------|------------|------|
| Backend | `backend/Dockerfile` | python:3.12-slim | 8000 |
| Frontend | `frontend/Dockerfile` | node:20-alpine (build) | 5173 |

### CI Pipeline (`.github/workflows/ci.yml`)

| Job | Steps | Artifacts |
|-----|-------|-----------|
| Lint | black, isort, flake8, mypy | — |
| Test | pytest --cov=app | coverage report |
| Docker | Build, start, health check | docker image |

---

## Configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, tool config |
| `pytest.ini` | Test configuration |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `.editorconfig` | Editor settings |
| `.dockerignore` | Docker build exclusions |
| `.gitignore` | Git exclusions |
| `backend/.env.example` | Environment template |

---

## Summary

| Category | Count |
|----------|-------|
| Python source files | 25 |
| Test files | 8 |
| Test data files | 10 |
| Golden output files | 10 |
| Documentation (md files) | 26 |
| ADR documents | 5 |
| Evaluation reports | 5 |
| REST API endpoints | 7 |
| Pydantic models | 20 |
| ORM models | 2 |
| Docker images | 2 |
| CI/CD workflows | 1 |
| Frontend pages | 8 |
| Lines of code (total) | ~12,872 |

---

*This report is auto-generated from repository analysis. Not all counts are exact due to generated/third-party files.*
