# Changelog

All notable changes to ExtractIQ Engine are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-07-20

### Added
- Initial release of ExtractIQ Engine
- AI-powered structured extraction from noisy customer support tickets
- Model-Driven Repair Loop for self-correcting extraction
- Pydantic-based strict schema validation with enum enforcement
- PII redaction preprocessing (emails, phones, zip codes)
- RESTful API with FastAPI (extract, batch extract, history, metrics, health)
- Real-time analytics dashboard (Streamlit)
- Modern React frontend (Vite + TailwindCSS + TypeScript)
- Evaluation harness with metrics reporting
- SQLite database with SQLAlchemy ORM
- Structured JSON logging with request correlation
- Confidence scoring for extraction results
- Comprehensive test suite with pytest (80%+ coverage)
- GitHub Actions CI pipeline
- Docker support with multi-stage builds
- Pre-commit hooks for code quality
- Full developer documentation

### Security
- PII redaction before any external LLM API calls
- No secrets in code - all configuration via environment variables
- Request validation via Pydantic schemas
- Global exception handlers preventing stack trace leakage
