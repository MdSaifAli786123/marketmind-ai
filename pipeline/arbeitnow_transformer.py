from __future__ import annotations

from datetime import datetime, timezone

from bs4 import BeautifulSoup

from domain.company import Company
from domain.enums import ExperienceLevel, JobType
from domain.job import Job
from domain.location import Location
from domain.raw_job import RawJob
from pipeline.enrichment.location_normalizer import LocationNormalizer
from pipeline.transformer import BaseTransformer


class ArbeitnowTransformer(BaseTransformer):
    """
    Transform an Arbeitnow RawJob into the common Job domain model.

    Location data is normalized before creating the domain Job,
    so newly collected records are stored using structured:

        city
        state
        country
        remote

    fields instead of storing the complete raw location string
    inside the country field.
    """

    def transform(self, raw_job: RawJob) -> Job:
        data = raw_job.payload

        # --------------------------------------------------
        # Title
        # --------------------------------------------------
        title = (
            data.get("title")
            or "Unknown"
        ).strip()

        # --------------------------------------------------
        # Company
        # --------------------------------------------------
        company_name = (
            data.get("company_name")
            or "Unknown"
        ).strip()

        company = Company(
            name=company_name or "Unknown",
            website=None,
        )

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
        # Location
        # --------------------------------------------------
        location_text = (
            data.get("location")
            or ""
        ).strip()

        remote = bool(
            data.get("remote", False)
        )

        normalized_location = (
            LocationNormalizer().normalize(
                raw_location=location_text,
                remote=remote,
            )
        )

        location = Location(
            city=normalized_location.city,
            state=normalized_location.state,
            country=normalized_location.country,
            remote=normalized_location.remote,
        )

        # --------------------------------------------------
        # Skills / Tags
        # --------------------------------------------------
        raw_tags = (
            data.get("tags")
            or []
        )

        if not isinstance(
            raw_tags,
            list,
        ):
            raw_tags = []

        skills: list[str] = []
        seen: set[str] = set()

        for raw_tag in raw_tags:
            skill = str(
                raw_tag
            ).strip()

            if not skill:
                continue

            normalized = (
                skill.lower()
            )

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            skills.append(
                skill
            )

        # --------------------------------------------------
        # Posted Date
        # --------------------------------------------------
        posted_at = None

        created_at = data.get(
            "created_at"
        )

        if created_at is not None:
            try:
                # Arbeitnow commonly exposes created_at
                # as a Unix timestamp.
                posted_at = datetime.fromtimestamp(
                    float(created_at),
                    tz=timezone.utc,
                ).replace(
                    tzinfo=None
                )

            except (
                TypeError,
                ValueError,
                OSError,
                OverflowError,
            ):
                posted_at = None

        # --------------------------------------------------
        # Job Type
        # --------------------------------------------------
        # Remote status describes work location and should
        # not be interpreted as employment type.
        #
        # Employment type is inferred later by enrichment.
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
                "Arbeitnow job is missing "
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
            salary=None,
            job_type=job_type,
            experience_level=experience_level,
            skills=skills,
        )