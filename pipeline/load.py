from __future__ import annotations

from database.models import (
    Company as CompanyModel,
    Job as JobModel,
    Location as LocationModel,
    Skill as SkillModel,
)
from database.repositories.unit_of_work import UnitOfWork
from domain.job import Job as DomainJob
from pipeline.enrichment.skill_normalizer import SkillNormalizer
from utils.logger import logger


LocationKey = tuple[
    str | None,
    str | None,
    str | None,
    bool,
]


class JobLoader:
    """
    Bulk loader for validated Job domain objects.

    Responsibilities:
    - Deduplicate incoming jobs by source URL.
    - Skip jobs already stored in PostgreSQL.
    - Reuse existing companies, locations, and skills.
    - Normalize skills into canonical names.
    - Create missing entities in batches.
    - Persist jobs and relationships in one transaction.
    - Minimize database round trips to Neon PostgreSQL.
    """

    def load(
        self,
        jobs: list[DomainJob],
    ) -> tuple[int, int, int]:

        if not jobs:
            logger.info(
                "Database load complete: "
                "inserted=0, skipped=0, failed=0"
            )
            return 0, 0, 0

        inserted = 0
        skipped = 0
        failed = 0

        # --------------------------------------------------
        # 1. Deduplicate incoming jobs in memory
        # --------------------------------------------------
        unique_jobs: dict[str, DomainJob] = {}

        for job in jobs:
            source_url = str(job.source_url)

            if source_url in unique_jobs:
                skipped += 1
                continue

            unique_jobs[source_url] = job

        # --------------------------------------------------
        # 2. Begin database transaction
        # --------------------------------------------------
        with UnitOfWork() as uow:
            try:

                # --------------------------------------------------
                # 3. Find jobs already stored in PostgreSQL
                # --------------------------------------------------
                existing_urls = (
                    uow.jobs.get_existing_source_urls(
                        set(unique_jobs.keys())
                    )
                )

                new_jobs = [
                    job
                    for source_url, job in unique_jobs.items()
                    if source_url not in existing_urls
                ]

                skipped += len(existing_urls)

                # --------------------------------------------------
                # 4. Nothing new to insert
                # --------------------------------------------------
                if not new_jobs:
                    logger.info(
                        f"Database load complete: "
                        f"inserted=0, "
                        f"skipped={skipped}, "
                        f"failed=0"
                    )

                    return 0, skipped, 0

                # --------------------------------------------------
                # 5. Collect unique company names
                # --------------------------------------------------
                company_names = {
                    self._company_name(job)
                    for job in new_jobs
                }

                # Fetch existing companies in one query.
                companies = (
                    uow.companies.get_by_names(
                        company_names
                    )
                )

                # --------------------------------------------------
                # 6. Create missing companies
                # --------------------------------------------------
                for job in new_jobs:
                    company_name = self._company_name(job)

                    if company_name in companies:
                        continue

                    company = CompanyModel(
                        name=company_name,
                        website=job.company.website,
                    )

                    uow.companies.add(company)

                    companies[company_name] = company

                # --------------------------------------------------
                # 7. Collect and normalize unique skills
                # --------------------------------------------------
                all_skill_names: set[str] = set()

                for job in new_jobs:
                    all_skill_names.update(
                        self._skill_names(job)
                    )

                # Fetch existing skills in one query.
                skills = (
                    uow.skills.get_by_names(
                        all_skill_names
                    )
                )

                # --------------------------------------------------
                # 8. Create missing normalized skills
                # --------------------------------------------------
                for skill_name in all_skill_names:
                    if skill_name in skills:
                        continue

                    skill = SkillModel(
                        name=skill_name
                    )

                    uow.skills.add(skill)

                    skills[skill_name] = skill

                # --------------------------------------------------
                # 9. Fetch existing locations
                # --------------------------------------------------
                # LocationRepository returns:
                #
                # {
                #     (city, state, country, remote): Location
                # }
                #
                # This avoids querying Neon separately
                # for every job location.
                locations = (
                    uow.locations.get_all_lookup()
                )

                # --------------------------------------------------
                # 10. Create missing locations
                # --------------------------------------------------
                for job in new_jobs:
                    location_key = (
                        self._location_key(job)
                    )

                    if location_key in locations:
                        continue

                    location = LocationModel(
                        city=location_key[0],
                        state=location_key[1],
                        country=location_key[2],
                        remote=location_key[3],
                    )

                    uow.locations.add(location)

                    locations[location_key] = location

                # --------------------------------------------------
                # 11. Flush shared entities
                # --------------------------------------------------
                # Generates IDs for newly created:
                #
                # - companies
                # - skills
                # - locations
                #
                # without committing yet.
                uow.flush()

                # --------------------------------------------------
                # 12. Create jobs and relationships
                # --------------------------------------------------
                for job in new_jobs:
                    try:
                        company_name = (
                            self._company_name(job)
                        )

                        location_key = (
                            self._location_key(job)
                        )

                        skill_names = (
                            self._skill_names(job)
                        )

                        company = companies[
                            company_name
                        ]

                        location = locations[
                            location_key
                        ]

                        job_skills = [
                            skills[skill_name]
                            for skill_name in skill_names
                        ]

                        job_model = JobModel(
                            title=job.title.strip(),
                            description=job.description,
                            source=job.source,
                            source_url=str(
                                job.source_url
                            ),
                            posted_at=job.posted_at,
                            salary=job.salary,
                            job_type=job.job_type.value,
                            experience_level=(
                                job.experience_level.value
                            ),
                            company_id=company.id,
                            location_id=location.id,
                            skills=job_skills,
                        )

                        uow.jobs.add(job_model)

                        inserted += 1

                    except (
                        KeyError,
                        TypeError,
                        ValueError,
                    ):
                        failed += 1

                        logger.exception(
                            f"Failed to prepare job: "
                            f"{job.title}"
                        )

                # --------------------------------------------------
                # 13. Commit batch
                # --------------------------------------------------
                uow.commit()

            except Exception:
                # Any database-level failure rolls back
                # the entire current batch.
                uow.rollback()

                logger.exception(
                    "Bulk database load failed."
                )

                raise

        # --------------------------------------------------
        # 14. Final statistics
        # --------------------------------------------------
        logger.info(
            f"Database load complete: "
            f"inserted={inserted}, "
            f"skipped={skipped}, "
            f"failed={failed}"
        )

        return inserted, skipped, failed

    # ======================================================
    # Normalization helpers
    # ======================================================

    @staticmethod
    def _company_name(
        job: DomainJob,
    ) -> str:
        """
        Normalize company name before database lookup.
        """

        name = job.company.name.strip()

        return name or "Unknown"

    @staticmethod
    def _skill_names(
        job: DomainJob,
    ) -> list[str]:
        """
        Normalize skill aliases into canonical skill names.

        Examples:

        ML               -> machine learning
        machine-learning -> machine learning
        JS               -> javascript
        postgres         -> postgresql
        k8s              -> kubernetes
        LLM              -> large language models
        """

        return SkillNormalizer.normalize_many(
            job.skills
        )

    @staticmethod
    def _location_key(
        job: DomainJob,
    ) -> LocationKey:
        """
        Create a hashable representation of a location
        for fast in-memory lookup.
        """

        return (
            job.location.city,
            job.location.state,
            job.location.country,
            job.location.remote,
        )