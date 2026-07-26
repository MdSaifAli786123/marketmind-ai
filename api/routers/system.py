from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import func, select

from database.connection import SessionLocal
from database.models import Job
from pipeline.refresh_state import (
    get_refresh_status,
)
from rag.vector_store import get_vector_store


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/system",
    tags=[
        "System",
    ],
)


# ==========================================================
# Helpers
# ==========================================================

def _get_database_job_count() -> int:
    """
    Return the current number of jobs stored in PostgreSQL.
    """

    with SessionLocal() as session:

        statement = select(
            func.count(Job.id)
        )

        count = session.scalar(
            statement
        )

        return int(
            count or 0
        )


def _get_vector_count() -> int | None:
    """
    Return the current number of documents stored in the
    Chroma collection.

    None is returned when the vector store cannot be read.
    This prevents the dataset-status endpoint from failing
    solely because the semantic index is unavailable.
    """

    try:

        vector_store = (
            get_vector_store()
        )

        return int(
            vector_store
            ._collection
            .count()
        )

    except Exception:

        return None


def _safe_dict(
    value: Any,
) -> dict[str, Any]:

    if isinstance(
        value,
        dict,
    ):
        return value

    return {}


# ==========================================================
# Dataset Status
# ==========================================================

@router.get(
    "/dataset-status",
)
def dataset_status() -> dict[str, Any]:
    """
    Return operational information about the current
    job-market dataset and the most recent refresh.

    The endpoint combines:

    - actual PostgreSQL job count
    - actual Chroma document count
    - persisted refresh metadata
    - ingestion metrics
    - enrichment metrics
    - vector synchronization metrics
    """

    # ------------------------------------------------------
    # Current physical state
    # ------------------------------------------------------

    total_jobs = (
        _get_database_job_count()
    )

    total_indexed = (
        _get_vector_count()
    )


    # ------------------------------------------------------
    # Latest persisted refresh
    # ------------------------------------------------------

    refresh_state = (
        get_refresh_status()
    )

    ingestion = _safe_dict(
        refresh_state.get(
            "ingestion"
        )
    )

    vector_sync = _safe_dict(
        refresh_state.get(
            "vector_sync"
        )
    )


    # ------------------------------------------------------
    # Source metrics
    # ------------------------------------------------------

    sources = _safe_dict(
        ingestion.get(
            "sources"
        )
    )


    # ------------------------------------------------------
    # Index consistency
    # ------------------------------------------------------

    vector_index_available = (
        total_indexed is not None
    )

    index_in_sync = (
        vector_index_available
        and total_indexed == total_jobs
    )


    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {

        # ==================================================
        # Current Dataset
        # ==================================================

        "dataset": {
            "total_jobs": (
                total_jobs
            ),

            "total_indexed": (
                total_indexed
            ),

            "vector_index_available": (
                vector_index_available
            ),

            "index_in_sync": (
                index_in_sync
            ),
        },


        # ==================================================
        # Latest Refresh
        # ==================================================

        "refresh": {
            "has_refresh_history": (
                bool(
                    refresh_state.get(
                        "has_refresh_history",
                        False,
                    )
                )
            ),

            "status": (
                refresh_state.get(
                    "status",
                    "never_run",
                )
            ),

            "success": (
                bool(
                    refresh_state.get(
                        "success",
                        False,
                    )
                )
            ),

            "started_at": (
                refresh_state.get(
                    "started_at"
                )
            ),

            "completed_at": (
                refresh_state.get(
                    "completed_at"
                )
            ),

            "duration_seconds": (
                refresh_state.get(
                    "duration_seconds"
                )
            ),

            "saved_at": (
                refresh_state.get(
                    "saved_at"
                )
            ),

            "error": (
                refresh_state.get(
                    "error"
                )
            ),
        },


        # ==================================================
        # Latest Ingestion
        # ==================================================

        "ingestion": {
            "collected": (
                ingestion.get(
                    "collected",
                    0,
                )
            ),

            "transformed": (
                ingestion.get(
                    "transformed",
                    0,
                )
            ),

            "inserted": (
                ingestion.get(
                    "inserted",
                    0,
                )
            ),

            "skipped": (
                ingestion.get(
                    "skipped",
                    0,
                )
            ),

            "transform_failed": (
                ingestion.get(
                    "transform_failed",
                    0,
                )
            ),

            "load_failed": (
                ingestion.get(
                    "load_failed",
                    0,
                )
            ),

            "total_failed": (
                ingestion.get(
                    "total_failed",
                    0,
                )
            ),

            "sources": (
                sources
            ),
        },


        # ==================================================
        # Latest Enrichment
        # ==================================================

        "enrichment": {
            "enriched": (
                refresh_state.get(
                    "enrichment_count",
                    0,
                )
            ),

            "failed": (
                refresh_state.get(
                    "enrichment_failed",
                    0,
                )
            ),
        },


        # ==================================================
        # Latest Vector Synchronization
        # ==================================================

        "vector_sync": {
            "database_documents": (
                vector_sync.get(
                    "database_documents",
                    0,
                )
            ),

            "added": (
                vector_sync.get(
                    "added",
                    0,
                )
            ),

            "updated": (
                vector_sync.get(
                    "updated",
                    0,
                )
            ),

            "unchanged": (
                vector_sync.get(
                    "unchanged",
                    0,
                )
            ),

            "deleted": (
                vector_sync.get(
                    "deleted",
                    0,
                )
            ),

            "total_indexed": (
                vector_sync.get(
                    "total_indexed",
                    0,
                )
            ),

            "mode": (
                vector_sync.get(
                    "mode"
                )
            ),
        },
    }