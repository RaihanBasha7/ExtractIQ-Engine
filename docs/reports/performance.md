# Performance Report — ExtractIQ Engine

**Report Date:** 2026-07-20  
**System Version:** 0.1.0  
**Test Environment:** Local (Docker) + Groq API

---

## Performance Measurement Status

**All values in this report are reasoned estimates unless otherwise noted.**  
No formal performance profiling or load testing has been conducted. The numbers below are derived from:
- Python object size introspection for data structure estimates
- Single-sample latency measurements from evaluation runs
- Published provider latency characteristics
- Conservative engineering estimates

A formal performance benchmark (using cProfile, memory_profiler, and a load testing tool like locust or k6) is planned for the next development phase.

---

## 1. Memory Usage

### 1.1 Base Memory Footprint

**Not Yet Profiled.** The following are reasoned estimates based on typical Python/FastAPI application behavior:

| Component | Estimated Idle | Estimated Under Load |
|-----------|---------------|---------------------|
| FastAPI (uvicorn, single worker) | ~48 MB | ~64 MB |
| SQLite (database process) | < 1 MB | ~2 MB |
| Python runtime overhead | ~28 MB | ~28 MB |
| **Total backend (estimated)** | **~76 MB** | **~94 MB** |

Note: These are estimates. Actual memory usage depends on LLM response sizes, concurrent request handling, and Python's memory allocator behavior. Run `memory_profiler` or `tracemalloc` for precise measurements.

### 1.2 Memory Per Extraction Request

**Not Yet Measured.** The following are data structure size estimates:

| Resource | Estimated Allocation |
|----------|--------------------|
| Raw ticket text (in memory) | ~5 KB |
| Preprocessed text | ~4 KB |
| LLM response buffer | ~50 KB |
| Pydantic model instances | ~2 KB |
| Log entries (in-memory buffer) | ~1 KB |
| **Per-request peak (estimated)** | **~62 KB** |

### 1.3 Memory Growth Over Time

**Not Yet Measured.** No long-duration memory monitoring has been performed. Potential growth factors include:
- Python allocator fragmentation (typical ~5-10% over 24h)
- In-memory log buffer accumulation
- Unclosed database connections

---

## 2. CPU Usage

### 2.1 CPU Profile

**Not Yet Profiled.** No cProfile or py-spy output has been collected. The following are reasoned estimates:

| Operation | Estimated CPU Time |
|-----------|-------------------|
| Waiting on LLM API (I/O bound) | < 10 ms |
| Pydantic validation | < 2 ms |
| Text preprocessing | < 1 ms |
| JSON serialization | < 1 ms |
| Database operations | < 3 ms |
| **Total CPU per request (estimated)** | **< 20 ms** |

### 2.2 CPU Usage Under Load

**Not Yet Measured.** No load testing has been performed. The system is expected to be I/O-bound (waiting on LLM API responses) rather than CPU-bound.

---

## 3. Cold Start

**Not Yet Measured.** The following are reasoned estimates:

| Phase | Estimated Duration | Notes |
|-------|-------------------|-------|
| Python interpreter startup | ~240 ms | 3.12, standard library |
| Import all modules | ~480 ms | FastAPI, SQLAlchemy, instructor, etc. |
| SQLite table creation | ~60 ms | CREATE TABLE IF NOT EXISTS |
| Health check (first) | ~1,200 ms | Includes LLM provider API connectivity check |
| First extraction request | ~3,400 ms | Includes model warmup (provider-side) |
| **Total cold start to first result (estimated)** | **~4.4 s** | |

---

## 4. Inference Time

### 4.1 End-to-End Latency

**Measured from 37 Groq evaluation tickets** (see `backend/reports/evaluation_results_full.json`):

| Percentile | Duration |
|------------|----------|
| P50 | 0.71 s |
| P90 | 3.62 s |
| P95 | 3.72 s |
| Mean | 1.47 s |
| Max | 6.24 s |

### 4.2 Phase-Level Breakdown

**Not Yet Measured.** Per-phase timing instrumentation has not been added. The `ExtractionResult` records only total wall-clock time. To measure phase-level breakdown, add timing decorators or middleware.

---

## 5. Maximum Throughput

### 5.1 Measured Throughput

**Not Yet Measured.** No throughput testing has been conducted.

### 5.2 Estimated Throughput

| Configuration | Estimated Max Throughput | Bottleneck |
|--------------|-------------------------|------------|
| Single worker, no repair | ~0.5 req/s | LLM API latency |
| Single worker, with repair | ~0.3 req/s | Repair attempts |
| Single worker, async (uvicorn) | ~0.5 req/s | I/O bound, GIL not limiting |

---

## 6. Scalability Assumptions

### Current Architecture (MVP)
- **Single worker:** All requests serially processed
- **SQLite:** Single-writer, read-committed isolation
- **In-process evaluation:** Evaluation records written to JSONL synchronously
- **LLM provider:** Single-provider, single-model

### Known Ceilings

| Resource | Ceiling | Verification Status |
|----------|---------|-------------------|
| CPU | ~100 req/s (theoretical) | Not tested |
| SQLite writes | ~10 req/s (estimated) | Not tested |
| LLM API (Groq free) | 30 req/min = 0.5 req/s | Confirmed from provider docs |
| LLM API (Featherless free) | Varies by plan | Not tested |
| Network bandwidth | ~1,000 req/s (1 Gbps) | Not tested |

---

## 7. Future Production Scaling

| Phase | Architecture | Estimated Throughput | Key Changes |
|-------|-------------|---------------------|-------------|
| v0.1 (current) | Single worker, SQLite | ~0.5 req/s | — |
| v0.2 (production) | Multi-worker (gunicorn), PostgreSQL | 10-20 req/s | Database + concurrency |
| v0.3 (enterprise) | Celery workers, PostgreSQL + Redis | 50-100 req/s | Async processing + queuing |
| v0.4 (scale) | Horizontal auto-scaling, read replicas | 500+ req/s | K8s + load balancing |

---

## Performance Recommendations

1. **Immediate:** Add performance monitoring (cProfile, memory_profiler) during evaluation runs
2. **Immediate:** Add phase-level timing instrumentation to extraction pipeline
3. **Short-term:** Run formal load test (locust or k6) to measure throughput ceiling
4. **Short-term:** Use paid-tier LLM API to remove rate limit bottleneck
5. **Medium-term:** Implement gunicorn with 4 workers + PostgreSQL
6. **Medium-term:** Move extraction to Celery with Redis result backend

---

*All values in this report are reasoned estimates or single-run measurements unless explicitly marked as measured. Formal performance benchmarking is planned. See `metric_verification_report.md` for detailed audit findings.*
