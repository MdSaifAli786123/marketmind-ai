from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job
from pipeline.enrichment.job_enricher import JobEnricher
from utils.logger import logger


class DatabaseJobEnricher:
    """
    Apply the current JobEnricher version to jobs stored
    in PostgreSQL.

    By default:
    - Jobs never enriched are processed.
    - Jobs enriched by an older classifier version are processed.
    - Jobs already enriched by the current version are skipped.

    force=True:
    - Reprocess every job regardless of enrichment version.
    """

    def __init__(self) -> None:
        self.enricher = JobEnricher()

    def run(
        self,
        force: bool = False,
    ) -> tuple[int, int]:

        enriched = 0
        failed = 0

        with SessionLocal() as session:

            try:
                statement = (
                    select(Job)
                    .options(
                        selectinload(Job.skills)
                    )
                    .order_by(Job.id)
                )

                # --------------------------------------------------
                # Select only stale / unenriched jobs unless forced.
                # --------------------------------------------------

                if not force:
                    statement = statement.where(
                        (
                            Job.enrichment_version.is_(None)
                        )
                        |
                        (
                            Job.enrichment_version
                            != self.enricher.VERSION
                        )
                    )

                jobs = list(
                    session.scalars(
                        statement
                    ).all()
                )

                logger.info(
                    "Jobs requiring enrichment: "
                    f"{len(jobs)}"
                )

                # --------------------------------------------------
                # Enrich jobs
                # --------------------------------------------------

                for job in jobs:

                    try:
                        skill_names = [
                            skill.name
                            for skill in job.skills
                        ]

                        result = self.enricher.enrich(
                            title=job.title or "",
                            description=job.description or "",
                            skills=skill_names,
                        )

                        # ------------------------------------------
                        # Store the complete result produced by the
                        # current enrichment version.
                        # ------------------------------------------

                        job.experience_level = (
                            result.experience_level
                        )

                        job.job_type = (
                            result.job_type
                        )

                        job.job_family = (
                            result.job_family
                        )

                        job.enrichment_version = (
                            self.enricher.VERSION
                        )

                        job.enriched_at = (
                            datetime.now(timezone.utc)
                            .replace(tzinfo=None)
                        )

                        enriched += 1

                    except Exception:

                        failed += 1

                        logger.exception(
                            "Failed to enrich job "
                            f"id={job.id}"
                        )

                # --------------------------------------------------
                # Commit once after processing
                # --------------------------------------------------

                session.commit()

            except Exception:

                session.rollback()

                logger.exception(
                    "Database job enrichment failed."
                )

                raise

        logger.info(
            "Job enrichment complete: "
            f"enriched={enriched}, "
            f"failed={failed}, "
            f"version={self.enricher.VERSION}"
        )

        return enriched, failed