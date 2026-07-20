# API Examples — ExtractIQ Engine

**Date:** 2026-07-20  
**Version:** 0.1.0  
**Base URL:** `http://localhost:8000`

---

## 1. Single Ticket Extraction

### Request

```bash
curl -X POST http://localhost:8000/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-001",
    "raw_text": "Hi, I was charged twice for my subscription. My order ID is ORD-12345 and I want a refund of $49.99. This happened on March 15. - John"
  }'
```

### Successful Response

```json
{
  "ticket_id": "TKT-001",
  "success": true,
  "data": {
    "ticket_id": "TKT-001",
    "customer": {
      "name": "John",
      "account_id": null
    },
    "issue": {
      "category": "billing",
      "subcategory": "duplicate charge",
      "product_or_service": "subscription",
      "urgency": "high"
    },
    "sentiment": "frustrated",
    "entities": {
      "order_ids": ["ORD-12345"],
      "dates_mentioned": ["March 15"],
      "amounts_mentioned": ["$49.99"]
    },
    "requested_action": "Refund $49.99 for duplicate charge",
    "resolution_status": "unresolved"
  },
  "confidence": 0.95,
  "metadata": {
    "schema_version": "1.0",
    "extraction_timestamp": "2026-07-20T14:30:00.123Z",
    "processing_time_ms": 2840,
    "model": "llama-3.3-70b-versatile",
    "provider": "groq"
  },
  "retry_count": 0,
  "failure_category": null,
  "latency_seconds": 2.84,
  "language": "en",
  "request_id": "req_a1b2c3d4e5f6",
  "cleaned_text": "Hi, I was charged twice for my subscription. My order ID is ORD-12345 and I want a refund of $49.99. This happened on March 15. - John",
  "repair_attempts": []
}
```

### Response with Repair Attempts

```json
{
  "ticket_id": "TKT-002",
  "success": true,
  "data": {
    "ticket_id": "TKT-002",
    "customer": {
      "name": "Sarah Mitchell",
      "account_id": "ORD-78492-Z"
    },
    "issue": {
      "category": "billing",
      "subcategory": "duplicate charge",
      "product_or_service": "premium subscription",
      "urgency": "high"
    },
    "sentiment": "frustrated",
    "entities": {
      "order_ids": ["ORD-78492-Z"],
      "dates_mentioned": ["March 3 2026", "March 5 2026"],
      "amounts_mentioned": ["$149.99"]
    },
    "requested_action": "Refund $149.99 for duplicate charge",
    "resolution_status": "unresolved"
  },
  "confidence": 0.60,
  "metadata": {
    "schema_version": "1.0",
    "extraction_timestamp": "2026-07-20T14:31:00.456Z",
    "processing_time_ms": 4120,
    "model": "llama-3.3-70b-versatile",
    "provider": "groq"
  },
  "retry_count": 1,
  "failure_category": null,
  "latency_seconds": 4.12,
  "language": "en",
  "request_id": "req_f6e5d4c3b2a1",
  "cleaned_text": "SUBJECT: DUPLICATE CHARGE ON MY ACCOUNT ...",
  "repair_attempts": [
    {
      "attempt": 1,
      "status": "failed",
      "error": "1 validation error for TicketExtraction\nissue.category\n  Input should be 'billing', 'technical', 'shipping', 'account', 'product' or 'other' [type=enum, input_value='billing', ...]"
    },
    {
      "attempt": 2,
      "status": "success",
      "error": null
    }
  ]
}
```

---

## 2. Batch Extraction

### Request

```bash
curl -X POST http://localhost:8000/v1/extract/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tickets": [
      {
        "ticket_id": "TKT-001",
        "raw_text": "Hi, I was charged twice for my subscription. My order ID is ORD-12345 and I want a refund of $49.99."
      },
      {
        "ticket_id": "TKT-002",
        "raw_text": "I cannot log into my account. It says invalid credentials. Please help."
      }
    ]
  }'
```

### Response

```json
{
  "results": [
    {
      "ticket_id": "TKT-001",
      "success": true,
      "data": {
        "ticket_id": "TKT-001",
        "customer": {"name": null, "account_id": null},
        "issue": {
          "category": "billing",
          "subcategory": "duplicate charge",
          "product_or_service": "subscription",
          "urgency": "medium"
        },
        "sentiment": "frustrated",
        "entities": {
          "order_ids": ["ORD-12345"],
          "dates_mentioned": [],
          "amounts_mentioned": ["$49.99"]
        },
        "requested_action": "Refund $49.99 for duplicate charge",
        "resolution_status": "unresolved"
      },
      "confidence": 0.85,
      "metadata": {
        "schema_version": "1.0",
        "extraction_timestamp": "2026-07-20T14:32:00.789Z",
        "processing_time_ms": 2560,
        "model": "llama-3.3-70b-versatile",
        "provider": "groq"
      },
      "retry_count": 0,
      "failure_category": null,
      "latency_seconds": 2.56,
      "language": "en",
      "request_id": "req_001_batch_1",
      "cleaned_text": "Hi, I was charged twice for my subscription. My order ID is ORD-12345 and I want a refund of $49.99.",
      "repair_attempts": []
    },
    {
      "ticket_id": "TKT-002",
      "success": true,
      "data": {
        "ticket_id": "TKT-002",
        "customer": {"name": null, "account_id": null},
        "issue": {
          "category": "account",
          "subcategory": "cannot login",
          "product_or_service": null,
          "urgency": "high"
        },
        "sentiment": "frustrated",
        "entities": {
          "order_ids": [],
          "dates_mentioned": [],
          "amounts_mentioned": []
        },
        "requested_action": "Help with account login",
        "resolution_status": "unresolved"
      },
      "confidence": 0.85,
      "metadata": {
        "schema_version": "1.0",
        "extraction_timestamp": "2026-07-20T14:32:03.234Z",
        "processing_time_ms": 3010,
        "model": "llama-3.3-70b-versatile",
        "provider": "groq"
      },
      "retry_count": 0,
      "failure_category": null,
      "latency_seconds": 3.01,
      "language": "en",
      "request_id": "req_001_batch_2",
      "cleaned_text": "I cannot log into my account. It says invalid credentials. Please help.",
      "repair_attempts": []
    }
  ]
}
```

---

## 3. Error Examples

### Validation Error (Bad Request)

```bash
curl -X POST http://localhost:8000/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "", "raw_text": ""}'
```

```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [
    {
      "loc": ["body", "ticket_id"],
      "msg": "String should have at least 1 character",
      "type": "string_too_short"
    },
    {
      "loc": ["body", "raw_text"],
      "msg": "String should have at least 1 character",
      "type": "string_too_short"
    }
  ],
  "timestamp": "2026-07-20T14:33:00.111Z",
  "request_id": "req_error_001"
}
```

### Provider Error

```json
{
  "success": false,
  "error_code": "PROVIDER_ERROR",
  "message": "LLM provider returned an error",
  "details": {
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    "status_code": 429,
    "error": "Rate limit exceeded. Please retry after 60 seconds."
  },
  "timestamp": "2026-07-20T14:34:00.222Z",
  "request_id": "req_error_002"
}
```

### Schema Validation Failure (After Repair Loop Exhausted)

```json
{
  "ticket_id": "TKT-003",
  "success": false,
  "data": null,
  "confidence": 0.1,
  "metadata": {
    "schema_version": "1.0",
    "extraction_timestamp": "2026-07-20T14:35:00.333Z",
    "processing_time_ms": 8940,
    "model": "llama-3.3-70b-versatile",
    "provider": "groq"
  },
  "retry_count": 3,
  "failure_category": "enum_mismatch",
  "latency_seconds": 8.94,
  "language": "en",
  "request_id": "req_error_003",
  "cleaned_text": "...",
  "repair_attempts": [
    {
      "attempt": 1,
      "status": "failed",
      "error": "1 validation error for TicketExtraction\nissue.category\n  Input should be 'billing', 'technical', 'shipping', 'account', 'product' or 'other'"
    },
    {
      "attempt": 2,
      "status": "failed",
      "error": "1 validation error for TicketExtraction\nissue.category\n  Input should be 'billing', 'technical', 'shipping', 'account', 'product' or 'other'"
    },
    {
      "attempt": 3,
      "status": "failed",
      "error": "1 validation error for TicketExtraction\nissue.category\n  Input should be 'billing', 'technical', 'shipping', 'account', 'product' or 'other'"
    }
  ]
}
```

---

## 4. Health Check

### Request

```bash
curl http://localhost:8000/health
```

### Response

```json
{
  "status": "healthy",
  "timestamp": "2026-07-20T14:36:00.444Z",
  "response_time_ms": 1234,
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12,
      "error": null,
      "provider": null,
      "model": null,
      "database_type": "sqlite",
      "checked_at": "2026-07-20T14:36:00.444Z"
    },
    "llm_provider": {
      "status": "healthy",
      "response_time_ms": 1200,
      "error": null,
      "provider": "groq",
      "model": "llama-3.3-70b-versatile",
      "database_type": null,
      "checked_at": "2026-07-20T14:36:00.444Z"
    },
    "disk": {
      "status": "healthy",
      "response_time_ms": 2,
      "error": null,
      "provider": null,
      "model": null,
      "database_type": null,
      "checked_at": "2026-07-20T14:36:00.444Z"
    }
  }
}
```

---

## 5. Version Info

### Request

```bash
curl http://localhost:8000/version
```

### Response

```json
{
  "service": "OneInbox API",
  "version": "0.1.0",
  "api_version": "v1",
  "provider": "groq",
  "model": "llama-3.3-70b-versatile",
  "environment": "development",
  "python_version": "3.12.4",
  "timestamp": "2026-07-20T14:37:00.555Z"
}
```

---

## 6. Metrics

### Request

```bash
curl http://localhost:8000/v1/metrics
```

### Response

```json
{
  "total_requests": 75,
  "successful_extractions": 69,
  "failed_extractions": 6,
  "schema_valid_rate": 92.0,
  "average_retry_count": 0.49,
  "average_processing_time": 3.21,
  "failure_breakdown": {
    "enum_mismatch": 2,
    "missing_field": 1,
    "invalid_json": 1,
    "infrastructure_error": 2
  },
  "last_updated": "2026-07-20T14:38:00.666Z",
  "latency_history": [
    {"ticket_id": "TKT-001", "latency_seconds": 2.84, "timestamp": "2026-07-20T14:30:00Z"},
    {"ticket_id": "TKT-002", "latency_seconds": 4.12, "timestamp": "2026-07-20T14:31:00Z"}
  ],
  "success_history": [
    {"ticket_id": "TKT-001", "success": true, "timestamp": "2026-07-20T14:30:00Z"},
    {"ticket_id": "TKT-002", "success": true, "timestamp": "2026-07-20T14:31:00Z"}
  ],
  "retry_history": [
    {"ticket_id": "TKT-001", "retry_count": 0, "timestamp": "2026-07-20T14:30:00Z"},
    {"ticket_id": "TKT-002", "retry_count": 1, "timestamp": "2026-07-20T14:31:00Z"}
  ]
}
```

---

## 7. Extraction History

### Request

```bash
curl "http://localhost:8000/v1/history?limit=10&offset=0"
```

### Response

```json
{
  "items": [
    {
      "request_id": "req_a1b2c3d4e5f6",
      "ticket_id": "TKT-001",
      "original_ticket": "Hi, I was charged twice...",
      "extraction_summary": {
        "category": "billing",
        "urgency": "high",
        "sentiment": "frustrated",
        "amounts": ["$49.99"]
      },
      "confidence": 0.95,
      "latency": 2.84,
      "repair_attempts": [],
      "provider": "groq",
      "model": "llama-3.3-70b-versatile",
      "timestamp": "2026-07-20T14:30:00.123Z",
      "status": "completed"
    }
  ],
  "total": 75,
  "limit": 10,
  "offset": 0
}
```

---

## 8. Error Response Format

All errors follow a consistent structure:

```json
{
  "success": false,
  "error_code": "<ERROR_CODE>",
  "message": "<Human-readable error description>",
  "details": <optional structured details>,
  "timestamp": "<ISO-8601 UTC>",
  "request_id": "<correlation id>"
}
```

### Error Codes Reference

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request body validation failed |
| `SCHEMA_VALIDATION_ERROR` | 200* | Extraction failed schema validation |
| `PROVIDER_ERROR` | 503 | LLM provider error |
| `RATE_LIMIT_ERROR` | 429 | Provider rate limit exceeded |
| `TIMEOUT_ERROR` | 504 | Provider request timed out |
| `INTERNAL_ERROR` | 500 | Unexpected system error |

*Schema validation failures are returned with HTTP 200 but `success: false` — the extraction was processed but failed to produce valid output.

---

## 9. Request ID Headers

Every response includes correlation headers:

```
X-Request-ID: req_a1b2c3d4e5f6
X-Correlation-ID: (passed through from request, or generated)
```

To trace a request through the system, include a correlation ID:

```bash
curl -X POST http://localhost:8000/v1/extract \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: my-system-ref-123" \
  -d '{"ticket_id": "TKT-001", "raw_text": "..."}'
```

---

*For the complete API specification, see `api.md`.*
