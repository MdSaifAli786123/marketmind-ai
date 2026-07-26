from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job
from pipeline.enrichment.skill_extractor import SkillExtractor


def main() -> None:

    extractor = SkillExtractor()

    # ==========================================================
    # Statistics
    # ==========================================================

    total_jobs = 0
    jobs_with_skills = 0
    jobs_without_skills = 0
    total_relationships = 0

    skill_counter: Counter[str] = Counter()
    family_counter: Counter[str] = Counter()

    jobs_without_extraction: list[
        tuple[int, str, str | None]
    ] = []

    # ==========================================================
    # Read jobs
    # ==========================================================

    with SessionLocal() as session:

        jobs = list(
            session.scalars(
                select(Job)
                .options(
                    selectinload(Job.skills)
                )
                .order_by(Job.id)
            ).all()
        )

        total_jobs = len(jobs)

        # ======================================================
        # Extract skills WITHOUT writing to database
        # ======================================================

        for job in jobs:

            current_skills = [
                skill.name
                for skill in job.skills
            ]

            extracted = extractor.extract(
                title=job.title,
                description=job.description,
                source_skills=current_skills,
            )

            if extracted:

                jobs_with_skills += 1

                total_relationships += len(
                    extracted
                )

                skill_counter.update(
                    extracted
                )

                family = (
                    job.job_family
                    or "Unknown"
                )

                family_counter[
                    family
                ] += 1

            else:

                jobs_without_skills += 1

                jobs_without_extraction.append(
                    (
                        job.id,
                        job.title,
                        job.job_family,
                    )
                )

    # ==========================================================
    # Coverage
    # ==========================================================

    coverage = (
        jobs_with_skills
        / total_jobs
        * 100
        if total_jobs
        else 0.0
    )

    average_skills = (
        total_relationships
        / jobs_with_skills
        if jobs_with_skills
        else 0.0
    )

    # ==========================================================
    # Report
    # ==========================================================

    print()
    print("=" * 78)
    print("SKILL EXTRACTION AUDIT")
    print("=" * 78)

    print()
    print("OVERVIEW")
    print("-" * 78)

    print(
        f"Extractor version       : "
        f"{extractor.VERSION}"
    )

    print(
        f"Total jobs              : "
        f"{total_jobs}"
    )

    print(
        f"Jobs with skills        : "
        f"{jobs_with_skills}"
    )

    print(
        f"Jobs without skills     : "
        f"{jobs_without_skills}"
    )

    print(
        f"Coverage                : "
        f"{coverage:.2f}%"
    )

    print(
        f"Total relationships     : "
        f"{total_relationships}"
    )

    print(
        f"Unique extracted skills : "
        f"{len(skill_counter)}"
    )

    print(
        f"Avg skills / covered job: "
        f"{average_skills:.2f}"
    )

    # ==========================================================
    # Top skills
    # ==========================================================

    print()
    print("=" * 78)
    print("TOP EXTRACTED SKILLS")
    print("=" * 78)

    for skill, count in skill_counter.most_common(
        50
    ):
        print(
            f"{skill:<45}"
            f"{count:>8}"
        )

    # ==========================================================
    # Coverage by job family
    # ==========================================================

    print()
    print("=" * 78)
    print("JOBS WITH SKILLS BY JOB FAMILY")
    print("=" * 78)

    for family, count in (
        family_counter.most_common()
    ):
        print(
            f"{family:<50}"
            f"{count:>8}"
        )

    # ==========================================================
    # Sample jobs where nothing was found
    # ==========================================================

    print()
    print("=" * 78)
    print("SAMPLE JOBS WITH NO EXTRACTED SKILLS")
    print("=" * 78)

    for (
        job_id,
        title,
        family,
    ) in jobs_without_extraction[:30]:

        print()

        print(
            f"ID     : {job_id}"
        )

        print(
            f"TITLE  : {title}"
        )

        print(
            f"FAMILY : "
            f"{family or 'Unknown'}"
        )

    print()
    print("=" * 78)
    print(
        "READ-ONLY AUDIT COMPLETE - "
        "DATABASE WAS NOT MODIFIED"
    )
    print("=" * 78)
    print()


if __name__ == "__main__":
    main()