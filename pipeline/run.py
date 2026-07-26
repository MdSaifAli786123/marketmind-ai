from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from pydantic import ValidationError

from collectors.arbeitnow import ArbeitnowCollector
from collectors.remoteok import RemoteOKCollector
from domain.job import Job
from pipeline.arbeitnow_transformer import ArbeitnowTransformer
from pipeline.load import JobLoader
from pipeline.remoteok_transformer import RemoteOKTransformer
from pipeline.transformer import BaseTransformer
from utils.logger import logger


# ==========================================================
# Pipeline Result
# ==========================================================

@dataclass
class PipelineResult:
    """
    Summary of one ingestion pipeline execution.
    """

    collected: int
    transformed: int

    inserted: int
    skipped: int

    transform_failed: int
    load_failed: int

    total_failed: int

    sources: dict[str, dict[str, int]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ==========================================================
# Transform Jobs
# ==========================================================

def transform_jobs(
    raw_jobs,
    transformer: BaseTransformer,
) -> tuple[list[Job], int]:

    jobs: list[Job] = []
    failed = 0

    for raw_job in raw_jobs:

        try:

            job = transformer.transform(
                raw_job
            )

            jobs.append(
                job
            )

        except (
            ValidationError,
            ValueError,
            TypeError,
        ):

            failed += 1

            logger.exception(
                f"Failed to transform "
                f"{raw_job.source} job."
            )

    return jobs, failed


# ==========================================================
# Run Pipeline
# ==========================================================

def run_pipeline() -> PipelineResult:
    """
    Execute the complete collection, transformation,
    and PostgreSQL loading pipeline.

    Returns structured execution metrics so higher-level
    services can inspect the ingestion result.
    """

    sources = [
        (
            RemoteOKCollector(),
            RemoteOKTransformer(),
        ),
        (
            ArbeitnowCollector(
                max_pages=5
            ),
            ArbeitnowTransformer(),
        ),
    ]

    all_jobs: list[Job] = []

    total_collected = 0
    total_transform_failed = 0

    source_metrics: dict[
        str,
        dict[str, int],
    ] = {}


    # ======================================================
    # Collection + Transformation
    # ======================================================

    for collector, transformer in sources:

        source_name = str(
            collector.source_name
        )

        logger.info(
            f"Collecting jobs from "
            f"{source_name}..."
        )

        try:

            raw_jobs = (
                collector.collect()
            )

        except Exception:

            logger.exception(
                f"Collection failed for "
                f"{source_name}."
            )

            source_metrics[
                source_name
            ] = {
                "collected": 0,
                "transformed": 0,
                "transform_failed": 0,
                "collection_failed": 1,
            }

            continue


        # --------------------------------------------------
        # Collection metrics
        # --------------------------------------------------

        collected_count = len(
            raw_jobs
        )

        total_collected += (
            collected_count
        )


        # --------------------------------------------------
        # Transformation
        # --------------------------------------------------

        jobs, failed = (
            transform_jobs(
                raw_jobs,
                transformer,
            )
        )

        transformed_count = len(
            jobs
        )

        all_jobs.extend(
            jobs
        )

        total_transform_failed += (
            failed
        )


        # --------------------------------------------------
        # Source metrics
        # --------------------------------------------------

        source_metrics[
            source_name
        ] = {
            "collected": collected_count,
            "transformed": transformed_count,
            "transform_failed": failed,
            "collection_failed": 0,
        }


        logger.info(
            f"{source_name}: "
            f"collected={collected_count}, "
            f"transformed={transformed_count}, "
            f"failed={failed}"
        )


    # ======================================================
    # Load into PostgreSQL
    # ======================================================

    inserted = 0
    skipped = 0
    load_failed = 0

    if all_jobs:

        logger.info(
            "Loading transformed jobs "
            "into PostgreSQL..."
        )

        loader = JobLoader()

        (
            inserted,
            skipped,
            load_failed,
        ) = loader.load(
            all_jobs
        )

    else:

        logger.warning(
            "No transformed jobs available "
            "for database loading."
        )


    # ======================================================
    # Final Metrics
    # ======================================================

    transformed = len(
        all_jobs
    )

    total_failed = (
        total_transform_failed
        + load_failed
    )


    result = PipelineResult(
        collected=total_collected,

        transformed=transformed,

        inserted=inserted,

        skipped=skipped,

        transform_failed=(
            total_transform_failed
        ),

        load_failed=load_failed,

        total_failed=total_failed,

        sources=source_metrics,
    )


    # ======================================================
    # Logging
    # ======================================================

    logger.info(
        "Pipeline complete: "
        f"collected={result.collected}, "
        f"transformed={result.transformed}, "
        f"inserted={result.inserted}, "
        f"skipped={result.skipped}, "
        f"failed={result.total_failed}"
    )

    return result


# ==========================================================
# CLI Entry Point
# ==========================================================

if __name__ == "__main__":

    result = run_pipeline()

    print()

    print(
        "=" * 70
    )

    print(
        "INGESTION PIPELINE RESULT"
    )

    print(
        "=" * 70
    )

    print(
        f"Collected        : "
        f"{result.collected}"
    )

    print(
        f"Transformed      : "
        f"{result.transformed}"
    )

    print(
        f"Inserted         : "
        f"{result.inserted}"
    )

    print(
        f"Skipped          : "
        f"{result.skipped}"
    )

    print(
        f"Transform failed : "
        f"{result.transform_failed}"
    )

    print(
        f"Load failed      : "
        f"{result.load_failed}"
    )

    print(
        f"Total failed     : "
        f"{result.total_failed}"
    )

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
    ) in result.sources.items():

        print(
            f"{source_name}: "
            f"{metrics}"
        )

    print(
        "=" * 70
    )