from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job


OUTPUT_FILE = Path(
    "datasets/evaluation/raw_locations.csv"
)


def main() -> None:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with SessionLocal() as session:

        statement = (
            select(Job)
            .options(
                selectinload(Job.location)
            )
            .order_by(Job.id)
        )

        jobs = list(
            session.scalars(
                statement
            ).all()
        )

    counts: Counter[str] = Counter()

    remote_counts: Counter[str] = Counter()

    for job in jobs:

        location = job.location

        if location is None:
            raw = ""
            remote = False

        else:
            raw = (
                location.country
                or location.city
                or location.state
                or ""
            ).strip()

            remote = bool(
                location.remote
            )

        counts[raw] += 1

        if remote:
            remote_counts[raw] += 1

    rows = sorted(
        counts.items(),
        key=lambda item: (
            -item[1],
            item[0].lower(),
        ),
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.writer(
            file
        )

        writer.writerow(
            [
                "raw_location",
                "job_count",
                "remote_jobs",
            ]
        )

        for raw, count in rows:

            writer.writerow(
                [
                    raw,
                    count,
                    remote_counts[raw],
                ]
            )

    print()
    print("=" * 70)
    print("RAW LOCATION EXPORT")
    print("=" * 70)
    print(
        f"Total jobs           : {len(jobs)}"
    )
    print(
        f"Unique raw locations : {len(counts)}"
    )
    print(
        f"Output               : {OUTPUT_FILE}"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()