from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.analytics import (
    router as analytics_router,
)
from api.routers.intelligence import (
    router as intelligence_router,
)
from api.routers.jobs import (
    router as jobs_router,
)
from api.routers.system import (
    router as system_router,
)
from config.settings import settings


# ==========================================================
# FastAPI Application
# ==========================================================

app = FastAPI(
    title=settings.app_name,

    description=(
        "AI-powered job-market intelligence platform "
        "providing enriched job data, market analytics, "
        "semantic retrieval, grounded LLM-based "
        "job-market intelligence, and operational "
        "dataset monitoring."
    ),

    version=settings.app_version,
)


# ==========================================================
# CORS Configuration
# ==========================================================

# Allow the React frontend to communicate with the FastAPI
# backend during local development.
#
# The permitted frontend origins are managed centrally in
# config/settings.py through settings.cors_origins.

app.add_middleware(
    CORSMiddleware,

    allow_origins=list(
        settings.cors_origins
    ),

    allow_credentials=True,

    allow_methods=[
        "*",
    ],

    allow_headers=[
        "*",
    ],
)


# ==========================================================
# System Root
# ==========================================================

@app.get(
    "/",
    tags=[
        "System",
    ],
)
def root() -> dict[str, str]:
    """
    Basic API information endpoint.
    """

    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running",
    }


# ==========================================================
# Health Check
# ==========================================================

@app.get(
    "/health",
    tags=[
        "System",
    ],
)
def health() -> dict[str, str]:
    """
    Lightweight application health endpoint.

    This endpoint is intentionally inexpensive so that
    Docker, deployment platforms, and monitoring systems
    can use it for application-level health checks.
    """

    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


# ==========================================================
# Routers
# ==========================================================

# Job browsing and job-detail endpoints.
app.include_router(
    jobs_router
)

# Structured market analytics endpoints.
app.include_router(
    analytics_router
)

# Hybrid SQL + RAG + LLM intelligence endpoint.
app.include_router(
    intelligence_router
)

# Operational dataset and pipeline status endpoints.
app.include_router(
    system_router
)