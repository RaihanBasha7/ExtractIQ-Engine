# Observability Guide — ExtractIQ Engine

**Date:** 2026-07-20  
**Version:** 0.1.0

---

## 1. Overview

ExtractIQ Engine implements structured observability across four pillars:

| Pillar | Implementation | Location |
|--------|---------------|----------|
| **Logging** | Structured JSON logging with correlation IDs | `app/logging.py` |
| **Metrics** | Aggregated extraction metrics from database | `app/api/routes.py` |
| **Tracing** | Request IDs and correlation IDs across pipeline | `app/api/middleware.py` |
| **Monitoring** | Health checks, evaluation records, repair logs | `app/services/` |

---

## 2. Logging

### Log Format

All logs are emitted as structured JSON with the following schema:

```json
{
  "timestamp": "2026-07-20T14:30:00.123Z",
  "level": "INFO",
  "logger": "extractiq.extraction",
  "message": "Extraction completed",
  "request_id": "req_a1b2c3d4e5f6",
  "ticket_id": "TKT-001",
  "latency_ms": 2840,
  "retry_count": 1,
  "schema_valid": true,
  "confidence": 0.85
}
```

### Log Categories

| Logger Name | Purpose | Log Level |
|-------------|---------|-----------|
| `extractiq.api` | API request/response lifecycle | INFO |
| `extractiq.extraction` | Extraction pipeline steps | INFO |
| `extractiq.repair` | Repair loop attempts | INFO |
| `extractiq.database` | Database operations | DEBUG |
| `extractiq.preprocessing` | Text normalization and PII redaction | DEBUG |
| `extractiq.confidence` | Confidence scoring | DEBUG |
| `extractiq.evaluation` | Evaluation record creation | INFO |
| `extractiq.middleware` | Request ID assignment | DEBUG |
| `extractiq.health` | Health check results | INFO |

### Sensitive Data Handling

PII-redacted text may appear in logs at DEBUG level only. PRODUCTION DEPLOYMENTS MUST:
- Set minimum log level to INFO (suppresses DEBUG logs containing cleaned text)
- Use log shipping with encryption (e.g., TLS to Loki/Elasticsearch)
- Configure log retention policies per compliance requirements

### Log Shipping Configuration (Production)

```yaml
# Example Filebeat configuration
filebeat.inputs:
  - type: log
    paths: /var/log/extractiq/*.json
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["https://elasticsearch:9200"]
  index: "extractiq-logs-%{+yyyy.MM.dd}"
```

---

## 3. Metrics

### Available Metrics Endpoint

**`GET /v1/metrics`** returns:

| Metric | Description | Source |
|--------|-------------|--------|
| `total_requests` | Total extraction requests processed | DB count |
| `successful_extractions` | Schema-valid extractions | DB count |
| `failed_extractions` | Schema-invalid or infrastructure failures | DB count |
| `schema_valid_rate` | Ratio of valid to total | Computed |
| `average_retry_count` | Mean retries across all extractions | DB average |
| `average_processing_time` | Mean end-to-end latency (seconds) | DB average |
| `failure_breakdown` | Count per failure category | DB group-by |
| `latency_history` | Time-series of per-ticket latencies | DB ordered |
| `success_history` | Time-series of success/failure booleans | DB ordered |
| `retry_history` | Time-series of retry counts | DB ordered |

### Prometheus Integration (Planned)

```yaml
# Prometheus scrape configuration (v0.2)
scrape_configs:
  - job_name: 'extractiq'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
```

The application currently does not expose Prometheus-format metrics. This requires the `prometheus_client` library and a `/metrics` endpoint. Planned for v0.2.

### Key Performance Indicators

| KPI | Target | Warning | Critical |
|-----|--------|---------|----------|
| Schema valid rate | > 90% | < 85% | < 75% |
| P50 latency | < 3.0 s | > 3.5 s | > 5.0 s |
| P95 latency | < 8.0 s | > 10.0 s | > 15.0 s |
| Repair success rate | > 75% | < 70% | < 50% |
| Average retries | < 0.5 | > 0.8 | > 1.5 |
| Provider availability (health) | > 99.5% | < 99% | < 95% |

---

## 4. Request IDs

### Generation

Every API request receives a unique `X-Request-ID` header (generated as `req_` + 12 random hex characters) and an optional `X-Correlation-ID` passed through from the caller.

### Propagation

The `request_id` flows through:
1. Middleware → assigns to `request.state.request_id`
2. Service layer → passed to extraction pipeline
3. Extraction pipeline → logged with every event
4. Database → stored in `extraction_results` table
5. Response → returned as `X-Request-ID` header
6. Evaluation record → stored for traceability

### Correlation IDs

For batch requests, a single `correlation_id` links all individual ticket extractions. This enables:
- End-to-end tracing across a batch processing job
- Correlation with upstream systems (the caller's ticket system)
- Root cause analysis when multiple extractions fail simultaneously

### Log Query Example

```bash
# Find all log entries for a specific request
grep "req_a1b2c3d4e5f6" /var/log/extractiq/*.json

# Tail extraction logs for a specific ticket
tail -f /var/log/extractiq/extraction.json | grep "TKT-001"
```

---

## 5. Error Tracking

### Error Taxonomy

| Error Category | HTTP Code | Retryable | Examples |
|----------------|-----------|-----------|----------|
| Validation error | 422 | Yes (repair loop) | Enum mismatch, missing field |
| Invalid ticket | 400 | No | Empty text, non-UTF-8 encoding |
| Provider error | 503 | No (infra) | API timeout, rate limit |
| Internal error | 500 | No | Database error, unexpected exception |

### Error Response Format

All errors return `ErrorResponse` model:

```json
{
  "success": false,
  "error_code": "SCHEMA_VALIDATION_ERROR",
  "message": "Extraction failed schema validation after 3 repair attempts",
  "details": {
    "validation_errors": [
      {
        "field": "issue.category",
        "error": "Input should be 'billing', 'technical', 'shipping', 'account', 'product' or 'other'"
      }
    ],
    "retry_count": 3
  },
  "timestamp": "2026-07-20T14:30:00.123Z",
  "request_id": "req_a1b2c3d4e5f6"
}
```

### Error Codes

| Code | Meaning |
|------|---------|
| `VALIDATION_ERROR` | Input validation failed |
| `SCHEMA_VALIDATION_ERROR` | Extraction failed schema validation |
| `PROVIDER_ERROR` | LLM provider returned error |
| `RATE_LIMIT_ERROR` | Provider rate limit exceeded |
| `TIMEOUT_ERROR` | Provider request timed out |
| `INTERNAL_ERROR` | Unexpected system error |
| `DATABASE_ERROR` | Database operation failed |

---

## 6. Repair Logs

### Structure

Each extraction attempt (initial + up to 3 repairs) is logged via the repair logging module (`app/repair_logging.py`):

| Field | Description |
|-------|-------------|
| `attempt` | 1-based attempt number (1-4) |
| `status` | "success" or "failed" |
| `error` | Error message (Pydantic validation error for failed attempts) |
| `latency_ms` | Duration of this attempt |
| `timestamp` | ISO-8601 timestamp |

### Access

Repair logs are:
1. Stored in-memory during extraction → returned in API response as `repair_attempts`
2. Persisted to `extraction_results.repair_attempts_json` (JSON column in SQLite)
3. Available in extraction history via `GET /v1/history`

### Analysis

```python
# Query: count of extractions requiring repairs
session.query(ExtractionResult).filter(
    ExtractionResult.retry_count > 0
).count()

# Query: most common repair error patterns
session.query(
    ExtractionResult.repair_attempts_json['error'].as_string(),
    func.count()
).group_by(
    ExtractionResult.repair_attempts_json['error']
).all()
```

---

## 7. Monitoring Strategy

### MVP Phase (Current)

| Monitor | Mechanism | Frequency |
|---------|-----------|-----------|
| LLM provider health | `GET /health` endpoint | On each status check |
| Database connectivity | `GET /health` → SQLite check | On each status check |
| Extraction quality | Evaluation records (JSONL) | After each extraction |
| Latency tracking | Metrics endpoint (DB aggregate) | On each metrics request |
| Error rate | Metrics endpoint → failure_breakdown | On each metrics request |

### Production Phase (v0.2, Planned)

| Monitor | Tool | Purpose |
|---------|------|---------|
| Uptime monitoring | UptimeRobot / Pingdom | External availability |
| Log aggregation | ELK Stack or Grafana Loki | Centralized log search |
| Metrics dashboard | Grafana + Prometheus | Real-time KPI visualization |
| Alerting | PagerDuty / OpsGenie | Critical threshold notifications |
| Error tracking | Sentry | Exception aggregation and triage |

### Alert Rules (Planned)

```yaml
# Prometheus alert rules (v0.2)
groups:
  - name: extractiq
    rules:
      - alert: HighFailureRate
        expr: extractiq_schema_valid_rate < 0.75
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Schema valid rate dropped below 75%"

      - alert: HighLatency
        expr: extractiq_p95_latency > 10.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency exceeded 10 seconds"

      - alert: ProviderDown
        expr: extractiq_provider_health == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "LLM provider is unreachable"
```

### Dashboard Layout (Planned)

```
┌──────────────────────────────────────────────────────┐
│  KPI Row: Valid Rate | Avg Latency | Repair Rate    │
├──────────────────────────────────────────────────────┤
│  Latency Histogram (P50/P90/P95)                     │
├──────────────────────────────────────────────────────┤
│  Schema Valid Rate (Time Series)                     │
├──────────────────────────────────────────────────────┤
│  Error Breakdown (Pie Chart)                        │
├──────────────────────────────────────────────────────┤
│  Recent Extraction Results (Table)                   │
└──────────────────────────────────────────────────────┘
```

---

## 8. Logging Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |
| `LOG_FORMAT` | `json` | Output format: json or text |
| `LOG_OUTPUT` | `stdout` | Output destination: stdout, stderr, or file path |

### Docker Logging

```yaml
# docker-compose.yml logging config
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

*For questions about observability infrastructure, contact the platform engineering team.*
