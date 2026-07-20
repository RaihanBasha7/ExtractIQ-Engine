# ExtractIQ Engine

AI-powered structured extraction engine that converts noisy customer support tickets into guaranteed, schema-valid JSON using a Model-Driven Repair Loop with zero regex fallback.

## Project Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Frontend   │────▶│  FastAPI     │────▶│  LLM Provider   │────▶│  SQLite DB   │
│  React/TS   │◀────│  Backend     │◀────│  (Groq/Feather) │     │  Persistence  │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
```

The pipeline flows: **Raw Ticket → Preprocessing (PII strip, normalize) → LLM Extraction → Schema Validation → Repair Loop (if needed) → Guaranteed JSON**

### Key Concepts

- **Model-Driven Repair Loop**: Instead of regex fallback, failed schema validations are fed back to the LLM as repair prompts (up to 3 retries)
- **PII Redaction**: Emails, phone numbers, and ZIP codes are stripped before text reaches external LLM providers
- **Request Correlation**: Every extraction gets a `request_id` threaded through all logs and telemetry
- **Structured JSON Logging**: All events use structured JSON format for log aggregation

## Frontend Structure

```
frontend/src/
├── main.tsx                    # React entry point
├── App.tsx                     # Router + QueryClient
├── types.ts                    # Shared TypeScript interfaces
├── index.css                   # Tailwind + custom styles
├── lib/
│   ├── api.ts                  # HTTP client + response normalizers
│   ├── useExtraction.ts        # Extraction hook with pipeline animation
│   ├── settings.tsx            # Dark mode, animations, API URL context
│   ├── sampleTicket.ts         # Demo sample ticket
│   └── examples.ts             # 5 example tickets for Playground
├── pages/
│   ├── Dashboard.tsx           # / - Overview, KPI cards, charts
│   ├── ExtractTicket.tsx       # /extract - Single extraction with pipeline viz
│   ├── BatchExtract.tsx        # /batch - Batch extraction with progress
│   ├── Playground.tsx          # /playground - Interactive pipeline demo
│   ├── Analytics.tsx           # /analytics - Telemetry charts
│   ├── Health.tsx              # /health - System health status
│   ├── History.tsx             # /history - Paginated extraction history
│   └── SettingsPage.tsx        # /settings - App preferences
└── components/
    ├── Layout.tsx              # App shell (sidebar + navbar)
    ├── Sidebar.tsx             # Collapsible navigation
    ├── Navbar.tsx              # Top bar with health indicator
    ├── Pipeline.tsx            # Pipeline visualization + NodeFlow
    ├── GlassCard.tsx           # Reusable glassmorphic card
    ├── JsonBlock.tsx           # Syntax-highlighted JSON viewer
    ├── ErrorCard.tsx           # Error state with retry
    ├── Skeleton.tsx            # Loading skeleton
    ├── StatusDot.tsx           # Health status indicator
    ├── AnimatedNumber.tsx      # Animated counter
    ├── SectionHeading.tsx      # Section header
    ├── Logo.tsx                # Brand logo SVG
    ├── WorkflowStrip.tsx       # Dashboard workflow visualization
    ├── AnimatedBackground.tsx  # Ambient background effects
    └── ParticleField.tsx       # Canvas particle system
```

## Backend Structure

```
app/
├── main.py                     # FastAPI entry point, middleware, exception handlers
├── config.py                   # Environment-based configuration
├── schema.py                   # Pydantic extraction schema (TicketExtraction)
├── extraction.py               # Model-Driven Repair Loop (LLM calls)
├── preprocessing.py            # Text normalization + PII stripping
├── confidence.py               # Confidence scoring
├── metadata.py                 # Extraction metadata builder
├── logging.py                  # Structured JSON logging
├── repair_logging.py           # Repair attempt telemetry
├── api/
│   ├── routes.py               # Route definitions
│   ├── models.py               # Request/response Pydantic models
│   ├── service.py              # Business-logic orchestrator
│   ├── middleware.py           # Request-ID middleware
│   └── error_models.py         # Error response models
├── database/
│   ├── database.py             # SQLAlchemy engine/session
│   ├── models.py               # ORM models
│   └── repository.py           # Data access layer + stats + history queries
└── services/
    ├── health_service.py       # Dependency health checks
    ├── metrics_service.py      # Metrics aggregation
    └── version_service.py      # Version/runtime metadata
```

## Available API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | System health check with per-dependency status |
| GET | `/version` | Service version, provider, model info |
| POST | `/v1/extract` | Extract structured data from a single ticket |
| POST | `/v1/extract/batch` | Extract from multiple tickets |
| GET | `/v1/metrics` | Aggregated metrics (success rate, latency, etc.) |
| GET | `/v1/history?limit=50&offset=0` | Paginated extraction history |
| GET | `/v1/system` | Combined health + metrics (single request) |
| GET | `/docs` | Interactive Swagger UI |

### Example: Extract a ticket

```bash
curl -X POST http://localhost:8000/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "test-1", "raw_text": "My internet is down since Tuesday. Need help ASAP."}'
```

## Environment Variables

### Backend (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `groq` | LLM provider: `groq` or `featherless` |
| `GROQ_API_KEY` | — | Groq API key (required for Groq) |
| `FEATHERLESS_API_KEY` | — | Featherless API key (required for Featherless) |
| `MODEL` | — | Model name (required for Featherless) |
| `MAX_REPAIR_RETRIES` | `3` | Maximum repair loop retries |
| `DATABASE_URL` | `sqlite:///data/extractions.db` | Database connection string |
| `ENVIRONMENT` | `development` | Deployment environment |

### Frontend (frontend/.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API URL |

## Run Instructions

### Backend

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Deployment Instructions

### Docker

```bash
# Build the backend image
docker build -t extractiq-engine .

# Run the container
docker run -p 8000:8000 \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=your_key_here \
  -v $(pwd)/data:/app/data \
  extractiq-engine
```

### Production Considerations

- Set `ENVIRONMENT=production`
- Configure CORS to your frontend domain
- Use PostgreSQL instead of SQLite for concurrent access
- Add rate limiting and authentication
- Use a process manager (e.g., systemd, supervisor) for the backend
- Build the frontend with `npm run build` and serve via Nginx/CDN

## Performance & Design Decisions

- **No regex fallback**: The repair loop re-prompts the LLM with exact Pydantic errors instead of falling back to brittle regex parsing
- **PII safety**: All sensitive data is redacted before reaching external LLM providers
- **Request correlation**: Every HTTP request gets a unique `request_id` propagated through all subsystems
- **Honest telemetry**: All metrics come from actual database records — no fabricated chart data
- **Min pipeline UX**: Extraction animation runs minimum 5 seconds to show the pipeline stages without blocking the real backend response
