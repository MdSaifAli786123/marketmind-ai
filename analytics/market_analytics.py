from __future__ import annotations

from sqlalchemy import func, select

from database.connection import SessionLocal
from database.models import Company, Job, Location


class MarketAnalytics:
    """
    Read-only analytics service for job-market data stored
    in PostgreSQL.

    Provides:
    - Database overview
    - Job-family distribution
    - Experience distribution
    - Job-type distribution
    - Source distribution
    - Geographic coverage
    - Country distribution
    - State distribution
    - City distribution
    - Company distribution
    - Remote-work distribution

    This class never inserts, updates, or deletes records.
    """

    # ==========================================================
    # Overview
    # ==========================================================

    def overview(self) -> dict:

        with SessionLocal() as session:

            total_jobs = session.scalar(
                select(
                    func.count(Job.id)
                )
            ) or 0

            total_companies = session.scalar(
                select(
                    func.count(Company.id)
                )
            ) or 0

            total_locations = session.scalar(
                select(
                    func.count(Location.id)
                )
            ) or 0

            remote_jobs = session.scalar(
                select(
                    func.count(Job.id)
                )
                .join(Job.location)
                .where(
                    Location.remote.is_(True)
                )
            ) or 0

            remote_percentage = (
                remote_jobs / total_jobs * 100
                if total_jobs
                else 0.0
            )

            return {
                "total_jobs": total_jobs,
                "total_companies": total_companies,
                "total_locations": total_locations,
                "remote_jobs": remote_jobs,
                "remote_percentage": round(
                    remote_percentage,
                    2,
                ),
            }

    # ==========================================================
    # Job-family distribution
    # ==========================================================

    def job_family_distribution(
        self,
    ) -> list[dict]:

        with SessionLocal() as session:

            statement = (
                select(
                    Job.job_family,
                    func.count(Job.id).label(
                        "job_count"
                    ),
                )
                .group_by(
                    Job.job_family
                )
                .order_by(
                    func.count(Job.id).desc()
                )
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "job_family":
                        family or "Unknown",
                    "count": count,
                }
                for family, count in rows
            ]

    # ==========================================================
    # Experience distribution
    # ==========================================================

    def experience_distribution(
        self,
    ) -> list[dict]:

        with SessionLocal() as session:

            statement = (
                select(
                    Job.experience_level,
                    func.count(Job.id).label(
                        "job_count"
                    ),
                )
                .group_by(
                    Job.experience_level
                )
                .order_by(
                    func.count(Job.id).desc()
                )
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "experience_level":
                        level or "Unknown",
                    "count": count,
                }
                for level, count in rows
            ]

    # ==========================================================
    # Job-type distribution
    # ==========================================================

    def job_type_distribution(
        self,
    ) -> list[dict]:

        with SessionLocal() as session:

            statement = (
                select(
                    Job.job_type,
                    func.count(Job.id).label(
                        "job_count"
                    ),
                )
                .group_by(
                    Job.job_type
                )
                .order_by(
                    func.count(Job.id).desc()
                )
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "job_type":
                        job_type or "Unknown",
                    "count": count,
                }
                for job_type, count in rows
            ]

    # ==========================================================
    # Source distribution
    # ==========================================================

    def source_distribution(
        self,
    ) -> list[dict]:

        with SessionLocal() as session:

            statement = (
                select(
                    Job.source,
                    func.count(Job.id).label(
                        "job_count"
                    ),
                )
                .group_by(
                    Job.source
                )
                .order_by(
                    func.count(Job.id).desc()
                )
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "source":
                        source or "Unknown",
                    "count": count,
                }
                for source, count in rows
            ]

    # ==========================================================
    # Geographic coverage
    # ==========================================================

    def geographic_coverage(
        self,
    ) -> dict:

        with SessionLocal() as session:

            total_jobs = session.scalar(
                select(
                    func.count(Job.id)
                )
            ) or 0

            jobs_with_country = session.scalar(
                select(
                    func.count(Job.id)
                )
                .join(Job.location)
                .where(
                    Location.country.is_not(None)
                )
            ) or 0

            jobs_with_state = session.scalar(
                select(
                    func.count(Job.id)
                )
                .join(Job.location)
                .where(
                    Location.state.is_not(None)
                )
            ) or 0

            jobs_with_city = session.scalar(
                select(
                    func.count(Job.id)
                )
                .join(Job.location)
                .where(
                    Location.city.is_not(None)
                )
            ) or 0

            return {
                "jobs_with_country":
                    jobs_with_country,

                "country_coverage":
                    round(
                        (
                            jobs_with_country
                            / total_jobs
                            * 100
                        )
                        if total_jobs
                        else 0.0,
                        2,
                    ),

                "jobs_with_state":
                    jobs_with_state,

                "state_coverage":
                    round(
                        (
                            jobs_with_state
                            / total_jobs
                            * 100
                        )
                        if total_jobs
                        else 0.0,
                        2,
                    ),

                "jobs_with_city":
                    jobs_with_city,

                "city_coverage":
                    round(
                        (
                            jobs_with_city
                            / total_jobs
                            * 100
                        )
                        if total_jobs
                        else 0.0,
                        2,
                    ),
            }

    # ==========================================================
    # Countries
    # ==========================================================

    def top_countries(
        self,
        limit: int = 15,
    ) -> list[dict]:

        with SessionLocal() as session:

            statement = (
                select(
                    Location.country,
                    func.count(Job.id).label(
                        "job_count"
                    ),
                )
                .join(
                    Job,
                    Job.location_id
                    == Location.id,
                )
                .where(
                    Location.country.is_not(None)
                )
                .group_by(
                    Location.country
                )
                .order_by(
                    func.count(Job.id).desc()
                )
                .limit(limit)
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "country": country,
                    "count": count,
                }
                for country, count in rows
            ]

    # ==========================================================
    # States
    # ==========================================================

    def top_states(
        self,
        limit: int = 20,
    ) -> list[dict]:

        with SessionLocal() as session:

            statement = (
                select(
                    Location.state,
                    Location.country,
                    func.count(Job.id).label(
                        "job_count"
                    ),
                )
                .join(
                    Job,
                    Job.location_id
                    == Location.id,
                )
                .where(
                    Location.state.is_not(None)
                )
                .group_by(
                    Location.state,
                    Location.country,
                )
                .order_by(
                    func.count(Job.id).desc()
                )
                .limit(limit)
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "state": state,
                    "country":
                        country or "Unknown",
                    "count": count,
                }
                for (
                    state,
                    country,
                    count,
                ) in rows
            ]

    # ==========================================================
    # Cities
    # ==========================================================

    def top_cities(
        self,
        limit: int = 20,
    ) -> list[dict]:

        with SessionLocal() as session:

            statement = (
                select(
                    Location.city,
                    Location.state,
                    Location.country,
                    func.count(Job.id).label(
                        "job_count"
                    ),
                )
                .join(
                    Job,
                    Job.location_id
                    == Location.id,
                )
                .where(
                    Location.city.is_not(None)
                )
                .group_by(
                    Location.city,
                    Location.state,
                    Location.country,
                )
                .order_by(
                    func.count(Job.id).desc()
                )
                .limit(limit)
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "city": city,
                    "state": state,
                    "country":
                        country or "Unknown",
                    "count": count,
                }
                for (
                    city,
                    state,
                    country,
                    count,
                ) in rows
            ]

    # ==========================================================
    # Companies
    # ==========================================================

    def top_companies(
        self,
        limit: int = 15,
    ) -> list[dict]:

        with SessionLocal() as session:

            statement = (
                select(
                    Company.name,
                    func.count(Job.id).label(
                        "job_count"
                    ),
                )
                .join(
                    Job,
                    Job.company_id
                    == Company.id,
                )
                .group_by(
                    Company.id,
                    Company.name,
                )
                .order_by(
                    func.count(Job.id).desc()
                )
                .limit(limit)
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "company": company,
                    "count": count,
                }
                for company, count in rows
            ]

    # ==========================================================
    # Remote distribution
    # ==========================================================

    def remote_distribution(
        self,
    ) -> dict:

        with SessionLocal() as session:

            total = session.scalar(
                select(
                    func.count(Job.id)
                )
            ) or 0

            remote = session.scalar(
                select(
                    func.count(Job.id)
                )
                .join(Job.location)
                .where(
                    Location.remote.is_(True)
                )
            ) or 0

            non_remote = (
                total - remote
            )

            return {
                "remote": remote,
                "non_remote": non_remote,
                "total": total,
                "remote_percentage": round(
                    (
                        remote
                        / total
                        * 100
                    )
                    if total
                    else 0.0,
                    2,
                ),
            }


# ==============================================================
# Console report
# ==============================================================

def main() -> None:

    analytics = MarketAnalytics()

    print()
    print("=" * 78)
    print("AI JOB MARKET ANALYTICS")
    print("=" * 78)

    # ----------------------------------------------------------
    # Overview
    # ----------------------------------------------------------

    print()
    print("OVERVIEW")
    print("-" * 78)

    for key, value in (
        analytics.overview().items()
    ):
        print(
            f"{key:30}: {value}"
        )

    # ----------------------------------------------------------
    # Job families
    # ----------------------------------------------------------

    print()
    print("JOB FAMILY DISTRIBUTION")
    print("-" * 78)

    for row in (
        analytics.job_family_distribution()
    ):
        print(
            f"{row['job_family']:<55}"
            f"{row['count']:>8}"
        )

    # ----------------------------------------------------------
    # Experience
    # ----------------------------------------------------------

    print()
    print("EXPERIENCE DISTRIBUTION")
    print("-" * 78)

    for row in (
        analytics.experience_distribution()
    ):
        print(
            f"{row['experience_level']:<55}"
            f"{row['count']:>8}"
        )

    # ----------------------------------------------------------
    # Job type
    # ----------------------------------------------------------

    print()
    print("JOB TYPE DISTRIBUTION")
    print("-" * 78)

    for row in (
        analytics.job_type_distribution()
    ):
        print(
            f"{row['job_type']:<55}"
            f"{row['count']:>8}"
        )

    # ----------------------------------------------------------
    # Sources
    # ----------------------------------------------------------

    print()
    print("SOURCE DISTRIBUTION")
    print("-" * 78)

    for row in (
        analytics.source_distribution()
    ):
        print(
            f"{row['source']:<55}"
            f"{row['count']:>8}"
        )

    # ----------------------------------------------------------
    # Geographic coverage
    # ----------------------------------------------------------

    print()
    print("GEOGRAPHIC COVERAGE")
    print("-" * 78)

    for key, value in (
        analytics.geographic_coverage().items()
    ):
        print(
            f"{key:30}: {value}"
        )

    # ----------------------------------------------------------
    # Countries
    # ----------------------------------------------------------

    print()
    print("TOP COUNTRIES")
    print("-" * 78)

    for row in (
        analytics.top_countries()
    ):
        print(
            f"{row['country']:<55}"
            f"{row['count']:>8}"
        )

    # ----------------------------------------------------------
    # States
    # ----------------------------------------------------------

    print()
    print("TOP STATES / REGIONS")
    print("-" * 78)

    for row in (
        analytics.top_states()
    ):
        label = (
            f"{row['state']}, "
            f"{row['country']}"
        )

        print(
            f"{label:<55}"
            f"{row['count']:>8}"
        )

    # ----------------------------------------------------------
    # Cities
    # ----------------------------------------------------------

    print()
    print("TOP CITIES")
    print("-" * 78)

    for row in (
        analytics.top_cities()
    ):

        parts = [
            row["city"],
        ]

        if row["state"]:
            parts.append(
                row["state"]
            )

        if row["country"]:
            parts.append(
                row["country"]
            )

        label = ", ".join(
            parts
        )

        print(
            f"{label:<55}"
            f"{row['count']:>8}"
        )

    # ----------------------------------------------------------
    # Companies
    # ----------------------------------------------------------

    print()
    print("TOP COMPANIES")
    print("-" * 78)

    for row in (
        analytics.top_companies()
    ):
        print(
            f"{row['company']:<55}"
            f"{row['count']:>8}"
        )

    # ----------------------------------------------------------
    # Remote
    # ----------------------------------------------------------

    print()
    print("REMOTE DISTRIBUTION")
    print("-" * 78)

    for key, value in (
        analytics.remote_distribution().items()
    ):
        print(
            f"{key:30}: {value}"
        )

    print()
    print("=" * 78)
    print()


if __name__ == "__main__":
    main()