from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

AUTO_REFRESH_SECONDS: int = int(os.getenv("DASHBOARD_AUTO_REFRESH_SECONDS", "30"))
DEFAULT_DATA_PATH: str = os.getenv(
    "DASHBOARD_DATA_PATH",
    str(_PROJECT_ROOT / "data" / "evaluation_records.jsonl"),
)
MAX_ROWS: int = int(os.getenv("DASHBOARD_MAX_ROWS", "50000"))
CACHE_TTL: int = int(os.getenv("DASHBOARD_CACHE_TTL", "30"))
CHART_HEIGHT: int = int(os.getenv("DASHBOARD_CHART_HEIGHT", "300"))
EXPORT_DIR: str = os.getenv(
    "DASHBOARD_EXPORT_DIR",
    str(_PROJECT_ROOT / "exports"),
)
LOG_LEVEL: str = os.getenv("DASHBOARD_LOG_LEVEL", "INFO")
