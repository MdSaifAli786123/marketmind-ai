from __future__ import annotations

from sqlalchemy import func, select

from database.connection import SessionLocal
from database.models import Job


def print_distribution(
    session,
    column,
    heading: str,
) -> None:

    print(f"\n{'=' * 70}")
    print(heading)
    print("=" * 70)

    statement = (
        select(
            column,
            func.count(Job.id),
        )
        .group_by(column)
        .order_by(
            func.count(Job.id).desc()
        )
    )

    rows = session.execute(statement).all()

    for value, count in rows:
        print(
            f"{str(value):45} {count:>6}"
        )


def main() -> None:

    with SessionLocal() as session:

        total = session.scalar(
            select(
                func.count(Job.id)
            )
        )

        print("\nJOB ENRICHMENT AUDIT")
        print("=" * 70)
        print(f"Total jobs: {total}")

        # --------------------------------------------------
        # Job-family distribution
        # --------------------------------------------------

        print_distribution(
            session,
            Job.job_family,
            "JOB FAMILY DISTRIBUTION",
        )

        # --------------------------------------------------
        # Experience distribution
        # --------------------------------------------------

        print_distribution(
            session,
            Job.experience_level,
            "EXPERIENCE LEVEL DISTRIBUTION",
        )

        # --------------------------------------------------
        # Employment-type distribution
        # --------------------------------------------------

        print_distribution(
            session,
            Job.job_type,
            "JOB TYPE DISTRIBUTION",
        )

        # --------------------------------------------------
        # Enrichment versions
        # --------------------------------------------------

        print_distribution(
            session,
            Job.enrichment_version,
            "ENRICHMENT VERSION",
        )

        # --------------------------------------------------
        # Example jobs by family
        # --------------------------------------------------

        families = session.scalars(
            select(
                Job.job_family
            )
            .where(
                Job.job_family.is_not(None)
            )
            .distinct()
            .order_by(
                Job.job_family
            )
        ).all()

        print(f"\n{'=' * 70}")
        print("SAMPLE CLASSIFICATIONS")
        print("=" * 70)

        for family in families:

            print(
                f"\n[{family}]"
            )

            jobs = session.scalars(
                select(Job)
                .where(
                    Job.job_family == family
                )
                .order_by(
                    Job.id
                )
                .limit(5)
            ).all()

            for job in jobs:
                print(
                    f"  {job.id:<6} "
                    f"{job.title}"
                )


if __name__ == "__main__":
    main()