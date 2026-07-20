# ExtractIQ Engine — Roadmap

**Last Updated:** 2026-07-20  
**Current Version:** v0.1.0 (Current MVP)

---

```
v0.1 (MVP) ──→ v0.2 (Production Ready) ──→ v0.3 (Enterprise Scale) ──→ v0.4 (Future AI)
   │                    │                        │                          │
   │  ┌──────────┐      │  ┌────────────┐       │  ┌──────────────┐       │  ┌─────────────┐
   │  │ Core API  │      │  │ Auth &      │       │  │ Async          │       │  │ Multi-       │
   │  │ Extraction│      │  │ Security    │       │  │ Processing     │       │  │ Language     │
   │  │ Pipeline  │      │  │ PostgreSQL  │       │  │ Multi-Provider  │       │  │ Self-        │
   │  │ Repair    │      │  │ Monitoring  │       │  │ Advanced       │       │  │ Improving    │
   │  │ Loop      │      │  │ CI/CD       │       │  │ Analytics      │       │  │ Fine-Tuned   │
   │  └──────────┘      │  └────────────┘       │  └──────────────┘       │  └─────────────┘
   └────── NOW ──────┘  └─── Q3 2026 ──────┘   └─── Q1 2027 ───────┘   └─── Q3 2027 ──────┘
```

---

## Current MVP — v0.1.0 (Released)

| Area | Feature | Status |
|------|---------|--------|
| **Core** | Single-ticket extraction with structured output | ✅ Complete |
| **Core** | Batch extraction (synchronous) | ✅ Complete |
| **Core** | Model-Driven Repair Loop (3 retries) | ✅ Complete |
| **Core** | PII redaction (emails, phones, ZIPs) | ✅ Complete |
| **Core** | Confidence scoring | ✅ Complete |
| **Schema** | TicketExtraction Pydantic model (13 fields) | ✅ Complete |
| **Schema** | 6-category classification | ✅ Complete |
| **Schema** | Sentiment, urgency, resolution status enums | ✅ Complete |
| **API** | 6 REST endpoints (extract, batch, metrics, history, health, version) | ✅ Complete |
| **API** | Request ID and correlation ID propagation | ✅ Complete |
| **API** | Structured error responses | ✅ Complete |
| **Database** | SQLite persistence | ✅ Complete |
| **Database** | Raw ticket and extraction result storage | ✅ Complete |
| **Evaluation** | Evaluation record collection (JSONL) | ✅ Complete |
| **Evaluation** | Metrics calculation | ✅ Complete |
| **Evaluation** | Evaluation scripts (60 + 75 ticket) | ✅ Complete |
| **Logging** | Structured JSON logging | ✅ Complete |
| **Logging** | Repair attempt logging | ✅ Complete |
| **Frontend** | React dashboard with 8 pages | ✅ Complete |
| **Frontend** | Extraction, batch, playground, analytics, health, history | ✅ Complete |
| **Dashboard** | Streamlit analytics dashboard | ✅ Complete |
| **DevOps** | Docker multi-stage build | ✅ Complete |
| **DevOps** | Docker Compose (backend + frontend) | ✅ Complete |
| **DevOps** | GitHub Actions CI (lint → test → docker) | ✅ Complete |
| **DevOps** | Pre-commit hooks (black, isort, flake8, mypy) | ✅ Complete |
| **Docs** | Architecture documentation | ✅ Complete |
| **Docs** | API reference | ✅ Complete |
| **Docs** | Deployment guide | ✅ Complete |
| **Docs** | Workflow documentation | ✅ Complete |
| **Docs** | ADRs (5 architecture decisions) | ✅ Complete |
| **Docs** | Model card | ✅ Complete |
| **Docs** | Security guide | ✅ Complete |
| **Docs** | Observability guide | ✅ Complete |
| **Docs** | API examples | ✅ Complete |
| **Testing** | 8 test files (2,000+ lines) | ✅ Complete |
| **Testing** | 10 test tickets with golden annotations | ✅ Complete |
| **Testing** | 88.5% line coverage (reported) | ✅ Complete |

---

## Production Ready — v0.2.0 (Q3 2026)

### Authentication & Security
- [ ] API key authentication (Bearer token middleware)
- [ ] CORS restricted to allowed origins
- [ ] TLS/HTTPS via nginx reverse proxy
- [ ] Rate limiting (per-IP, per-key)
- [ ] Secrets manager integration (AWS Secrets Manager / HashiCorp Vault)

### Database & Performance
- [ ] PostgreSQL migration (via SQLAlchemy)
- [ ] Database migration tooling (Alembic)
- [ ] Connection pooling with pgBouncer
- [ ] Database indexing for history/metrics queries
- [ ] Query optimization for analytics endpoints

### Observability
- [ ] Prometheus metrics endpoint (`/metrics`)
- [ ] Grafana dashboard for KPIs
- [ ] Structured log shipping (Filebeat → Elasticsearch)
- [ ] Alert rules for critical thresholds
- [ ] Sentry error tracking integration

### Infrastructure
- [ ] Multi-worker deployment (gunicorn + uvicorn workers)
- [ ] Kubernetes manifests (Deployment, Service, Ingress)
- [ ] Terraform/Pulumi infrastructure-as-code
- [ ] Blue-green deployment strategy
- [ ] Load testing (k6/locust)

### Developer Experience
- [ ] OpenAPI/Swagger documentation refinement
- [ ] TypeScript type generation from Pydantic models
- [ ] API versioning strategy (v1 → v2)
- [ ] Integration test suite with real API calls

### Frontend
- [ ] Authentication UI (login/logout)
- [ ] User preferences and settings persistence
- [ ] Batch upload via CSV/JSON file
- [ ] Export extraction results (CSV, JSON, XLSX)

---

## Enterprise Scale — v0.3.0 (Q1 2027)

### Processing Architecture
- [ ] Async extraction via Celery workers
- [ ] Redis result backend for job status
- [ ] WebSocket progress notifications
- [ ] Multi-provider support with failover
- [ ] Provider health monitoring and auto-failover

### Advanced Features
- [ ] Chunked extraction for long tickets (> 2K tokens)
- [ ] Multi-label category support
- [ ] ML-based PII detection (NER model)
- [ ] Semantic consistency checking (extracted fields → source text)
- [ ] Custom schema configuration (per-tenant field definitions)
- [ ] Few-shot prompt configuration (per-tenant examples)

### Analytics & Reporting
- [ ] Time-series metrics database (TimescaleDB)
- [ ] Custom report builder with scheduling
- [ ] Anomaly detection on extraction quality trends
- [ ] Drill-down from aggregate metrics to individual records
- [ ] SLA tracking and reporting

### Enterprise Integration
- [ ] Webhook notifications on extraction completion
- [ ] Integration adapters (Zendesk, Jira, ServiceNow)
- [ ] SSO/SAML authentication
- [ ] Audit log for compliance (immutable, append-only)
- [ ] Tenant isolation (database-per-tenant or row-level security)

### Scale Targets
- 10,000+ tickets/day throughput
- 99.9% uptime SLA
- < 5s P99 latency
- Multi-region deployment support

---

## Future AI Improvements — v0.4.0+ (Q3 2027+)

### Language & Domain Expansion
- [ ] Full multilingual support (top 10 languages)
- [ ] Domain-specific extraction models (healthcare, finance, legal)
- [ ] Few-shot domain adaptation without fine-tuning
- [ ] Code-switching support within single ticket

### Self-Improving System
- [ ] Active learning loop: low-confidence → human review → model improvement
- [ ] Fine-tuned smaller model for common extraction patterns
- [ ] Caching layer for semantically similar tickets
- [ ] Confidence calibration across domains and languages

### Advanced Repair
- [ ] Repair strategy selection (choose optimal repair approach per error type)
- [ ] Multi-turn repair with targeted sub-questions
- [ ] External knowledge base integration for entity resolution
- [ ] Human-in-the-loop repair for critical failures

### Reasoning & Understanding
- [ ] Implicit intent detection (beyond explicit requested_action)
- [ ] Temporal reasoning (issue timeline extraction)
- [ ] Cross-ticket correlation (same customer, related issues)
- [ ] Root cause suggestion based on extracted patterns

### Performance Optimization
- [ ] Speculative extraction (predict schema while reading input)
- [ ] Batch-aware extraction optimization (shared context across batch)
- [ ] Quantized local model for offline/cold-start scenarios
- [ ] Edge deployment option for air-gapped environments

### Research Initiatives
- [ ] Extraction quality prediction (predict accuracy before extraction)
- [ ] Multi-task extraction + summarization
- [ ] Reinforcement learning from human feedback on extraction quality
- [ ] Open-source benchmark contribution (customer support extraction dataset)

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| v0.1.0 | 2026-07-20 | Initial MVP release with core extraction pipeline |
| v0.2.0 | Q3 2026 | Production hardening, security, PostgreSQL |
| v0.3.0 | Q1 2027 | Enterprise features, async processing, scale |
| v0.4.0+ | Q3 2027+ | AI improvements, multilingual, self-improving |

---

*This roadmap is a living document. Priorities may shift based on user feedback, technology changes, and business requirements.*
