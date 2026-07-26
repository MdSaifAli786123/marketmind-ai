from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job

from pipeline.enrichment.semantic_classifier import (
    SemanticJobClassifier,
)


SAMPLE_SIZE = 30


def main() -> None:

    classifier = SemanticJobClassifier()

    with SessionLocal() as session:

        # Random sample of jobs that rules-v2 could not classify.
        statement = (
            select(Job)
            .options(
                selectinload(Job.skills)
            )
            .where(
                Job.job_family == "Other"
            )
            .order_by(
                func.random()
            )
            .limit(SAMPLE_SIZE)
        )

        jobs = list(
            session.scalars(
                statement
            ).all()
        )

    print()
    print("=" * 110)
    print("REAL-DATA SEMANTIC CLASSIFIER EVALUATION")
    print("=" * 110)
    print(f"Sample size: {len(jobs)}")
    print()

    accepted_count = 0
    other_count = 0

    for index, job in enumerate(
        jobs,
        start=1,
    ):

        skills = [
            skill.name
            for skill in job.skills
        ]

        result = classifier.classify(
            title=job.title,
            description=job.description,
            skills=skills,
        )

        if result.accepted:
            accepted_count += 1

        if result.family == "Other":
            other_count += 1

        print("-" * 110)

        print(
            f"{index:02}. "
            f"ID={job.id} | "
            f"{job.title}"
        )

        print(
            f"    TOP       : "
            f"{result.family}"
        )

        print(
            f"    SCORE     : "
            f"{result.confidence:.4f}"
        )

        print(
            f"    SECOND    : "
            f"{result.second_family}"
        )

        print(
            f"    2ND SCORE : "
            f"{result.second_confidence:.4f}"
        )

        print(
            f"    MARGIN    : "
            f"{result.margin:.4f}"
        )

        print(
            f"    ACCEPTED  : "
            f"{result.accepted}"
        )

    print()
    print("=" * 110)
    print("SUMMARY")
    print("=" * 110)

    print(
        f"Jobs evaluated       : {len(jobs)}"
    )

    print(
        f"Threshold accepted   : {accepted_count}"
    )

    print(
        f"Predicted Other      : {other_count}"
    )

    if jobs:

        acceptance_rate = (
            accepted_count
            / len(jobs)
            * 100
        )

        other_rate = (
            other_count
            / len(jobs)
            * 100
        )

        print(
            f"Acceptance rate      : "
            f"{acceptance_rate:.1f}%"
        )

        print(
            f"Predicted Other rate : "
            f"{other_rate:.1f}%"
        )

    print("=" * 110)


if __name__ == "__main__":
    main()