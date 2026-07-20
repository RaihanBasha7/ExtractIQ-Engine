# ExtractIQ Engine API Documentation

> **Base URL**
>
> `http://localhost:8000`

------------------------------------------------------------------------

# POST `/v1/extract`

## Description

Extract structured JSON from a single customer support ticket. The
endpoint preprocesses raw text, performs AI-powered extraction,
validates the response against the Pydantic schema, automatically
repairs invalid outputs using the Model-Driven Repair Loop, and returns
schema-valid JSON.

## Request Body

``` json
{
  "ticket_id": "TKT-001",
  "raw_text": "Hi, I was charged twice for Order #12345. Please refund the duplicate payment."
}
```

## Successful Response (200)

``` json
{
  "ticket_id": "TKT-001",
  "success": true,
  "data": {
    "ticket_id": "TKT-001",
    "customer": { "name": null, "account_id": null },
    "issue": {
      "category": "billing",
      "subcategory": "duplicate_charge",
      "product_or_service": null,
      "urgency": "medium"
    },
    "sentiment": "frustrated",
    "entities": { "order_ids": ["12345"], "dates_mentioned": [], "amounts_mentioned": [] },
    "requested_action": "Refund duplicate payment",
    "resolution_status": "pending"
  },
  "confidence": 0.85,
  "metadata": {
    "repair_attempts": 0,
    "latency_ms": 1482,
    "provider": "featherless",
    "model": "zai-org/GLM-5.2",
    "validation": "passed",
    "timestamp": "2026-07-20T15:20:14Z"
  },
  "retry_count": 0,
  "latency_seconds": 1.482,
  "language": "en",
  "request_id": "REQ-000001",
  "cleaned_text": "Hi, I was charged twice for Order #12345. Please refund the duplicate payment.",
  "repair_attempts": []
}
```

## Error Responses

### 400 Bad Request

``` json
{"error_code": "HTTP_400", "message": "raw_text must not be empty", "success": false, "timestamp": "..."}
```

### 422 Validation Error

``` json
{"error_code": "VALIDATION_ERROR", "message": "Request validation failed", "success": false, "timestamp": "..."}
```

### 500 Internal Server Error

``` json
{"error_code": "INTERNAL_ERROR", "message": "An internal error occurred", "success": false, "timestamp": "..."}
```

## Response Codes

  Code   Meaning
  ------ -----------------------------------
  200    Extraction completed successfully
  400    Invalid input
  422    Validation failed
  500    Internal extraction failure

## Example cURL

``` bash
curl -X POST http://localhost:8000/v1/extract \
-H "Content-Type: application/json" \
-d '{"ticket_id": "TKT-001", "raw_text": "Hi, I was charged twice for Order #12345."}'
```

------------------------------------------------------------------------

# POST `/v1/extract/batch`

## Description

Processes multiple customer support tickets and returns structured
extraction results for each ticket.

## Request Body

``` json
{
  "tickets":[
    {"ticket_id": "TKT-001", "raw_text": "Refund my order."},
    {"ticket_id": "TKT-002", "raw_text": "My package hasn't arrived."},
    {"ticket_id": "TKT-003", "raw_text": "Unable to login."}
  ]
}
```

## Successful Response

``` json
{
  "results": [{"ticket_id": "...", "success": true, ...}, {}, {}]
}
```

## Error Responses

  Code   Description
  ------ ---------------------------
  400    Invalid batch payload
  422    Validation failed
  500    Internal processing error

## Example cURL

``` bash
curl -X POST http://localhost:8000/v1/extract/batch \
-H "Content-Type: application/json" \
-d @tickets.json
```

------------------------------------------------------------------------

# GET `/v1/history`

## Description

Returns previously processed extraction records.

## Response

``` json
{
  "items": [
    {
      "request_id": "1",
      "ticket_id": "TKT-001",
      "original_ticket": "Hi, I was charged twice...",
      "extraction_summary": {...},
      "confidence": 0.9,
      "latency": 1.482,
      "repair_attempts": [],
      "provider": "groq",
      "model": "llama-3.3-70b-versatile",
      "timestamp": "2026-07-20T15:20:14Z",
      "status": "completed"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

## Response Codes

  Code   Meaning
  ------ ----------------
  200    Success
  500    Database Error

## Example cURL

``` bash
curl http://localhost:8000/v1/history
```

------------------------------------------------------------------------

# GET `/v1/metrics`

## Description

Returns live extraction metrics.

## Response

``` json
{
  "total_requests": 124,
  "successful_extractions": 120,
  "failed_extractions": 4,
  "schema_valid_rate": 96.77,
  "average_retry_count": 0.05,
  "average_processing_time": 1.456,
  "failure_breakdown": {"validation_error": 2, "timeout": 2},
  "last_updated": "2026-07-20T15:20:14Z",
  "latency_history": [],
  "success_history": [],
  "retry_history": []
}
```

## Response Codes

  Code   Meaning
  ------ ---------------------
  200    Metrics returned
  500    Metrics unavailable

## Example cURL

``` bash
curl http://localhost:8000/v1/metrics
```

------------------------------------------------------------------------

# GET `/v1/system`

## Description

Returns combined health check and metrics.

## Response

``` json
{
  "health": {
    "status": "healthy",
    "timestamp": "...",
    "response_time_ms": 12.34,
    "checks": {
      "api": {"status": "ok", "response_time_ms": 0.1},
      "database": {"status": "ok", "response_time_ms": 1.2},
      "llm_provider": {"status": "ok", "response_time_ms": 5.0, "provider": "featherless", "model": "zai-org/GLM-5.2"},
      "disk": {"status": "ok", "response_time_ms": 0.3}
    }
  },
  "metrics": {...}
}
```

## Response Codes

  Code   Meaning
  ------ ---------
  200    Success

## Example cURL

``` bash
curl http://localhost:8000/v1/system
```

------------------------------------------------------------------------

# GET `/health`

## Description

Checks API health.

## Response

``` json
{
  "status": "healthy",
  "timestamp": "...",
  "response_time_ms": 0.5,
  "checks": {
    "api": {"status": "ok", "response_time_ms": 0.1},
    "database": {"status": "ok", "response_time_ms": 1.2},
    "llm_provider": {"status": "ok", "response_time_ms": 0.0, "provider": "featherless", "model": "zai-org/GLM-5.2"},
    "disk": {"status": "ok", "response_time_ms": 0.3}
  }
}
```

## Response Codes

  Code   Meaning
  ------ -----------
  200    Healthy
  503    Unhealthy

## Example cURL

``` bash
curl http://localhost:8000/health
```

------------------------------------------------------------------------

# GET `/version`

## Description

Returns application version and runtime metadata.

## Response

``` json
{
  "service": "OneInbox API",
  "version": "0.1.0",
  "api_version": "v1",
  "provider": "featherless",
  "model": "zai-org/GLM-5.2",
  "environment": "development",
  "python_version": "3.12.4",
  "timestamp": "2026-07-20T15:20:14Z"
}
```

## Response Codes

  Code   Meaning
  ------ ---------
  200    Success

## Example cURL

``` bash
curl http://localhost:8000/version
```

------------------------------------------------------------------------

# API Summary

  Endpoint              Method   Purpose
  --------------------- -------- ----------------------------------------------
  `/v1/extract`         POST     Extract structured JSON from a single ticket
  `/v1/extract/batch`   POST     Batch extraction
  `/v1/history`         GET      Extraction history
  `/v1/metrics`         GET      Evaluation metrics
  `/v1/system`          GET      Combined health and metrics
  `/health`             GET      Health check
  `/version`            GET      Version and runtime metadata
