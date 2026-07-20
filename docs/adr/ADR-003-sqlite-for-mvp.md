# ADR-003: SQLite for MVP Persistence

**Status:** Accepted  
**Date:** 2026-07-20  
**Deciders:** Engineering Team  
**References:** `backend/app/database/database.py`, `backend/app/database/models.py`

---

## Context

The MVP requires persistent storage for:
1. Raw ticket text (for debugging and reprocessing)
2. Extraction results (for history, analytics, and evaluation)
3. Evaluation records (for quality monitoring and benchmarking)

The storage solution must be operable with zero infrastructure setup (no database server, no schema migrations tooling) for local development and evaluation runs.

---

## Decision

Use **SQLite** via **SQLAlchemy 2.0** as the persistence backend for the MVP phase.

### Configuration
- Database file: `data/extractions.db` (configurable via `DB_PATH` setting)
- Engine: `sqlite+aiosqlite:///` (async support via aiosqlite)
- Connection: Single-file, no server process

### ORM Models
- `RawTicket`: Original text, cleaned text, language, timestamp
- `ExtractionResult`: Structured JSON, validation status, retry count, latency

---

## Consequences

### Positive
- **Zero infrastructure:** No database server installation, no Docker dependency for local runs
- **Portable:** Database is a single file — easy to back up, share, or archive
- **SQLAlchemy abstraction:** Migration to PostgreSQL requires changing only the connection string and driver
- **ACID compliance:** SQLite provides transactional guarantees sufficient for single-worker deployments

### Negative
- **Write contention:** SQLite locks the entire database file during writes. Concurrent requests in multi-worker deployments will cause `database is locked` errors.
- **No user management:** No role-based access, no connection pooling
- **Limited concurrency:** Practical limit of ~5-10 concurrent writes/second
- **No native JSON operations:** JSON queries are supported but not performant at scale

### Scale Ceiling
- **Ticket volume:** SQLite is viable up to ~10,000 extraction results
- **Read concurrency:** Adequate for single-user dashboards and analytics
- **Write concurrency:** Suitable for single-worker extraction (sequential writes)

---

## Migration Path

| Phase | Backend | When |
|-------|---------|------|
| MVP (v0.1) | SQLite | Now |
| Production (v0.2) | PostgreSQL via SQLAlchemy | When concurrent requests exceed 5/s |
| Enterprise (v0.3) | PostgreSQL + read replicas | When analytics queries impact write performance |

The SQLAlchemy abstraction layer ensures the migration requires only:
1. Changing `DATABASE_URL` in settings
2. Adding `psycopg2` or `asyncpg` to dependencies
3. Running a proper migration tool (Alembic)

---

## Alternatives Considered

### PostgreSQL (direct)
- **Rejected for MVP.** Requires database server installation, Docker dependency, and ongoing maintenance overhead inappropriate for a development-phase project.

### JSON File Storage
- **Rejected.** No query capability, no concurrency control, no transactional safety. Used only for evaluation records (append-only JSONL) where these properties are acceptable.

### In-Memory Storage
- **Rejected.** Data loss on restart makes this unsuitable for any persistence requirement.
