# 🏗️ ExtractIQ Engine Architecture

## Overview

ExtractIQ Engine follows a modular, production-inspired architecture
that transforms unstructured customer support tickets into schema-valid
JSON using Large Language Models (LLMs), strict Pydantic validation, and
a Model-Driven Repair Loop.

The pipeline separates responsibilities into independent layers, making
the system reliable, maintainable, and scalable.

------------------------------------------------------------------------

# High-Level Architecture

``` text
                User
                  │
                  ▼
      React Frontend (Vite + Tailwind)
                  │
          HTTP REST API
                  │
                  ▼
        FastAPI Backend Server
                  │
        Request Validation & Logging
                  │
                  ▼
           Preprocessing Layer
                  │
      Text Cleaning & Normalization
                  │
                  ▼
           LLM Extraction Engine
         (Groq • Featherless AI)
                  │
                  ▼
      Pydantic Schema Validation
                  │
        Valid? ──────────────── Yes
          │                      │
          No                     ▼
          │             Persist Structured JSON
          ▼                      │
   Model-Driven Repair Loop      ▼
          │                 SQLite Database
          └──────────────►       │
                                 ▼
                   Metrics & History Service
                                 │
                                 ▼
                Analytics Dashboard (React)
```

------------------------------------------------------------------------

# Component Breakdown

## 1. User

The user uploads or pastes an unstructured customer support ticket
through the web interface.

Responsibilities:

-   Submit raw ticket text
-   View extraction results
-   Review repair attempts
-   Browse extraction history
-   Monitor analytics

------------------------------------------------------------------------

## 2. Frontend (React)

**Technology**

-   React
-   Vite
-   Tailwind CSS
-   Recharts

The frontend provides a modern engineer dashboard for interacting with
the extraction engine.

### Responsibilities

-   Ticket upload
-   Paste text
-   Batch extraction
-   Display structured JSON
-   Visualize repair timeline
-   Show metrics
-   Display extraction history
-   Download JSON

------------------------------------------------------------------------

## 3. FastAPI Backend

Acts as the central orchestration layer.

### Responsibilities

-   Expose REST API endpoints
-   Validate incoming requests
-   Generate request IDs
-   Handle exceptions
-   Route requests to services
-   Return structured responses

### API Endpoints

-   POST /v1/extract
-   POST /v1/extract/batch
-   GET /v1/history
-   GET /v1/metrics
-   GET /v1/system
-   GET /health
-   GET /version

------------------------------------------------------------------------

## 4. Preprocessing Layer

Before sending data to the LLM, the text is normalized.

### Responsibilities

-   Remove unnecessary whitespace
-   Normalize punctuation
-   Clean formatting
-   Standardize text
-   Prepare prompt-ready input

### Benefits

-   Higher extraction accuracy
-   Lower hallucination rate
-   Consistent model behavior

------------------------------------------------------------------------

## 5. LLM Extraction Engine

The AI layer performs semantic understanding of the ticket.

### Technology

-   Featherless AI (zai-org/GLM-5.2) — default
-   Groq (llama-3.3-70b-versatile) — optional

### Responsibilities

-   Understand ticket context
-   Identify entities
-   Classify issue category
-   Detect urgency
-   Detect sentiment
-   Extract requested action
-   Generate structured JSON

------------------------------------------------------------------------

## 6. Pydantic Validation

Every LLM response is validated against a strict nested schema.

### Validated Fields

-   Customer
-   Issue
-   Category
-   Urgency
-   Sentiment
-   Entities
-   Requested Action
-   Resolution Status

### Benefits

-   Prevents malformed JSON
-   Ensures consistent API output
-   Enforces schema integrity

------------------------------------------------------------------------

## 7. Model-Driven Repair Loop

If validation fails, the response is **not** corrected using regex.

Instead, validation errors are sent back to the LLM for intelligent
self-correction.

### Workflow

1.  LLM generates JSON
2.  Pydantic validates output
3.  Validation errors are captured
4.  Errors are included in a repair prompt
5.  LLM regenerates corrected JSON
6.  Repeat until valid or retry limit is reached

### Advantages

-   No brittle regex rules
-   Self-healing pipeline
-   Higher schema validity
-   Transparent failure reporting

------------------------------------------------------------------------

## 8. SQLite Database

Stores extraction results and operational metadata.

### Stored Data

-   Request ID
-   Original ticket
-   Cleaned text
-   Final JSON
-   Processing time
-   Repair attempts
-   Status
-   Timestamp

### Benefits

-   Lightweight
-   Portable
-   Ideal for MVP deployments

------------------------------------------------------------------------

## 9. Metrics Service

Aggregates operational statistics.

### Tracks

-   Total requests
-   Schema validity
-   Repair success rate
-   Average latency
-   Failure rate
-   Category distribution
-   Historical trends

------------------------------------------------------------------------

## 10. Analytics Dashboard

Provides real-time visibility into extraction performance.

### Dashboard Features

-   Success rate
-   Validation rate
-   Latency charts
-   Repair statistics
-   History table
-   Category distribution
-   Health status
-   System information

------------------------------------------------------------------------

# End-to-End Request Flow

``` text
1. User submits a ticket

↓

2. React sends POST request

↓

3. FastAPI receives request

↓

4. Request validation

↓

5. Text preprocessing

↓

6. LLM extracts structured data

↓

7. Pydantic validates schema

↓

8. If invalid → Repair Loop

↓

9. Valid JSON stored in SQLite

↓

10. Metrics updated

↓

11. JSON returned to frontend

↓

12. Dashboard visualizes results
```

------------------------------------------------------------------------

# Design Principles

-   Modular architecture
-   Separation of concerns
-   Strict schema validation
-   AI-first extraction
-   No regex fallbacks
-   Production-ready APIs
-   Transparent observability
-   Easy extensibility

------------------------------------------------------------------------

# Scalability Roadmap

Current MVP

-   FastAPI
-   SQLite
-   Single LLM provider
-   Local deployment

Future Production

-   PostgreSQL
-   Redis
-   Celery
-   Kubernetes
-   LiteLLM gateway
-   Multi-provider failover
-   Cloud deployment
-   Distributed workers
-   Real-time monitoring

------------------------------------------------------------------------

# Architecture Highlights

-   AI-powered structured extraction
-   Model-Driven Repair Loop
-   Strict Pydantic schema enforcement
-   Lightweight persistence
-   RESTful API design
-   Analytics and observability
-   Modular components for future scaling
