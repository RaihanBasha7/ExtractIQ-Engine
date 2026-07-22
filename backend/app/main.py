"""
FastAPI application entry point.

Responsible for:
    - Application lifespan (logging setup, database creation, config logging)
    - Request-ID middleware for end-to-end correlation
    - CORS configuration
    - Global exception handlers that return consistent ``ErrorResponse`` payloads
    - Routing to the extraction API

Every request receives a unique ``request_id`` (``X-Request-ID`` header) that is
propagated through the extraction pipeline so individual extractions can be
traced across API logs, extraction logs, and repair logs.
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.error_models import ErrorResponse
from app.api.middleware import request_id_middleware
from app.api.routes import router
from app.config import (
    ACTIVE_MODEL,
    ACTIVE_PROVIDER,
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    CONTACT,
    LICENSE_INFO,
    MAX_REPAIR_RETRIES,
    SERVERS,
)
from app.database.database import create_database
from app.logging import configure_logging, get_logger, log_event

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(application: FastAPI):
    configure_logging()
    create_database()
    application.state.start_time = time.monotonic()
    log_event(
        logger,
        event="service_startup",
        stage="api",
        status="started",
        provider=ACTIVE_PROVIDER,
        model=ACTIVE_MODEL,
        max_retries=MAX_REPAIR_RETRIES,
        version=APP_VERSION,
    )
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    contact=CONTACT,
    license_info=LICENSE_INFO,
    servers=SERVERS,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    tags_metadata=[
        {"name": "extraction", "description": "Ticket extraction endpoints"},
        {"name": "metrics", "description": "Metrics and statistics endpoints"},
        {"name": "health", "description": "Service health, version, and monitoring"},
    ],
)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.middleware("http")(request_id_middleware)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(router)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------


def _error_response(
    request: Request,
    status_code: int,
    error_code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=message,
            details=details,
            timestamp=datetime.now(timezone.utc),
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(mode="json"),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    log_event(
        logger, event="http_error", stage="api", status="failed", request_id=request_id, status_code=exc.status_code
    )
    return _error_response(
        request,
        status_code=exc.status_code,
        error_code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    log_event(logger, event="request_validation_error", stage="validation", status="failed", request_id=request_id)
    return _error_response(
        request,
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details=exc.errors(),
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    request_id = getattr(request.state, "request_id", None)
    log_event(logger, event="data_validation_error", stage="validation", status="failed", request_id=request_id)
    return _error_response(
        request,
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Data validation failed",
        details=exc.errors(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    log_event(
        logger,
        event="unhandled_exception",
        stage="api",
        status="failed",
        level="ERROR",
        exc_info=True,
        request_id=getattr(request.state, "request_id", None),
        path=request.url.path,
        method=request.method,
    )
    return _error_response(
        request,
        status_code=500,
        error_code="INTERNAL_ERROR",
        message="An internal error occurred",
    )
