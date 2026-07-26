from __future__ import annotations

import csv
import random
from pathlib import Path

from sqlalchemy import select

from database.connection import SessionLocal
from database.models import Job


OUTPUT_FILE = Path(
    "datasets/evaluation/attribute_evaluation.csv"
)

SAMPLE_SIZE = 100
RANDOM_SEED = 42


def clean(text: str | None) -> str:
    if not text:
        return ""

    return " ".join(
        str(text).split()
    )


def main() -> None:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with SessionLocal() as session:

        jobs = list(
            session.scalars(
                select(Job).order_by(Job.id)
            ).all()
        )

    if not jobs:
        raise RuntimeError(
            "No jobs found in database."
        )

    # ----------------------------------------------------------
    # Split records by current inference status.
    #
    # We deliberately include many Unknown records because
    # those are the cases the next classifier must improve.
    # ----------------------------------------------------------

    both_unknown = []
    experience_unknown = []
    type_unknown = []
    both_known = []

    for job in jobs:

        experience = (
            job.experience_level
            or "Unknown"
        )

        job_type = (
            job.job_type
            or "Unknown"
        )

        exp_missing = (
            experience == "Unknown"
        )

        type_missing = (
            job_type == "Unknown"
        )

        if exp_missing and type_missing:
            both_unknown.append(job)

        elif exp_missing:
            experience_unknown.append(job)

        elif type_missing:
            type_unknown.append(job)

        else:
            both_known.append(job)

    rng = random.Random(
        RANDOM_SEED
    )

    for group in (
        both_unknown,
        experience_unknown,
        type_unknown,
        both_known,
    ):
        rng.shuffle(group)

    # ----------------------------------------------------------
    # Target sample:
    #
    # 50 both unknown
    # 20 experience unknown
    # 20 type unknown
    # 10 both already known
    #
    # If a group is smaller than requested, remaining slots
    # are filled from the unused jobs.
    # ----------------------------------------------------------

    targets = (
        (both_unknown, 50),
        (experience_unknown, 20),
        (type_unknown, 20),
        (both_known, 10),
    )

    selected = []
    selected_ids = set()

    for group, target in targets:

        for job in group:

            if len(
                [
                    item
                    for item in selected
                    if item in group
                ]
            ) >= target:
                break

            if job.id in selected_ids:
                continue

            selected.append(job)
            selected_ids.add(
                job.id
            )

    # Fill remaining slots if necessary.
    remaining = [
        job
        for job in jobs
        if job.id not in selected_ids
    ]

    rng.shuffle(
        remaining
    )

    for job in remaining:

        if len(selected) >= SAMPLE_SIZE:
            break

        selected.append(job)
        selected_ids.add(
            job.id
        )

    selected = selected[
        :SAMPLE_SIZE
    ]

    # Stable output makes later evaluation reproducible.
    selected.sort(
        key=lambda job: job.id
    )

    # ----------------------------------------------------------
    # CSV
    # ----------------------------------------------------------

    fields = [
        "id",
        "title",
        "description",
        "current_experience_level",
        "current_job_type",
        "human_experience_level",
        "human_job_type",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()

        for job in selected:

            writer.writerow(
                {
                    "id": job.id,

                    "title": clean(
                        job.title
                    ),

                    "description": clean(
                        job.description
                    ),

                    "current_experience_level":
                        job.experience_level
                        or "Unknown",

                    "current_job_type":
                        job.job_type
                        or "Unknown",

                    # Intentionally blank.
                    "human_experience_level": "",

                    "human_job_type": "",
                }
            )

    print()
    print("=" * 72)
    print("ATTRIBUTE EVALUATION DATASET CREATED")
    print("=" * 72)

    print(
        f"Database jobs       : {len(jobs)}"
    )

    print(
        f"Evaluation jobs     : {len(selected)}"
    )

    print(
        f"Both unknown pool   : {len(both_unknown)}"
    )

    print(
        f"Experience unknown  : {len(experience_unknown)}"
    )

    print(
        f"Job type unknown    : {len(type_unknown)}"
    )

    print(
        f"Both known          : {len(both_known)}"
    )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print("=" * 72)
    print()


if __name__ == "__main__":
    main()