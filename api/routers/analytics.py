from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from database.connection import SessionLocal
from database.models import (
    Company,
    Job,
    Location,
    Skill,
    job_skills,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


# ==========================================================
# Helpers
# ==========================================================

def _distribution(
    session,
    column,
) -> list[dict]:

    statement = (
        select(
            column.label("name"),
            func.count(Job.id).label("count"),
        )
        .group_by(column)
        .order_by(
            func.count(Job.id).desc()
        )
    )

    rows = session.execute(
        statement
    ).all()

    return [
        {
            "name": (
                name
                if name is not None
                else "Unknown"
            ),
            "count": count,
        }
        for name, count in rows
    ]


# ==========================================================
# GET /analytics
# ==========================================================

@router.get(
    "",
    summary="Analytics API information",
)
def analytics_root() -> dict:

    return {
        "message": (
            "AI Job Market Analytics API"
        ),
        "endpoints": [
            "/analytics/overview",
            "/analytics/job-families",
            "/analytics/experience",
            "/analytics/job-types",
            "/analytics/sources",
            "/analytics/remote",
            "/analytics/skills",
            "/analytics/countries",
            "/analytics/companies",
        ],
    }


# ==========================================================
# GET /analytics/overview
# ==========================================================

@router.get(
    "/overview",
    summary="Get market overview",
)
def get_overview() -> dict:

    with SessionLocal() as session:

        total_jobs = (
            session.scalar(
                select(
                    func.count(Job.id)
                )
            )
            or 0
        )

        total_companies = (
            session.scalar(
                select(
                    func.count(Company.id)
                )
            )
            or 0
        )

        total_locations = (
            session.scalar(
                select(
                    func.count(Location.id)
                )
            )
            or 0
        )

        total_skills = (
            session.scalar(
                select(
                    func.count(Skill.id)
                )
            )
            or 0
        )

        remote_jobs = (
            session.scalar(
                select(
                    func.count(Job.id)
                )
                .join(Job.location)
                .where(
                    Location.remote.is_(True)
                )
            )
            or 0
        )

        remote_percentage = (
            round(
                remote_jobs
                / total_jobs
                * 100,
                2,
            )
            if total_jobs
            else 0.0
        )

        return {
            "total_jobs": total_jobs,
            "total_companies": total_companies,
            "total_locations": total_locations,
            "unique_skills": total_skills,
            "remote_jobs": remote_jobs,
            "remote_percentage":
                remote_percentage,
        }


# ==========================================================
# GET /analytics/job-families
# ==========================================================

@router.get(
    "/job-families",
    summary="Job-family distribution",
)
def get_job_families() -> dict:

    with SessionLocal() as session:

        data = _distribution(
            session,
            Job.job_family,
        )

        return {
            "data": data,
        }


# ==========================================================
# GET /analytics/experience
# ==========================================================

@router.get(
    "/experience",
    summary="Experience-level distribution",
)
def get_experience_distribution() -> dict:

    with SessionLocal() as session:

        data = _distribution(
            session,
            Job.experience_level,
        )

        return {
            "data": data,
        }


# ==========================================================
# GET /analytics/job-types
# ==========================================================

@router.get(
    "/job-types",
    summary="Employment-type distribution",
)
def get_job_type_distribution() -> dict:

    with SessionLocal() as session:

        data = _distribution(
            session,
            Job.job_type,
        )

        return {
            "data": data,
        }


# ==========================================================
# GET /analytics/sources
# ==========================================================

@router.get(
    "/sources",
    summary="Job-source distribution",
)
def get_source_distribution() -> dict:

    with SessionLocal() as session:

        data = _distribution(
            session,
            Job.source,
        )

        return {
            "data": data,
        }


# ==========================================================
# GET /analytics/remote
# ==========================================================

@router.get(
    "/remote",
    summary="Remote-work distribution",
)
def get_remote_distribution() -> dict:

    with SessionLocal() as session:

        remote_jobs = (
            session.scalar(
                select(
                    func.count(Job.id)
                )
                .join(Job.location)
                .where(
                    Location.remote.is_(True)
                )
            )
            or 0
        )

        non_remote_jobs = (
            session.scalar(
                select(
                    func.count(Job.id)
                )
                .join(Job.location)
                .where(
                    Location.remote.is_(False)
                )
            )
            or 0
        )

        total = (
            remote_jobs
            + non_remote_jobs
        )

        return {
            "remote": remote_jobs,
            "non_remote":
                non_remote_jobs,
            "total": total,
            "remote_percentage": (
                round(
                    remote_jobs
                    / total
                    * 100,
                    2,
                )
                if total
                else 0.0
            ),
        }


# ==========================================================
# GET /analytics/skills
# ==========================================================

@router.get(
    "/skills",
    summary="Top skills by job demand",
)
def get_top_skills(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
) -> dict:

    with SessionLocal() as session:

        statement = (
            select(
                Skill.name,
                func.count(
                    job_skills.c.job_id
                ).label("job_count"),
            )
            .join(
                job_skills,
                Skill.id
                == job_skills.c.skill_id,
            )
            .group_by(
                Skill.id,
                Skill.name,
            )
            .order_by(
                func.count(
                    job_skills.c.job_id
                ).desc(),
                Skill.name.asc(),
            )
            .limit(limit)
        )

        rows = session.execute(
            statement
        ).all()

        total_jobs = (
            session.scalar(
                select(
                    func.count(Job.id)
                )
            )
            or 0
        )

        data = []

        for (
            skill_name,
            job_count,
        ) in rows:

            percentage = (
                round(
                    job_count
                    / total_jobs
                    * 100,
                    2,
                )
                if total_jobs
                else 0.0
            )

            data.append(
                {
                    "skill":
                        skill_name,
                    "jobs":
                        job_count,
                    "percentage":
                        percentage,
                }
            )

        return {
            "total_jobs":
                total_jobs,
            "data": data,
        }


# ==========================================================
# GET /analytics/countries
# ==========================================================

@router.get(
    "/countries",
    summary="Top countries by job count",
)
def get_top_countries(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
) -> dict:

    with SessionLocal() as session:

        statement = (
            select(
                Location.country,
                func.count(
                    Job.id
                ).label("job_count"),
            )
            .join(
                Job,
                Job.location_id
                == Location.id,
            )
            .where(
                Location.country.is_not(
                    None
                )
            )
            .group_by(
                Location.country
            )
            .order_by(
                func.count(
                    Job.id
                ).desc()
            )
            .limit(limit)
        )

        rows = session.execute(
            statement
        ).all()

        return {
            "data": [
                {
                    "country": country,
                    "jobs": count,
                }
                for (
                    country,
                    count,
                ) in rows
            ]
        }


# ==========================================================
# GET /analytics/companies
# ==========================================================

@router.get(
    "/companies",
    summary="Top hiring companies",
)
def get_top_companies(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
) -> dict:

    with SessionLocal() as session:

        statement = (
            select(
                Company.name,
                func.count(
                    Job.id
                ).label("job_count"),
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
                func.count(
                    Job.id
                ).desc(),
                Company.name.asc(),
            )
            .limit(limit)
        )

        rows = session.execute(
            statement
        ).all()

        return {
            "data": [
                {
                    "company": company,
                    "jobs": count,
                }
                for (
                    company,
                    count,
                ) in rows
            ]
        }