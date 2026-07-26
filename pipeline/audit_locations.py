from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job
from pipeline.enrichment.location_normalizer import (
    LocationNormalizer,
)


def display(value: str | None) -> str:
    """
    Convert None to a readable value for terminal output.
    """
    return value if value else "NULL"


def main() -> None:
    """
    Read existing job locations from PostgreSQL/Neon,
    normalize them in memory, and print an audit report.

    IMPORTANT:
    This script is read-only.
    It does not update the database.
    """

    normalizer = LocationNormalizer()

    # ==========================================================
    # 1. Load jobs and their locations
    # ==========================================================
    #
    # Job.location is a SQLAlchemy relationship.
    #
    # selectinload(Job.location) loads the relationship while
    # the session is still active. This prevents:
    #
    # DetachedInstanceError
    #
    # after the session closes.
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
    # 2. Statistics containers
    # ==========================================================

    total_jobs = len(jobs)

    raw_locations: Counter[str] = Counter()

    countries: Counter[str] = Counter()

    cities: Counter[str] = Counter()

    states: Counter[str] = Counter()

    remote_jobs = 0

    country_known = 0

    city_known = 0

    state_known = 0

    unresolved = 0

    # Store a few normal examples.
    samples: list[
        tuple[
            int,
            str,
            str | None,
            str | None,
            str | None,
            bool,
        ]
    ] = []

    # Store unresolved examples for improving the normalizer.
    unresolved_samples: list[
        tuple[
            int,
            str,
            str,
        ]
    ] = []

    # ==========================================================
    # 3. Process every job
    # ==========================================================

    for job in jobs:

        location = getattr(
            job,
            "location",
            None,
        )

        # ------------------------------------------------------
        # No location relationship
        # ------------------------------------------------------

        if location is None:

            raw_location = None

            source_remote = False

        else:

            # --------------------------------------------------
            # Existing database situation
            # --------------------------------------------------
            #
            # Earlier source transformers stored the raw source
            # location string primarily in:
            #
            # location.country
            #
            # For example:
            #
            # country = "Berlin"
            #
            # Therefore country is checked first while auditing
            # historical data.
            #
            # If it is absent, city/state are used as fallbacks.
            # --------------------------------------------------

            raw_location = (
                getattr(
                    location,
                    "country",
                    None,
                )
                or getattr(
                    location,
                    "city",
                    None,
                )
                or getattr(
                    location,
                    "state",
                    None,
                )
            )

            source_remote = bool(
                getattr(
                    location,
                    "remote",
                    False,
                )
            )

        # ------------------------------------------------------
        # Raw location statistics
        # ------------------------------------------------------

        if raw_location:

            raw_key = str(
                raw_location
            ).strip()

        else:

            raw_key = "NULL"

        raw_locations[
            raw_key
        ] += 1

        # ------------------------------------------------------
        # Normalize
        # ------------------------------------------------------

        result = normalizer.normalize(
            raw_location=raw_location,
            remote=source_remote,
        )

        # ------------------------------------------------------
        # Remote statistics
        # ------------------------------------------------------

        if result.remote:

            remote_jobs += 1

        # ------------------------------------------------------
        # Country statistics
        # ------------------------------------------------------

        if result.country:

            country_known += 1

            countries[
                result.country
            ] += 1

        # ------------------------------------------------------
        # City statistics
        # ------------------------------------------------------

        if result.city:

            city_known += 1

            cities[
                result.city
            ] += 1

        # ------------------------------------------------------
        # State statistics
        # ------------------------------------------------------

        if result.state:

            state_known += 1

            states[
                result.state
            ] += 1

        # ------------------------------------------------------
        # Determine unresolved locations
        # ------------------------------------------------------
        #
        # A location is unresolved when:
        #
        # - some raw location exists
        # - we could not determine the country
        #
        # Pure remote values such as:
        #
        # Remote
        # Worldwide
        #
        # are NOT considered unresolved when they correctly
        # become remote=True with no geographic location.
        # ------------------------------------------------------

        is_pure_remote = (
            result.remote
            and result.city is None
            and result.state is None
            and result.country is None
        )

        is_unresolved = (
            raw_location is not None
            and result.country is None
            and not is_pure_remote
        )

        if is_unresolved:

            unresolved += 1

            if len(
                unresolved_samples
            ) < 50:

                unresolved_samples.append(
                    (
                        job.id,
                        job.title,
                        str(
                            raw_location
                        ),
                    )
                )

        # ------------------------------------------------------
        # Store first 30 normalization examples
        # ------------------------------------------------------

        if len(samples) < 30:

            samples.append(
                (
                    job.id,
                    str(
                        raw_location
                    )
                    if raw_location
                    else "NULL",
                    result.city,
                    result.state,
                    result.country,
                    result.remote,
                )
            )

    # ==========================================================
    # 4. Print audit
    # ==========================================================

    print()

    print(
        "=" * 78
    )

    print(
        "LOCATION NORMALIZATION AUDIT"
    )

    print(
        "=" * 78
    )

    # ==========================================================
    # Overview
    # ==========================================================

    print()

    print(
        "OVERVIEW"
    )

    print(
        "-" * 78
    )

    print(
        f"Normalizer version      : "
        f"{normalizer.VERSION}"
    )

    print(
        f"Total jobs              : "
        f"{total_jobs}"
    )

    print(
        f"Unique raw locations    : "
        f"{len(raw_locations)}"
    )

    print(
        f"Remote jobs             : "
        f"{remote_jobs}"
    )

    if total_jobs > 0:

        remote_percentage = (
            remote_jobs
            / total_jobs
            * 100
        )

        country_percentage = (
            country_known
            / total_jobs
            * 100
        )

        city_percentage = (
            city_known
            / total_jobs
            * 100
        )

        state_percentage = (
            state_known
            / total_jobs
            * 100
        )

        print(
            f"Remote percentage       : "
            f"{remote_percentage:.2f}%"
        )

        print(
            f"Country coverage        : "
            f"{country_percentage:.2f}%"
        )

        print(
            f"City coverage           : "
            f"{city_percentage:.2f}%"
        )

        print(
            f"State coverage          : "
            f"{state_percentage:.2f}%"
        )

    print(
        f"Unresolved jobs         : "
        f"{unresolved}"
    )

    # ==========================================================
    # Top raw locations
    # ==========================================================

    print()

    print(
        "=" * 78
    )

    print(
        "TOP RAW LOCATION VALUES"
    )

    print(
        "=" * 78
    )

    for value, count in (
        raw_locations.most_common(
            30
        )
    ):

        print(
            f"{value:<55}"
            f"{count:>8}"
        )

    # ==========================================================
    # Countries
    # ==========================================================

    print()

    print(
        "=" * 78
    )

    print(
        "NORMALIZED COUNTRIES"
    )

    print(
        "=" * 78
    )

    if countries:

        for value, count in (
            countries.most_common(
                30
            )
        ):

            print(
                f"{value:<55}"
                f"{count:>8}"
            )

    else:

        print(
            "No countries resolved."
        )

    # ==========================================================
    # Cities
    # ==========================================================

    print()

    print(
        "=" * 78
    )

    print(
        "NORMALIZED CITIES"
    )

    print(
        "=" * 78
    )

    if cities:

        for value, count in (
            cities.most_common(
                30
            )
        ):

            print(
                f"{value:<55}"
                f"{count:>8}"
            )

    else:

        print(
            "No cities resolved."
        )

    # ==========================================================
    # States
    # ==========================================================

    print()

    print(
        "=" * 78
    )

    print(
        "NORMALIZED STATES"
    )

    print(
        "=" * 78
    )

    if states:

        for value, count in (
            states.most_common(
                30
            )
        ):

            print(
                f"{value:<55}"
                f"{count:>8}"
            )

    else:

        print(
            "No states resolved."
        )

    # ==========================================================
    # Sample normalizations
    # ==========================================================

    print()

    print(
        "=" * 78
    )

    print(
        "SAMPLE NORMALIZATIONS"
    )

    print(
        "=" * 78
    )

    for (
        job_id,
        raw,
        city,
        state,
        country,
        remote,
    ) in samples:

        print()

        print(
            f"ID      : {job_id}"
        )

        print(
            f"RAW     : {raw}"
        )

        print(
            f"CITY    : {display(city)}"
        )

        print(
            f"STATE   : {display(state)}"
        )

        print(
            f"COUNTRY : {display(country)}"
        )

        print(
            f"REMOTE  : {remote}"
        )

    # ==========================================================
    # Unresolved samples
    # ==========================================================

    print()

    print(
        "=" * 78
    )

    print(
        "UNRESOLVED LOCATION SAMPLES"
    )

    print(
        "=" * 78
    )

    if not unresolved_samples:

        print(
            "No unresolved locations."
        )

    else:

        for (
            job_id,
            title,
            raw,
        ) in unresolved_samples:

            print()

            print(
                f"ID    : {job_id}"
            )

            print(
                f"TITLE : {title}"
            )

            print(
                f"RAW   : {raw}"
            )

    # ==========================================================
    # Final message
    # ==========================================================

    print()

    print(
        "=" * 78
    )

    print(
        "READ-ONLY AUDIT COMPLETE - "
        "DATABASE WAS NOT MODIFIED"
    )

    print(
        "=" * 78
    )

    print()


if __name__ == "__main__":
    main()