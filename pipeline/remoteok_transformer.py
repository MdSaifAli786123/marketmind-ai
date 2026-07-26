from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from domain.company import Company
from domain.enums import ExperienceLevel, JobType
from domain.job import Job
from domain.location import Location
from domain.raw_job import RawJob
from pipeline.enrichment.location_normalizer import LocationNormalizer
from pipeline.transformer import BaseTransformer


class RemoteOKTransformer(BaseTransformer):
    """
    Transform a RemoteOK RawJob into the common Job domain model.

    RemoteOK jobs are treated as remote, while geographic
    information is normalized into city/state/country fields.
    """

    def transform(self, raw_job: RawJob) -> Job:
        data = raw_job.payload

        # --------------------------------------------------
        # Title
        # --------------------------------------------------
        title = (
            data.get("position")
            or "Unknown"
        ).strip()

        # --------------------------------------------------
        # Company
        # --------------------------------------------------
        company_name = (
            data.get("company")
            or "Unknown"
        ).strip()

        company = Company(
            name=company_name or "Unknown",
            website=None,
        )

        # --------------------------------------------------
        # Location
        # --------------------------------------------------
        location_text = (
            data.get("location")
            or ""
        ).strip()

        # RemoteOK is a remote-job source.
        # Therefore remote=True regardless of whether the
        # source also provides geographic information.
        normalized_location = (
            LocationNormalizer().normalize(
                raw_location=location_text,
                remote=True,
            )
        )

        location = Location(
            city=normalized_location.city,
            state=normalized_location.state,
            country=normalized_location.country,
            remote=normalized_location.remote,
        )

        # --------------------------------------------------
        # Posted Time
        # --------------------------------------------------
        posted_at = None

        epoch = data.get("epoch")

        if epoch is not None:
            try:
                posted_at = datetime.fromtimestamp(
                    float(epoch)
                )

            except (
                TypeError,
                ValueError,
                OSError,
                OverflowError,
            ):
                posted_at = None

        # --------------------------------------------------
        # Salary
        # --------------------------------------------------
        salary_min = data.get(
            "salary_min"
        )

        salary_max = data.get(
            "salary_max"
        )

        if salary_min == 0:
            salary_min = None

        if salary_max == 0:
            salary_max = None

        salary = None

        try:
            if (
                salary_min is not None
                and salary_max is not None
            ):
                salary = (
                    f"${salary_min:,} - "
                    f"${salary_max:,}"
                )

            elif salary_min is not None:
                salary = (
                    f"${salary_min:,}+"
                )

            elif salary_max is not None:
                salary = (
                    f"Up to ${salary_max:,}"
                )

        except (
            TypeError,
            ValueError,
        ):
            salary = None

        # --------------------------------------------------
        # Description
        # --------------------------------------------------
        raw_description = (
            data.get("description")
            or ""
        )

        description = BeautifulSoup(
            raw_description,
            "html.parser",
        ).get_text(
            " ",
            strip=True,
        )

        description = " ".join(
            description.split()
        )

        # --------------------------------------------------
        # Skills
        # --------------------------------------------------
        raw_skills = (
            data.get("tags")
            or []
        )

        if not isinstance(
            raw_skills,
            list,
        ):
            raw_skills = []

        skills: list[str] = []
        seen_skills: set[str] = set()

        for raw_skill in raw_skills:
            skill = str(
                raw_skill
            ).strip()

            if not skill:
                continue

            normalized = (
                skill.lower()
            )

            if normalized in seen_skills:
                continue

            seen_skills.add(
                normalized
            )

            skills.append(
                skill
            )

        # --------------------------------------------------
        # Job Type
        # --------------------------------------------------
        # Remote describes work location, not employment
        # type. Employment type is inferred later.
        job_type = JobType.UNKNOWN

        # --------------------------------------------------
        # Experience Level
        # --------------------------------------------------
        # Experience level is inferred later by enrichment.
        experience_level = (
            ExperienceLevel.UNKNOWN
        )

        # --------------------------------------------------
        # Source URL
        # --------------------------------------------------
        source_url = data.get(
            "url"
        )

        if not source_url:
            raise ValueError(
                "RemoteOK job is missing "
                "its source URL."
            )

        # --------------------------------------------------
        # Domain Job
        # --------------------------------------------------
        return Job(
            title=title,
            company=company,
            location=location,
            description=description,
            source=raw_job.source,
            source_url=source_url,
            posted_at=posted_at,
            salary=salary,
            job_type=job_type,
            experience_level=experience_level,
            skills=skills,
        )