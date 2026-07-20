# ExtractIQ Engine — Directory Tree

```
ExtractIQ-Engine/
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── error_models.py
│   │   │   ├── middleware.py
│   │   │   ├── models.py
│   │   │   ├── routes.py
│   │   │   └── service.py
│   │   ├── database/
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── repository.py
│   │   ├── evaluation/
│   │   │   ├── collector.py
│   │   │   ├── metrics.py
│   │   │   ├── models.py
│   │   │   └── repository.py
│   │   ├── services/
│   │   │   ├── health_service.py
│   │   │   ├── metrics_service.py
│   │   │   └── version_service.py
│   │   ├── confidence.py
│   │   ├── config.py
│   │   ├── extraction.py
│   │   ├── logging.py
│   │   ├── main.py
│   │   ├── metadata.py
│   │   ├── preprocessing.py
│   │   ├── repair_logging.py
│   │   ├── schema.py
│   │   └── settings.py
│   ├── data/
│   │   ├── evaluation_records.jsonl
│   │   ├── extractions.db
│   │   ├── raw_customer_support_tickets.csv
│   │   ├── stress_tickets.jsonl
│   │   └── tickets_sample.jsonl
│   ├── reports/
│   │   ├── evaluation_report.md
│   │   └── evaluation_results_full.json
│   ├── scripts/
│   │   ├── prepare_dataset.py
│   │   ├── run_evaluation.py
│   │   └── run_full_evaluation.py
│   ├── tests/
│   │   ├── data/              # 10 test ticket text files
│   │   ├── golden/            # 10 golden annotation JSON files
│   │   ├── conftest.py
│   │   ├── final_test.py
│   │   └── test_*.py          # 8 test files
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── pytest.ini
│   ├── requirements-dev.txt
│   └── requirements.txt
├── dashboard/
│   ├── app.py
│   ├── analytics.py
│   ├── charts.py
│   ├── components.py
│   ├── config.py
│   ├── error_analysis.py
│   ├── exporter.py
│   ├── health.py
│   ├── layout.py
│   ├── loaders.py
│   ├── styles.py
│   └── README.md
├── data/
│   └── evaluation_records.jsonl
├── docs/
│   ├── adr/
│   │   ├── ADR-001-repair-loop.md
│   │   ├── ADR-002-why-pydantic.md
│   │   ├── ADR-003-sqlite-for-mvp.md
│   │   ├── ADR-004-why-no-regex.md
│   │   └── ADR-005-why-instructor.md
│   ├── reports/
│   │   ├── audit_report.md
│   │   ├── benchmark.md
│   │   ├── evaluation.md
│   │   ├── failure_analysis.md
│   │   ├── metric_verification_report.md
│   │   ├── performance.md
│   │   └── project_metrics.md
│   ├── screenshots/
│   │   ├── analytics.png
│   │   ├── dashboard.png
│   │   ├── extraction.png
│   │   ├── health.png
│   │   ├── history.png
│   │   ├── landing.png
│   │   └── playground.png
│   ├── api.md
│   ├── api_examples.md
│   ├── architecture.md
│   ├── architecture.png
│   ├── banner.png
│   ├── changelog.md
│   ├── code_of_conduct.md
│   ├── contributing.md
│   ├── deployment.md
│   ├── logo.png
│   ├── model-card.md
│   ├── observability.md
│   ├── roadmap.md
│   ├── security.md
│   └── workflow.md
├── frontend/
│   ├── src/
│   │   ├── components/        # 17 React components
│   │   ├── lib/               # API client & utilities
│   │   ├── pages/             # 8 page components
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── types.ts
│   │   └── index.css
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── .github/
│   └── workflows/
│       └── ci.yml
├── reports/                   # Generated outputs
├── .dockerignore
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE
├── README.md
└── docker-compose.yml
```
