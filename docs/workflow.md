# 🔄 ExtractIQ Engine Workflow

## Overview

ExtractIQ Engine transforms noisy, unstructured customer support tickets
into clean, schema-valid JSON through an AI-powered pipeline. Each stage
has a dedicated responsibility, ensuring accuracy, reliability, and
transparency.

------------------------------------------------------------------------

# End-to-End Workflow

``` text
Upload Ticket
      │
      ▼
Cleaning & Preprocessing
      │
      ▼
LLM Extraction
      │
      ▼
Pydantic Schema Validation
      │
      ├──────────────► Valid
      │                    │
      ▼                    ▼
Model-Driven Repair Loop  SQLite Storage
      │                    │
      └──────────────►      ▼
                      Metrics Engine
                            │
                            ▼
                  Analytics Dashboard
                            │
                            ▼
                     Download JSON
```

------------------------------------------------------------------------

# Step 1 --- Upload Ticket

The workflow begins when the user uploads or pastes a customer support
ticket using the React dashboard.

### Supported Input

-   Plain text
-   Customer support tickets
-   Chat conversations
-   Email content
-   Batch uploads

**Output:** Raw text is sent to the FastAPI backend.

------------------------------------------------------------------------

# Step 2 --- Cleaning & Preprocessing

Before AI extraction, the text is normalized to improve model quality.

### Tasks

-   Remove extra whitespace
-   Normalize punctuation
-   Clean formatting
-   Standardize line breaks
-   Prepare prompt-ready input

### Why it matters

Clean input improves extraction accuracy and reduces hallucinations.

------------------------------------------------------------------------

# Step 3 --- AI Extraction

The cleaned ticket is sent to the configured LLM.

### Model

-   Featherless AI (deepseek-ai/DeepSeek-V4-Pro) — default provider
-   Groq (llama-3.3-70b-versatile) — optional alternate

### Responsibilities

-   Understand customer intent
-   Detect issue category
-   Identify entities
-   Determine urgency
-   Analyze sentiment
-   Generate structured JSON

------------------------------------------------------------------------

# Step 4 --- Schema Validation

Every AI response is validated against a strict nested Pydantic schema.

### Validation Checks

-   Required fields
-   Data types
-   Enum values
-   Nested objects
-   JSON structure

### Goal

Guarantee consistent and schema-valid API responses.

------------------------------------------------------------------------

# Step 5 --- Model-Driven Repair

If validation fails, the pipeline automatically starts the repair
process.

### Repair Process

1.  Capture validation errors
2.  Generate a repair prompt
3.  Send original output and errors back to the LLM
4.  Receive corrected JSON
5.  Revalidate
6.  Repeat until valid or retry limit is reached

### Benefits

-   Zero regex fallbacks
-   Intelligent self-correction
-   Higher schema validity
-   Transparent failure handling

------------------------------------------------------------------------

# Step 6 --- Storage

Validated extraction results are stored in SQLite.

### Stored Information

-   Request ID
-   Original ticket
-   Cleaned text
-   Structured JSON
-   Processing time
-   Repair attempts
-   Status
-   Timestamp

------------------------------------------------------------------------

# Step 7 --- Analytics

Operational metrics are updated after every request.

### Captured Metrics

-   Total requests
-   Schema validity rate
-   Repair success rate
-   Average latency
-   Failure rate
-   Category distribution
-   Historical trends

------------------------------------------------------------------------

# Step 8 --- Download JSON

The frontend presents the validated JSON with options to inspect and
download the results.

### User Actions

-   Copy JSON
-   Download JSON
-   View repair timeline
-   Review extraction history
-   Analyze metrics

------------------------------------------------------------------------

# Complete Pipeline Summary

  Stage               Purpose                      Output
  ------------------- ---------------------------- -------------------------
  Upload Ticket       Accept user input            Raw support ticket
  Cleaning            Normalize text               Clean prompt-ready text
  AI Extraction       Generate structured data     Initial JSON
  Schema Validation   Verify structure             Valid or invalid result
  Repair Loop         Correct validation errors    Schema-valid JSON
  Storage             Persist results              SQLite records
  Analytics           Update performance metrics   Dashboard statistics
  Download JSON       Deliver final output         Structured JSON file

------------------------------------------------------------------------

# Workflow Highlights

-   AI-first extraction pipeline
-   Strict schema enforcement
-   Intelligent Model-Driven Repair Loop
-   No regex-based corrections
-   Persistent storage and history
-   Real-time analytics dashboard
-   Production-ready modular workflow
