from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job


def percentage(
    count: int,
    total: int,
) -> float:
    if total == 0:
        return 0.0

    return count / total * 100


def main() -> None:

    # ==========================================================
    # Load current database state
    # ==========================================================

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

    # ==========================================================
    # Counters
    # ==========================================================

    total_jobs = len(jobs)

    jobs_with_location = 0
    jobs_without_location = 0

    city_known = 0
    state_known = 0
    country_known = 0
    remote_jobs = 0

    countries: Counter[str] = Counter()
    states: Counter[str] = Counter()
    cities: Counter[str] = Counter()

    incomplete: list[
        tuple[
            int,
            str,
            str | None,
            str | None,
            str | None,
            bool,
        ]
    ] = []

    # ==========================================================
    # Inspect current normalized database values
    # ==========================================================

    for job in jobs:

        location = job.location

        if location is None:
            jobs_without_location += 1
            continue

        jobs_with_location += 1

        city = location.city
        state = location.state
        country = location.country
        remote = bool(location.remote)

        if city:
            city_known += 1
            cities[city] += 1

        if state:
            state_known += 1
            states[state] += 1

        if country:
            country_known += 1
            countries[country] += 1

        if remote:
            remote_jobs += 1

        # Keep samples where geographic information remains
        # incomplete after migration.
        if (
            city is None
            or state is None
            or country is None
        ):
            incomplete.append(
                (
                    job.id,
                    job.title,
                    city,
                    state,
                    country,
                    remote,
                )
            )

    # ==========================================================
    # Output
    # ==========================================================

    print()

    print("=" * 78)
    print("POST-MIGRATION LOCATION VERIFICATION")
    print("=" * 78)

    print()

    print("OVERVIEW")
    print("-" * 78)

    print(
        f"Total jobs              : {total_jobs}"
    )

    print(
        f"Jobs with location      : {jobs_with_location}"
    )

    print(
        f"Jobs without location   : {jobs_without_location}"
    )

    print(
        f"Remote jobs             : {remote_jobs}"
    )

    print(
        f"Remote percentage       : "
        f"{percentage(remote_jobs, total_jobs):.2f}%"
    )

    print(
        f"Country coverage        : "
        f"{percentage(country_known, total_jobs):.2f}%"
    )

    print(
        f"City coverage           : "
        f"{percentage(city_known, total_jobs):.2f}%"
    )

    print(
        f"State coverage          : "
        f"{percentage(state_known, total_jobs):.2f}%"
    )

    # ==========================================================
    # Countries
    # ==========================================================

    print()

    print("=" * 78)
    print("COUNTRY DISTRIBUTION")
    print("=" * 78)

    for country, count in countries.most_common():
        print(
            f"{country:<55}{count:>8}"
        )

    # ==========================================================
    # States
    # ==========================================================

    print()

    print("=" * 78)
    print("TOP STATES")
    print("=" * 78)

    for state, count in states.most_common(30):
        print(
            f"{state:<55}{count:>8}"
        )

    # ==========================================================
    # Cities
    # ==========================================================

    print()

    print("=" * 78)
    print("TOP CITIES")
    print("=" * 78)

    for city, count in cities.most_common(30):
        print(
            f"{city:<55}{count:>8}"
        )

    # ==========================================================
    # Important known records
    # ==========================================================

    print()

    print("=" * 78)
    print("KNOWN RECORD CHECKS")
    print("=" * 78)

    check_ids = {
        1,
        4,
        12,
        13,
        14,
        17,
        18,
        24,
        25,
        26,
    }

    jobs_by_id = {
        job.id: job
        for job in jobs
    }

    for job_id in sorted(check_ids):

        job = jobs_by_id.get(job_id)

        if job is None:
            continue

        location = job.location

        print()

        print(
            f"ID      : {job.id}"
        )

        print(
            f"TITLE   : {job.title}"
        )

        if location is None:

            print(
                "LOCATION: NULL"
            )

            continue

        print(
            f"CITY    : {location.city}"
        )

        print(
            f"STATE   : {location.state}"
        )

        print(
            f"COUNTRY : {location.country}"
        )

        print(
            f"REMOTE  : {bool(location.remote)}"
        )

    # ==========================================================
    # Incomplete location samples
    # ==========================================================

    print()

    print("=" * 78)
    print("INCOMPLETE LOCATION SUMMARY")
    print("=" * 78)

    print(
        f"Jobs with at least one missing geographic field: "
        f"{len(incomplete)}"
    )

    print()

    for (
        job_id,
        title,
        city,
        state,
        country,
        remote,
    ) in incomplete[:40]:

        print(
            f"{job_id:<6} | "
            f"{title[:40]:<40} | "
            f"city={city!r} | "
            f"state={state!r} | "
            f"country={country!r} | "
            f"remote={remote}"
        )

    print()

    print("=" * 78)
    print(
        "READ-ONLY VERIFICATION COMPLETE - "
        "DATABASE WAS NOT MODIFIED"
    )
    print("=" * 78)

    print()


if __name__ == "__main__":
    main()