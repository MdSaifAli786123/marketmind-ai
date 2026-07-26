from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job


OUTPUT_PATH = Path(
    "datasets/evaluation/job_family_evaluation.csv"
)

OTHER_SAMPLE = 70
CLASSIFIED_SAMPLE = 30

MAX_DESCRIPTION_CHARS = 1200


def get_jobs() -> list[Job]:

    with SessionLocal() as session:

        other_jobs = list(
            session.scalars(
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
                .limit(OTHER_SAMPLE)
            ).all()
        )

        classified_jobs = list(
            session.scalars(
                select(Job)
                .options(
                    selectinload(Job.skills)
                )
                .where(
                    Job.job_family != "Other"
                )
                .order_by(
                    func.random()
                )
                .limit(CLASSIFIED_SAMPLE)
            ).all()
        )

        # Detach while relationships are already loaded.
        jobs = other_jobs + classified_jobs

        for job in jobs:
            session.expunge(job)

        return jobs


def export_dataset(
    jobs: list[Job],
) -> None:

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "job_id",
                "title",
                "description",
                "skills",
                "rules_v2_prediction",
                "human_label",
            ],
        )

        writer.writeheader()

        for job in jobs:

            skills = ", ".join(
                skill.name
                for skill in job.skills
            )

            description = (
                job.description or ""
            )

            description = (
                description[
                    :MAX_DESCRIPTION_CHARS
                ]
            )

            writer.writerow(
                {
                    "job_id": job.id,
                    "title": job.title,
                    "description": description,
                    "skills": skills,
                    "rules_v2_prediction":
                        job.job_family,
                    "human_label": "",
                }
            )


def main() -> None:

    jobs = get_jobs()

    export_dataset(jobs)

    print()
    print("=" * 70)
    print("LABELING DATASET CREATED")
    print("=" * 70)
    print(f"Jobs exported : {len(jobs)}")
    print(f"Output        : {OUTPUT_PATH}")
    print()
    print(
        "Do not change job_id or rules_v2_prediction."
    )
    print(
        "Fill only the human_label column."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()