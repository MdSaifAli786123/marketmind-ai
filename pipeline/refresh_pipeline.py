from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from pipeline.enrichment.database_enricher import (
    DatabaseJobEnricher,
)
from pipeline.refresh_state import (
    save_refresh_state,
)
from pipeline.run import (
    PipelineResult,
    run_pipeline,
)
from rag.vector_store import (
    VectorSyncResult,
    sync_vector_store,
)
from utils.logger import logger


# ==========================================================
# Refresh Result
# ==========================================================

@dataclass
class RefreshResult:
    """
    Summary of one complete job-market refresh cycle.

    Contains:
    - ingestion metrics
    - enrichment metrics
    - vector synchronization metrics
    - execution status
    - execution timing
    """

    started_at: datetime
    completed_at: datetime

    status: str
    success: bool

    ingestion: dict[str, Any]

    enrichment_count: int
    enrichment_failed: int

    vector_sync: dict[str, Any]

    duration_seconds: float

    error: str | None = None

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return asdict(self)


# ==========================================================
# Market Refresh Pipeline
# ==========================================================

class MarketRefreshPipeline:
    """
    Orchestrates one complete refresh of the job-market
    intelligence platform.

    Pipeline:

    External Sources
        -> Collection
        -> Transformation
        -> PostgreSQL
        -> AI/ML Enrichment
        -> Incremental Vector Synchronization
        -> Persistent Refresh State

    Existing modules remain responsible for their own
    processing logic. This class coordinates those stages
    and returns unified execution metrics.
    """

    VERSION = "market-refresh-pipeline-v4"


    # ======================================================
    # Public API
    # ======================================================

    def run(
        self,
    ) -> RefreshResult:

        started_at = datetime.now(
            timezone.utc
        )

        start_time = perf_counter()


        # ==================================================
        # Stage Results
        # ==================================================

        ingestion_result: (
            PipelineResult | None
        ) = None

        vector_result: (
            VectorSyncResult | None
        ) = None

        enrichment_count = 0
        enrichment_failed = 0


        # ==================================================
        # Start
        # ==================================================

        logger.info(
            "=" * 70
        )

        logger.info(
            "Starting complete job-market refresh."
        )

        logger.info(
            f"Refresh pipeline version: "
            f"{self.VERSION}"
        )

        logger.info(
            "=" * 70
        )


        try:

            # ==================================================
            # Stage 1 — Ingestion
            # ==================================================

            logger.info(
                "[1/3] Starting data ingestion..."
            )

            ingestion_result = (
                run_pipeline()
            )

            logger.info(
                "[1/3] Data ingestion completed: "
                f"collected="
                f"{ingestion_result.collected}, "
                f"transformed="
                f"{ingestion_result.transformed}, "
                f"inserted="
                f"{ingestion_result.inserted}, "
                f"skipped="
                f"{ingestion_result.skipped}, "
                f"failed="
                f"{ingestion_result.total_failed}"
            )


            # ==================================================
            # Stage 2 — AI/ML Enrichment
            # ==================================================

            logger.info(
                "[2/3] Starting intelligent "
                "job enrichment..."
            )

            enricher = (
                DatabaseJobEnricher()
            )

            (
                enrichment_count,
                enrichment_failed,
            ) = enricher.run()

            logger.info(
                "[2/3] Job enrichment completed: "
                f"enriched={enrichment_count}, "
                f"failed={enrichment_failed}"
            )


            # ==================================================
            # Stage 3 — Incremental Vector Synchronization
            # ==================================================

            logger.info(
                "[3/3] Starting incremental "
                "vector synchronization..."
            )

            vector_result = (
                sync_vector_store(
                    delete_stale=True,
                )
            )

            logger.info(
                "[3/3] Vector synchronization completed: "
                f"added={vector_result.added}, "
                f"updated={vector_result.updated}, "
                f"unchanged={vector_result.unchanged}, "
                f"deleted={vector_result.deleted}, "
                f"indexed={vector_result.total_indexed}"
            )


            # ==================================================
            # Determine Overall Status
            # ==================================================

            status = (
                self._determine_status(
                    ingestion_result=(
                        ingestion_result
                    ),
                    enrichment_failed=(
                        enrichment_failed
                    ),
                )
            )

            success = (
                status
                in {
                    "success",
                    "partial",
                }
            )


            # ==================================================
            # Complete
            # ==================================================

            completed_at = (
                datetime.now(
                    timezone.utc
                )
            )

            duration = round(
                perf_counter()
                - start_time,
                2,
            )


            # ==================================================
            # Build Final Result
            # ==================================================

            result = RefreshResult(
                started_at=(
                    started_at
                ),

                completed_at=(
                    completed_at
                ),

                status=status,

                success=success,

                ingestion=(
                    ingestion_result
                    .to_dict()
                ),

                enrichment_count=(
                    enrichment_count
                ),

                enrichment_failed=(
                    enrichment_failed
                ),

                vector_sync=(
                    vector_result
                    .to_dict()
                ),

                duration_seconds=(
                    duration
                ),

                error=None,
            )


            # ==================================================
            # Persist Refresh State
            # ==================================================

            save_refresh_state(
                result
            )


            # ==================================================
            # Completion Logging
            # ==================================================

            logger.info(
                "=" * 70
            )

            logger.info(
                "Job-market refresh completed: "
                f"status={result.status}, "
                f"duration="
                f"{result.duration_seconds}s"
            )

            logger.info(
                "Refresh state persisted successfully."
            )

            logger.info(
                "=" * 70
            )

            return result


        # ==================================================
        # Failure Handling
        # ==================================================

        except Exception as exc:

            completed_at = (
                datetime.now(
                    timezone.utc
                )
            )

            duration = round(
                perf_counter()
                - start_time,
                2,
            )

            logger.exception(
                "Job-market refresh failed."
            )


            # --------------------------------------------------
            # Preserve ingestion metrics if Stage 1 completed.
            # --------------------------------------------------

            ingestion_data: dict[
                str,
                Any,
            ] = {}

            if (
                ingestion_result
                is not None
            ):

                ingestion_data = (
                    ingestion_result
                    .to_dict()
                )


            # --------------------------------------------------
            # Preserve vector metrics if Stage 3 completed.
            # --------------------------------------------------

            vector_data: dict[
                str,
                Any,
            ] = {}

            if (
                vector_result
                is not None
            ):

                vector_data = (
                    vector_result
                    .to_dict()
                )


            # --------------------------------------------------
            # Build failed result.
            # --------------------------------------------------

            result = RefreshResult(
                started_at=(
                    started_at
                ),

                completed_at=(
                    completed_at
                ),

                status="failed",

                success=False,

                ingestion=(
                    ingestion_data
                ),

                enrichment_count=(
                    enrichment_count
                ),

                enrichment_failed=(
                    enrichment_failed
                ),

                vector_sync=(
                    vector_data
                ),

                duration_seconds=(
                    duration
                ),

                error=str(
                    exc
                ),
            )


            # --------------------------------------------------
            # Try to persist the failed refresh as well.
            #
            # State persistence failure must not hide the
            # original refresh failure.
            # --------------------------------------------------

            try:

                save_refresh_state(
                    result
                )

            except Exception:

                logger.exception(
                    "Failed to save "
                    "failed-refresh state."
                )


            return result


    # ======================================================
    # Status Evaluation
    # ======================================================

    @staticmethod
    def _determine_status(
        *,
        ingestion_result: PipelineResult,
        enrichment_failed: int,
    ) -> str:
        """
        Determine overall refresh health.

        success:
            Pipeline completed without recorded source,
            transformation, loading, or enrichment failures.

        partial:
            Pipeline completed but one or more individual
            operations failed.

        failed:
            A fatal exception prevented completion. This is
            handled by the main exception handler.
        """

        collection_failures = sum(
            metrics.get(
                "collection_failed",
                0,
            )
            for metrics
            in ingestion_result
            .sources
            .values()
        )

        has_failures = any(
            (
                collection_failures > 0,

                ingestion_result
                .total_failed > 0,

                enrichment_failed > 0,
            )
        )

        if has_failures:

            return "partial"

        return "success"


# ==========================================================
# Convenience Function
# ==========================================================

def refresh_market_data(
) -> RefreshResult:
    """
    Execute one complete market-data refresh.
    """

    pipeline = (
        MarketRefreshPipeline()
    )

    return pipeline.run()


# ==========================================================
# CLI Entry Point
# ==========================================================

if __name__ == "__main__":

    result = (
        refresh_market_data()
    )


    # ======================================================
    # General Status
    # ======================================================

    print()

    print(
        "=" * 70
    )

    print(
        "JOB MARKET REFRESH RESULT"
    )

    print(
        "=" * 70
    )

    print(
        f"Status              : "
        f"{result.status}"
    )

    print(
        f"Success             : "
        f"{result.success}"
    )

    print(
        f"Started             : "
        f"{result.started_at}"
    )

    print(
        f"Completed           : "
        f"{result.completed_at}"
    )

    print(
        f"Duration            : "
        f"{result.duration_seconds}s"
    )


    # ======================================================
    # Ingestion Metrics
    # ======================================================

    print()

    print(
        "INGESTION"
    )

    print(
        "-" * 70
    )

    print(
        f"Collected           : "
        f"{result.ingestion.get('collected', 0)}"
    )

    print(
        f"Transformed         : "
        f"{result.ingestion.get('transformed', 0)}"
    )

    print(
        f"Inserted            : "
        f"{result.ingestion.get('inserted', 0)}"
    )

    print(
        f"Skipped             : "
        f"{result.ingestion.get('skipped', 0)}"
    )

    print(
        f"Transform failures  : "
        f"{result.ingestion.get('transform_failed', 0)}"
    )

    print(
        f"Load failures       : "
        f"{result.ingestion.get('load_failed', 0)}"
    )

    print(
        f"Total failures      : "
        f"{result.ingestion.get('total_failed', 0)}"
    )


    # ======================================================
    # Enrichment Metrics
    # ======================================================

    print()

    print(
        "AI/ML ENRICHMENT"
    )

    print(
        "-" * 70
    )

    print(
        f"Jobs enriched       : "
        f"{result.enrichment_count}"
    )

    print(
        f"Failures            : "
        f"{result.enrichment_failed}"
    )


    # ======================================================
    # Vector Synchronization Metrics
    # ======================================================

    print()

    print(
        "VECTOR SYNCHRONIZATION"
    )

    print(
        "-" * 70
    )

    print(
        f"Database documents  : "
        f"{result.vector_sync.get('database_documents', 0)}"
    )

    print(
        f"Vectors added       : "
        f"{result.vector_sync.get('added', 0)}"
    )

    print(
        f"Vectors updated     : "
        f"{result.vector_sync.get('updated', 0)}"
    )

    print(
        f"Vectors unchanged   : "
        f"{result.vector_sync.get('unchanged', 0)}"
    )

    print(
        f"Vectors deleted     : "
        f"{result.vector_sync.get('deleted', 0)}"
    )

    print(
        f"Total indexed       : "
        f"{result.vector_sync.get('total_indexed', 0)}"
    )


    # ======================================================
    # Source Metrics
    # ======================================================

    sources = (
        result.ingestion.get(
            "sources",
            {},
        )
    )

    if sources:

        print()

        print(
            "SOURCE METRICS"
        )

        print(
            "-" * 70
        )

        for (
            source_name,
            metrics,
        ) in sources.items():

            print(
                f"{source_name}: "
                f"{metrics}"
            )


    # ======================================================
    # Error
    # ======================================================

    if result.error:

        print()

        print(
            "ERROR"
        )

        print(
            "-" * 70
        )

        print(
            result.error
        )


    print()

    print(
        "=" * 70
    )