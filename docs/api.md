# 🔌 ExtractIQ Engine API Documentation

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
  "text": "Hi, I was charged twice for Order #12345. Please refund the duplicate payment."
}
```

## Successful Response (200)

``` json
{
  "request_id": "7e52b5d2",
  "processing_time_ms": 1482,
  "repair_attempts": 1,
  "cleaned_text": "Hi, I was charged twice for Order #12345. Please refund the duplicate payment.",
  "result": {
    "ticket_id": "AUTO-1001",
    "customer": {
      "name": null,
      "account_id": null
    },
    "issue": {
      "category": "billing",
      "subcategory": "duplicate_charge",
      "product_or_service": null,
      "urgency": "medium"
    },
    "sentiment": "frustrated",
    "entities": {
      "order_ids": ["12345"],
      "dates_mentioned": [],
      "amounts_mentioned": []
    },
    "requested_action": "Refund duplicate payment",
    "resolution_status": "pending"
  }
}
```

## Error Responses

### 400 Bad Request

``` json
{"detail":"Input text cannot be empty."}
```

### 422 Validation Error

``` json
{"detail":"Invalid request payload."}
```

### 500 Internal Server Error

``` json
{"detail":"Extraction failed after maximum repair attempts."}
```

## Response Codes

  Code   Meaning
  ------ -----------------------------------
  200    Extraction completed successfully
  400    Invalid input
  422    Validation failed
  500    Internal extraction failure

## Expected Latency

  Stage           Average
  --------------- ---------
  Preprocessing   80 ms
  AI Extraction   1.2 s
  Repair Loop     300 ms
  Total           \< 2 s

## Example cURL

``` bash
curl -X POST http://localhost:8000/v1/extract \
-H "Content-Type: application/json" \
-d '{"text":"Hi, I was charged twice for Order #12345."}'
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
    {"text":"Refund my order."},
    {"text":"My package hasn't arrived."},
    {"text":"Unable to login."}
  ]
}
```

## Successful Response

``` json
{
  "processed":3,
  "successful":3,
  "failed":0,
  "results":[{}, {}, {}]
}
```

## Error Responses

  Code   Description
  ------ ---------------------------
  400    Invalid batch payload
  422    Validation failed
  500    Internal processing error

## Expected Latency

\~1--2 seconds per ticket

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
[
  {
    "request_id":"7e52b5d2",
    "timestamp":"2026-07-20T15:20:14Z",
    "status":"success",
    "repair_attempts":1,
    "processing_time_ms":1482
  }
]
```

## Response Codes

  Code   Meaning
  ------ ----------------
  200    Success
  500    Database Error

## Expected Latency

\<100 ms

## Example cURL

``` bash
curl http://localhost:8000/v1/history
```

------------------------------------------------------------------------

# GET `/v1/metrics`

## Description

Returns live extraction and evaluation metrics.

## Response

``` json
{
  "total_requests":124,
  "schema_validity":97.8,
  "repair_success_rate":92.4,
  "average_latency_ms":1456,
  "failure_rate":2.2
}
```

## Response Codes

  Code   Meaning
  ------ ---------------------
  200    Metrics returned
  500    Metrics unavailable

## Expected Latency

\<50 ms

## Example cURL

``` bash
curl http://localhost:8000/v1/metrics
```

------------------------------------------------------------------------

# GET `/v1/system`

## Description

Returns runtime configuration and system information.

## Response

``` json
{
  "model":"GLM-5.2",
  "provider":"Featherless AI",
  "database":"SQLite",
  "version":"1.0.0",
  "uptime":"02:41:18"
}
```

## Response Codes

  Code   Meaning
  ------ ---------
  200    Success

## Expected Latency

\<20 ms

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
  "status":"healthy"
}
```

## Response Codes

  Code   Meaning
  ------ -----------
  200    Healthy
  503    Unhealthy

## Expected Latency

\<10 ms

## Example cURL

``` bash
curl http://localhost:8000/health
```

------------------------------------------------------------------------

# GET `/version`

## Description

Returns application version and build metadata.

## Response

``` json
{
  "version":"1.0.0",
  "build_date":"2026-07-20",
  "git_sha":"abc1234",
  "model":"GLM-5.2"
}
```

## Response Codes

  Code   Meaning
  ------ ---------
  200    Success

## Expected Latency

\<10 ms

## Example cURL

``` bash
curl http://localhost:8000/version
```

------------------------------------------------------------------------

# 📊 API Summary

  Endpoint              Method   Purpose
  --------------------- -------- ----------------------------------------------
  `/v1/extract`         POST     Extract structured JSON from a single ticket
  `/v1/extract/batch`   POST     Batch extraction
  `/v1/history`         GET      Extraction history
  `/v1/metrics`         GET      Evaluation metrics
  `/v1/system`          GET      Runtime information
  `/health`             GET      Health check
  `/version`            GET      Version and build metadata
