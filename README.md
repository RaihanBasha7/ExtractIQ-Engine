<div align="center">

#  ExtractIQ Engine

### AI-Powered Structured Information Extraction Engine for Noisy Customer Support Data

<p align="center">

🌐 Live Demo • 📄 Documentation • ⚡ API Docs • 🎥 Demo Video

</p>

<p align="center">

<img src="docs/screenshots/dashboard.png" width="95%"/>

</p>

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-green.svg)]()
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)]()
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-red.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

## 📊 Project Highlights

- ✅ Production-ready deployment
- 🤖 AI-Powered Structured Extraction
- 🔄 Model-Driven Repair Loop
- 📄 Strict Pydantic Schema Validation
- 🛡️ PII Redaction
- 📦 Batch Extraction
- 📈 Analytics Dashboard
- 📜 Extraction History
- ❤️ Health Monitoring
- 🌐 Render + Vercel Deployment
- 🗄️ Supabase Database
- ⚡ Featherless AI + Google Gemma 4 31B

---

**Extract structured, schema-valid JSON from messy customer support tickets using LLMs with a Model-Driven Repair Loop.**

Built for the **OneInbox AI Engineer Internship Hackathon 2026**

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Workflow](#workflow)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Deployment](#deployment)
- [Performance](#performance)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

#  Short Description

ExtractIQ Engine is a production-inspired AI extraction system that transforms noisy customer support tickets into clean, structured JSON.

Instead of relying on fragile regex patterns, it uses **LLMs**, **strict Pydantic validation**, and a **Model-Driven Repair Loop** to guarantee highly reliable outputs.

### Problem Statement

Customer support tickets are messy — missing punctuation, broken sentences, mixed languages, typing mistakes, missing fields, and unstructured conversations. Traditional regex-based extraction breaks easily, and even modern LLMs frequently produce invalid JSON or violate predefined schemas.

### Solution

ExtractIQ Engine introduces a **Model-Driven Repair Loop**:

1. **Extract** — LLM extracts structured data from ticket
2. **Validate** — Pydantic enforces strict schema compliance  
3. **Detect** — Validation errors are captured with exact field details
4. **Repair** — Errors are fed back to the LLM for targeted correction
5. **Repeat** — Loop continues until valid or retry limit reached

---

## ⭐ Key Features

### 🤖 AI-Powered Extraction
Extracts structured information from noisy customer support tickets using state-of-the-art LLMs (Featherless AI, Groq).

### ✅ Strict Schema Validation
Every response must satisfy nested Pydantic models with enum enforcement, type checking, and required field validation.

### 🔄 Model-Driven Repair Loop
Automatically repairs invalid outputs by feeding validation errors back to the LLM. No regex fallbacks, no force-fitting.

### 🛡️ PII Redaction
Emails, phone numbers, and zip codes are automatically redacted before any data reaches third-party LLM providers.

### 📊 Analytics Dashboard
Real-time Streamlit dashboard showing success rates, repair rates, latency, category distribution, and historical trends.

### 📂 Batch Extraction
Upload and process multiple tickets simultaneously with individual error handling.

### 📜 Extraction History
Complete history of all extractions with pagination, search, and detailed repair attempt logging.

### ❤️ Health Monitoring
Comprehensive health endpoint with per-dependency status checks (API, database, LLM provider, disk).

### 📈 Metrics API
Live extraction statistics including success rates, average processing time, retry distribution, and failure breakdown.

### 🧠 MVP Architecture
- Request IDs with end-to-end correlation
- Structured JSON logging
- Version endpoint
- Error tracking with correlation IDs
- Global exception handlers
- CORS configuration

---

## 🏗 Architecture

![Architecture](docs/architecture.png)

The system follows a modular pipeline architecture:

```
┌─────────────┐
│  Raw Ticket  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Preprocess   │  ← PII redaction, normalization, language detection
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ LLM Extract  │  ← instructor + Groq/Featherless
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│  Validate    │────→│  Repair Loop │  ← Feed errors back to LLM
└──────┬──────┘     └──────────────┘
       │
       ▼
┌─────────────┐
│ Validated    │  ← Schema-compliant JSON
│    JSON      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database    │  ← SQLite (SQLAlchemy)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Analytics   │  ← Streamlit / React Dashboard
└─────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI Server                     │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │  Routes   │→│  Service  │→│  Extraction Engine  │ │
│  └──────────┘  └──────────┘  └────────────────────┘ │
│                      │               │               │
│                      ▼               ▼               │
│               ┌──────────┐  ┌────────────────────┐ │
│               │ Database │  │  LLM Provider       │ │
│               │   (DB)   │  │  (Groq/Featherless) │ │
│               └──────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Workflow Pipeline

```
User Uploads Ticket
       │
       ▼
Text Cleaning & PII Redaction
       │
       ▼
LLM Extraction (instructor + Groq/Featherless)
       │
       ▼
JSON Validation (Pydantic TicketExtraction)
       │
       ├── Valid ──→ Database Storage ──→ Response
       │
       └── Invalid ──→ Repair Loop
                            │
                            ├── (≤3 attempts) Re-prompt with errors
                            │
                            └── Max retries exceeded → Return failure
```

---

## ⚙ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| FastAPI    | REST API framework |
| Python 3.12 | Runtime |
| Pydantic v2 | Schema validation & settings |
| SQLAlchemy 2.0 | ORM |
| SQLite      | Database |
| instructor  | Structured LLM output |
| Uvicorn     | ASGI server |

### AI / LLM
| Technology | Purpose |
|-----------|---------|
| Featherless AI | Primary LLM provider (default: google/gemma-4-31B-it) |
| Groq       | Optional alternate provider (llama-3.3-70b-versatile) |

### Frontend
| Technology | Purpose |
|-----------|---------|
| React 19   | UI framework |
| Vite       | Build tool |
| TailwindCSS | Styling |
| Recharts   | Charts |
| Framer Motion | Animations |
| TypeScript | Type safety |

### Dashboard
| Technology | Purpose |
|-----------|---------|
| Streamlit  | Analytics dashboard |
| Plotly     | Interactive charts |
| Pandas     | Data processing |

### DevOps
| Technology | Purpose |
|-----------|---------|
| Docker     | Containerization |
| GitHub Actions | CI/CD |
| pytest     | Testing |
| Black      | Code formatting |
| isort      | Import sorting |
| Flake8     | Linting |
| mypy       | Type checking |
| pre-commit | Git hooks |

---

## 📁 Project Structure

```
ExtractIQ-Engine/
│
├── backend/
│   ├── app/
│   │   ├── api/              # API routes, models, middleware, error models
│   │   │   ├── routes.py     # FastAPI route handlers
│   │   │   ├── models.py     # Request/response Pydantic models
│   │   │   ├── service.py    # Business logic orchestrator
│   │   │   ├── middleware.py # Request ID & correlation middleware
│   │   │   └── error_models.py  # Standard error response model
│   │   ├── database/
│   │   │   ├── database.py   # SQLAlchemy engine & session
│   │   │   ├── models.py     # ORM models
│   │   │   └── repository.py # Data access layer
│   │   ├── evaluation/
│   │   │   ├── collector.py  # Evaluation record collector
│   │   │   ├── metrics.py    # Evaluation metrics calculations
│   │   │   ├── models.py     # Evaluation record schema
│   │   │   └── repository.py # JSONL-backed evaluation persistence
│   │   ├── services/
│   │   │   ├── health_service.py  # Dependency health checks
│   │   │   ├── metrics_service.py # Metrics aggregation
│   │   │   └── version_service.py # Version info
│   │   ├── config.py         # Configuration (backward-compatible)
│   │   ├── settings.py       # Pydantic Settings (centralized config)
│   │   ├── schema.py         # TicketExtraction Pydantic schema
│   │   ├── extraction.py     # Extraction & repair loop
│   │   ├── preprocessing.py  # Text cleaning & PII redaction
│   │   ├── confidence.py     # Confidence scoring
│   │   ├── metadata.py       # Extraction metadata builder
│   │   ├── logging.py        # Structured JSON logging
│   │   └── repair_logging.py # Repair attempt logging
│   ├── tests/
│   │   ├── conftest.py       # Shared fixtures & test configuration
│   │   ├── test_api.py       # API endpoint tests
│   │   ├── test_schema.py    # Schema validation tests
│   │   ├── test_repair_loop.py  # Repair loop tests
│   │   ├── test_database.py  # Database operation tests
│   │   ├── test_utilities.py # Utility module tests
│   │   ├── test_error_handling.py  # Error handling tests
│   │   ├── test_integration_mocked.py  # Mocked integration tests
│   │   └── test_evaluation.py  # Evaluation module tests
│   ├── scripts/              # Utility scripts
│   ├── data/                 # Data files (CSV, JSONL, SQLite)
│   ├── reports/              # Evaluation reports
│   ├── Dockerfile            # Multi-stage Docker build
│   ├── requirements.txt      # Production dependencies
│   ├── requirements-dev.txt  # Development dependencies
│   ├── pyproject.toml        # Tool configuration
│   └── pytest.ini            # Pytest configuration
│
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── lib/              # API client & utilities
│   │   └── assets/           # Static assets
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── dashboard/
│   ├── app.py                # Streamlit app
│   ├── analytics.py          # Analytics components
│   ├── charts.py             # Chart components
│   └── config.py             # Dashboard config
│
├── docs/
│   ├── architecture.png      # Architecture diagram
│   ├── architecture.md       # Architecture documentation
│   ├── api.md                # API documentation
│   ├── api_examples.md       # API examples
│   ├── banner.png            # Project banner
│   ├── changelog.md          # Release history
│   ├── code_of_conduct.md    # Code of conduct
│   ├── contributing.md       # Contributing guide
│   ├── deployment.md         # Deployment guide
│   ├── logo.png              # Project logo
│   ├── model-card.md         # Model card
│   ├── observability.md      # Observability guide
│   ├── roadmap.md            # Roadmap
│   ├── screenshots/          # Application screenshots
│   ├── security.md           # Security guide
│   ├── workflow.md           # Workflow documentation
│   ├── adr/                  # Architecture decision records
│   └── reports/              # Documentation reports
│       ├── audit_report.md
│       ├── benchmark.md
│       ├── evaluation.md
│       ├── failure_analysis.md
│       ├── metric_verification_report.md
│       ├── performance.md
│       └── project_metrics.md
│
├── reports/                  # Generated outputs
│
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI pipeline
│
├── docker-compose.yml        # Multi-service orchestration
├── .pre-commit-config.yaml   # Pre-commit hooks
├── .editorconfig             # Editor configuration
├── .gitignore                # Git ignore rules
├── .dockerignore             # Docker ignore rules
├── README.md                 # This file
└── LICENSE                   # MIT License
```

---

## 💡 Why ExtractIQ?

Traditional regex pipelines fail on noisy customer support data.

ExtractIQ replaces brittle extraction with an AI-first validation pipeline where every response is validated against a strict schema and automatically repaired until it becomes structurally valid.

This makes the system significantly more reliable for production-oriented AI workflows.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- An API key from Groq or Featherless AI

### 1. Clone the Repository

```bash
git clone https://github.com/RaihanBasha7/ExtractIQ-Engine.git
cd ExtractIQ-Engine
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```env
LLM_PROVIDER=featherless
FEATHERLESS_API_KEY=fl_your_key_here
FEATHERLESS_MODEL=deepseek-ai/DeepSeek-V4-Pro
FEATHERLESS_BASE_URL=https://api.featherless.ai/v1
MAX_REPAIR_RETRIES=3
```

To switch to Groq as the provider, change `LLM_PROVIDER=groq` and set `GROQ_API_KEY` and `GROQ_MODEL` instead.

### 4. Run the Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 6. Access the Application

| Service      | URL                        |
|-------------|----------------------------|
| Frontend     | http://localhost:5173       |
| API Docs     | http://localhost:8000/docs  |
| Dashboard    | http://localhost:8501       |

---

## 🔌 API Reference

> **Note on example responses:** The JSON response bodies below show the expected structure and field types. Numeric values (response times, latency, confidence) are illustrative and will vary based on provider, network conditions, and input complexity. See `docs/reports/benchmark.md` for actual measured values.

### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-07-20T10:30:00Z",
  "response_time_ms": 12.34,
  "checks": {
    "api": { "status": "ok", "response_time_ms": 0.1 },
    "database": { "status": "ok", "response_time_ms": 1.2 },
    "llm_provider": { "status": "ok", "response_time_ms": 5.0, "provider": "featherless", "model": "deepseek-ai/DeepSeek-V4-Pro" },
    "disk": { "status": "ok", "response_time_ms": 0.3 }
  }
}
```

### Version Info

```http
GET /version
```

Response:
```json
{
  "service": "OneInbox API",
  "version": "0.1.0",
  "api_version": "v1",
  "provider": "featherless",
  "model": "deepseek-ai/DeepSeek-V4-Pro",
  "environment": "development",
  "python_version": "3.12.4",
  "timestamp": "2026-07-20T10:30:00Z"
}
```

### Single Extraction

```http
POST /v1/extract
Content-Type: application/json

{
  "ticket_id": "TKT-001",
  "raw_text": "From: John Doe <john@example.com>\nSubject: Need help\n\nI can't log into my account. It says 'invalid password'. Help!"
}
```

Response:
```json
{
  "ticket_id": "TKT-001",
  "success": true,
  "data": {
    "ticket_id": "TKT-001",
    "customer": { "name": "John Doe", "account_id": null },
    "issue": {
      "category": "account",
      "subcategory": "login failure",
      "product_or_service": null,
      "urgency": "high"
    },
    "sentiment": "frustrated",
    "entities": { "order_ids": [], "dates_mentioned": [], "amounts_mentioned": [] },
    "requested_action": "help with login",
    "resolution_status": "unresolved"
  },
  "confidence": 0.85,
  "metadata": {
    "repair_attempts": 0,
    "latency_ms": 450,
    "provider": "featherless",
    "model": "deepseek-ai/DeepSeek-V4-Pro",
    "validation": "passed",
    "timestamp": "2026-07-20T10:30:00Z"
  },
  "retry_count": 0,
  "latency_seconds": 0.45,
  "language": "en",
  "request_id": "REQ-000001",
  "cleaned_text": "From: John Doe <[REDACTED_EMAIL]>\nSubject: Need help\n\nI can't log into my account...",
  "repair_attempts": []
}
```

### Batch Extraction

```http
POST /v1/extract/batch
Content-Type: application/json

{
  "tickets": [
    { "ticket_id": "TKT-001", "raw_text": "Need help with my order" },
    { "ticket_id": "TKT-002", "raw_text": "Account locked, please help" }
  ]
}
```

### Extraction History

```http
GET /v1/history?limit=10&offset=0
```

### Metrics

```http
GET /v1/metrics
```

### Combined System Status

```http
GET /v1/system
```

---

## 🧪 Testing

The project uses **pytest** for testing.

### Running Tests

```bash
cd backend

# Run all tests
python -m pytest

# With coverage report
python -m pytest --cov=app --cov-report=term

# With HTML coverage report
python -m pytest --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/test_api.py

# Run tests by marker
python -m pytest -m "unit"
python -m pytest -m "integration"

# Verbose output
python -m pytest -v
```

### Test Structure

| Test File | Coverage |
|-----------|----------|
| `test_api.py` | API endpoints (health, version, metrics, history, extract, batch) |
| `test_schema.py` | Schema validation, enums, nested objects, optional fields |
| `test_repair_loop.py` | Repair loop execution, retry counting, error classification |
| `test_database.py` | CRUD operations, metrics aggregation, history retrieval |
| `test_utilities.py` | Text cleaning, PII stripping, request ID, confidence, metadata |
| `test_error_handling.py` | Error responses, exception handlers, validation errors |
| `test_integration_mocked.py` | End-to-end pipeline with mocked LLM |
| `test_evaluation.py` | Evaluation records, metrics, repository |

### Code Quality

```bash
# Format code
black --line-length=120 app/ tests/

# Sort imports
isort --profile=black app/ tests/

# Lint
flake8 app/ tests/

# Type check
mypy app/
```

---

## 🐳 Docker Deployment

### Build and Run with Docker

```bash
# Build the backend image
docker build -t extractiq-engine -f backend/Dockerfile .

# Run the container
docker run -p 8000:8000 \
  -e LLM_PROVIDER=featherless \
  -e FEATHERLESS_API_KEY=your_key \
  -e FEATHERLESS_MODEL=deepseek-ai/DeepSeek-V4-Pro \
  -e FEATHERLESS_BASE_URL=https://api.featherless.ai/v1 \
  extractiq-engine
```

### Full Stack with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

This starts:
- **Backend** on port 8000
- **Frontend** on port 5173
- Health checks ensure proper startup order

---

## 🛣️ Roadmap

### Short Term
- [ ] PostgreSQL support (via SQLAlchemy)
- [ ] Authentication & API keys
- [ ] Rate limiting middleware
- [ ] Request validation improvements

### Medium Term
- [ ] Multi-provider LLM routing (LiteLLM)
- [ ] Redis queue + Celery workers
- [ ] Webhook notifications
- [ ] Human review dashboard
- [ ] Export integration (CSV, JSON, PDF)

### Long Term
- [ ] Kubernetes deployment
- [ ] AWS/GCP deployment
- [ ] Real-time monitoring (Prometheus + Grafana)
- [ ] Active learning loop
- [ ] Multi-language schema support
- [ ] A/B testing framework

---

## ⚠️ Known Limitations

1. **SQLite** — Suitable for development/small-scale. For production, migrate to PostgreSQL.
2. **Process-local request IDs** — Current REQ-XXXXXX generator resets on restart. Use UUIDv7 for distributed deployments.
3. **Rate limits** — Free-tier LLM providers have daily token limits. Consider upgrading or adding provider failover.
4. **Single-worker** — The repair loop runs synchronously. For high throughput, implement Celery workers.
5. **Language detection** — Uses `langdetect` which may not detect all languages accurately.
6. **No authentication** — API endpoints are currently open. Add authentication before production deployment.

---

## 🏆 Production Features

✔ Global Error Handling

✔ Request Correlation IDs

✔ Structured Logging

✔ Health Monitoring

✔ Version Endpoint

✔ Analytics

✔ Batch Processing

✔ Docker Support

✔ CI/CD

✔ Environment-based Configuration

---

## 👨‍💻 Author

**Shaik Raihan Basha**

B.Tech CSE | AI/ML Engineer

- GitHub: [@raihanbasha7](https://github.com/raihanbasha7)
- LinkedIn: [Shaik Raihan Basha](https://www.linkedin.com/in/shaikraihanbasha)

---

## 🤝 Contributing

Please read [CONTRIBUTING.md](docs/contributing.md) for details on our code of conduct and the process for submitting pull requests.

---

## 📄 License

MIT License — Copyright (c) 2026 Shaik Raihan Basha

See [LICENSE](LICENSE) for full details.

Copyright (c) 2026 Shaik Raihan Basha