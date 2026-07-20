# ExtractIQ Evaluation Dashboard

A Streamlit-based evaluation harness for the ExtractIQ structured extraction
pipeline.

## Architecture

```
dashboard/
├── __init__.py          # Public API re-exports
├── app.py               # Entry point — page config, main()
├── config.py            # Dashboard settings (env-driven)
├── styles.py            # Design tokens + CSS
├── loaders.py           # Data loading, caching, filtering, metrics
├── components.py        # UI renderers (header, KPI cards, table)
├── charts.py            # 8 reusable Plotly figure factories
├── analytics.py         # Executive summary, insight cards, trend charts
├── error_analysis.py    # Confusion matrix, category perf, field analysis, etc.
├── exporter.py          # CSV/JSON export helpers
├── health.py            # Diagnostics & health checks
├── layout.py            # Page orchestration — wires everything together
└── README.md            # This file
```

### Data flow

```
JSONL file
  └── EvaluationRepository.load()
        └── loaders.load_data()          ← @st.cache_data (TTL=30s)
              └── apply_filters()         ← respects sidebar filters
                    ├── compute_metrics() → KPI cards
                    ├── render_analytics_section()
                    │     ├── Executive summary + insight cards
                    │     └── 8 trend/distribution charts (charts.py)
                    ├── render_error_analysis_section()
                    │     ├── Confusion matrix (heatmap)
                    │     ├── Category performance (table)
                    │     ├── Failure breakdown (table)
                    │     ├── Field analysis (chart + table)
                    │     ├── Retry analysis (chart + table)
                    │     ├── Latency vs accuracy (scatter)
                    │     └── Error inspector (interactive table)
                    └── Recent evaluations table
```

## How to run

```bash
# From the project root
streamlit run dashboard/app.py

# With a custom data path
EVALUATION_RECORDS_PATH=/custom/path/records.jsonl streamlit run dashboard/app.py
```

## Configuration

All dashboard settings are in `dashboard/config.py` and can be overridden
via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_AUTO_REFRESH_SECONDS` | `30` | Auto-refresh interval |
| `DASHBOARD_DATA_PATH` | `data/evaluation_records.jsonl` | JSONL file path |
| `DASHBOARD_MAX_ROWS` | `50000` | Max rows before truncation |
| `DASHBOARD_CACHE_TTL` | `30` | Streamlit cache TTL (seconds) |
| `DASHBOARD_CHART_HEIGHT` | `300` | Default chart height (px) |
| `DASHBOARD_EXPORT_DIR` | `exports/` | Export output directory |
| `DASHBOARD_LOG_LEVEL` | `INFO` | Logging level |

## How evaluation recording works

1. `app/api/service.py` calls `EvaluationCollector.add()` after every
   extraction (both success and failure paths).
2. The collector builds an `EvaluationRecord` with schema validity, field
   accuracy, latency, retry info, etc.
3. `EvaluationRepository.save()` appends the record as a JSON line to
   `data/evaluation_records.jsonl`.
4. The dashboard reads this file via `EvaluationRepository.load()`.

Recording failures never crash extraction — the collector is wrapped
inside the service's exception handler.

## How exports work

Export buttons appear in the sidebar after data loads.

- **Filtered Data (CSV)**: current view after sidebar filters
- **Metrics (JSON)**: aggregate KPIs
- **Category Perf (CSV)**: per-category accuracy breakdown
- **Failure Breakdown (CSV)**: failure reason grouping
- **Field Analysis (CSV)**: per-field error rates

Files are written to `exports/` with timestamped filenames:
`metrics_20260101_120000.json`.

## Interpreting metrics

| Metric | What it means |
|--------|---------------|
| Schema Valid % | Fraction of extractions that passed Pydantic validation |
| Field Accuracy % | Fraction of expected fields that matched predictions |
| Repair Success % | Of repair attempts, fraction that produced valid output |
| Average Latency | Mean extraction time across all tickets |
| Average Retries | Mean repair attempts per ticket |
| Infrastructure Errors | Failures from rate limits, timeouts, provider errors |
| Extraction Failures | Tickets that failed after exhausting all retries |

### Confusion matrix

Rows = expected category, columns = predicted category.
Diagonal = correct predictions. Off-diagonal = misclassifications.

### Field error analysis

Uses the `field_breakdown` dict from each `EvaluationRecord`:
- **match**: predicted value equals expected
- **mismatch**: predicted value differs from expected
- **missing**: field present in expected but absent from prediction

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| "No evaluation records found" | JSONL file missing or empty | Run extraction pipeline first |
| Dashboard shows 0 records | Wrong data path | Set `EVALUATION_RECORDS_PATH` |
| KPI cards show N/A | No field accuracy data | Ensure expected data was provided to collector |
| Exports fail | Export directory unwritable | Check `DASHBOARD_EXPORT_DIR` |
| Auto-refresh not updating | Cache TTL not expired | Click "Refresh Data" button |
| Charts blank | No matching data after filters | Widen filter criteria |

## Dependencies

- `streamlit>=1.35`
- `pandas>=2.2`
- `plotly>=5.20`

All listed in the project `requirements.txt`.
