from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
# app/ is now at backend/app/, so add backend/ to sys.path
sys.path.insert(0, str(_PROJECT_ROOT / "backend"))

from dashboard.config import CACHE_TTL, DEFAULT_DATA_PATH, LOG_LEVEL
from dashboard.layout import render_page

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="ExtractIQ \u2014 Evaluation Dashboard",
    page_icon="\u2699\uFE0F",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    """Dashboard entry point.

    Resolves the JSONL path from environment variable or config default,
    then renders the full dashboard page.
    """
    jsonl_path = os.getenv("EVALUATION_RECORDS_PATH", DEFAULT_DATA_PATH)
    logger.info(
        "Dashboard starting data_path=%s cache_ttl=%d",
        jsonl_path,
        CACHE_TTL,
    )
    render_page(jsonl_path)


if __name__ == "__main__":
    main()
