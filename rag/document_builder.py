from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job


# ==========================================================
# RAG Document
# ==========================================================

@dataclass
class JobDocument:
    """
    Internal representation of a job posting prepared for
    embedding and semantic retrieval.

    text:
        Human-readable content that will later be embedded.

    metadata:
        Structured information preserved alongside the vector.
    """

    text: str
    metadata: dict[str, Any]


# ==========================================================
# Utility Functions
# ==========================================================

def _clean_text(value: str | None) -> str:
    """
    Normalize whitespace in text fields.
    """

    if not value:
        return ""

    return " ".join(
        value.split()
    )


def _format_location(job: Job) -> str:
    """
    Convert the related Location object into readable text.
    """

    location = job.location

    if location is None:
        return "Unknown"

    parts = [
        location.city,
        location.state,
        location.country,
    ]

    cleaned_parts = [
        _clean_text(part)
        for part in parts
        if part
    ]

    if not cleaned_parts:
        location_text = "Unknown"
    else:
        location_text = ", ".join(
            cleaned_parts
        )

    if location.remote:
        location_text += " (Remote)"

    return location_text


def _get_skill_names(
    job: Job,
) -> list[str]:
    """
    Extract normalized skill names from a job.
    """

    skill_names = [
        _clean_text(skill.name)
        for skill in job.skills
        if skill.name
    ]

    return sorted(
        set(skill_names),
        key=str.lower,
    )


# ==========================================================
# Build One Document
# ==========================================================

def build_job_document(
    job: Job,
) -> JobDocument:
    """
    Convert one SQLAlchemy Job object into a RAG document.
    """

    company_name = (
        _clean_text(job.company.name)
        if job.company
        else "Unknown"
    )

    location_text = _format_location(
        job
    )

    skill_names = _get_skill_names(
        job
    )

    skills_text = (
        ", ".join(skill_names)
        if skill_names
        else "Not specified"
    )

    posted_at = (
        job.posted_at.isoformat()
        if job.posted_at
        else "Unknown"
    )

    salary = (
        _clean_text(job.salary)
        if job.salary
        else "Not specified"
    )

    job_family = (
        _clean_text(job.job_family)
        if job.job_family
        else "Not specified"
    )

    description = _clean_text(
        job.description
    )

    # ------------------------------------------------------
    # Embedding Content
    # ------------------------------------------------------

    text = "\n".join(
        [
            f"Job Title: {_clean_text(job.title)}",
            f"Company: {company_name}",
            f"Location: {location_text}",
            f"Job Family: {job_family}",
            (
                "Experience Level: "
                f"{_clean_text(job.experience_level)}"
            ),
            (
                "Employment Type: "
                f"{_clean_text(job.job_type)}"
            ),
            f"Salary: {salary}",
            f"Skills: {skills_text}",
            f"Posted At: {posted_at}",
            f"Source: {_clean_text(job.source)}",
            "",
            "Job Description:",
            description,
        ]
    )

    # ------------------------------------------------------
    # Metadata
    # ------------------------------------------------------

    metadata: dict[str, Any] = {
        "job_id": job.id,
        "title": _clean_text(
            job.title
        ),
        "company": company_name,
        "company_id": job.company_id,
        "location_id": job.location_id,
        "city": (
            _clean_text(job.location.city)
            if job.location
            and job.location.city
            else None
        ),
        "state": (
            _clean_text(job.location.state)
            if job.location
            and job.location.state
            else None
        ),
        "country": (
            _clean_text(job.location.country)
            if job.location
            and job.location.country
            else None
        ),
        "remote": (
            job.location.remote
            if job.location
            else False
        ),
        "job_family": job.job_family,
        "experience_level": (
            job.experience_level
        ),
        "job_type": job.job_type,
        "salary": job.salary,
        "skills": skill_names,
        "source": job.source,
        "source_url": job.source_url,
        "posted_at": (
            job.posted_at.isoformat()
            if job.posted_at
            else None
        ),
        "enrichment_version": (
            job.enrichment_version
        ),
    }

    return JobDocument(
        text=text,
        metadata=metadata,
    )


# ==========================================================
# Load Jobs From Database
# ==========================================================

def build_job_documents(
    limit: int | None = None,
) -> list[JobDocument]:
    """
    Load enriched jobs from the database and convert them into
    RAG-ready documents.

    limit can be used during development to avoid processing
    the complete dataset.
    """

    with SessionLocal() as session:

        statement = (
            select(Job)
            .options(
                selectinload(
                    Job.company
                ),
                selectinload(
                    Job.location
                ),
                selectinload(
                    Job.skills
                ),
            )
            .order_by(
                Job.id.asc()
            )
        )

        if limit is not None:
            statement = statement.limit(
                limit
            )

        jobs = list(
            session.scalars(
                statement
            ).unique().all()
        )

        documents = [
            build_job_document(job)
            for job in jobs
        ]

        return documents


# ==========================================================
# Development Test
# ==========================================================

if __name__ == "__main__":

    documents = build_job_documents(
        limit=3
    )

    print(
        f"\nBuilt {len(documents)} documents.\n"
    )

    for index, document in enumerate(
        documents,
        start=1,
    ):

        print(
            "=" * 70
        )

        print(
            f"DOCUMENT {index}"
        )

        print(
            "=" * 70
        )

        print(
            document.text
        )

        print(
            "\nMETADATA:"
        )

        print(
            document.metadata
        )

        print()