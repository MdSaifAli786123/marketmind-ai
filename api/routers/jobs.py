from __future__ import annotations

import math

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from sqlalchemy import (
    func,
    or_,
    select,
)

from sqlalchemy.orm import (
    selectinload,
)

from api.schemas import (
    JobResponse,
    PaginatedJobsResponse,
)

from database.connection import SessionLocal

from database.models import (
    Company,
    Job,
    Location,
    Skill,
)


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


# ==========================================================
# GET /jobs
# ==========================================================

@router.get(
    "",
    response_model=PaginatedJobsResponse,
    summary="List and filter jobs",
)
def get_jobs(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    search: str | None = Query(
        default=None,
        description=(
            "Search job title and description."
        ),
    ),
    company: str | None = Query(
        default=None,
        description="Filter by company name.",
    ),
    country: str | None = Query(
        default=None,
        description="Filter by country.",
    ),
    city: str | None = Query(
        default=None,
        description="Filter by city.",
    ),
    remote: bool | None = Query(
        default=None,
        description="Filter remote/non-remote jobs.",
    ),
    job_family: str | None = Query(
        default=None,
        description="Filter by job family.",
    ),
    experience_level: str | None = Query(
        default=None,
        description="Filter by experience level.",
    ),
    job_type: str | None = Query(
        default=None,
        description="Filter by employment type.",
    ),
    skill: str | None = Query(
        default=None,
        description="Filter by skill.",
    ),
    source: str | None = Query(
        default=None,
        description="Filter by source.",
    ),
) -> PaginatedJobsResponse:

    with SessionLocal() as session:

        # --------------------------------------------------
        # Base query
        # --------------------------------------------------

        statement = select(Job)

        # --------------------------------------------------
        # Search
        # --------------------------------------------------

        if search:

            search_value = (
                f"%{search.strip()}%"
            )

            statement = statement.where(
                or_(
                    Job.title.ilike(
                        search_value
                    ),
                    Job.description.ilike(
                        search_value
                    ),
                )
            )

        # --------------------------------------------------
        # Job attributes
        # --------------------------------------------------

        if job_family:

            statement = statement.where(
                Job.job_family
                == job_family
            )

        if experience_level:

            statement = statement.where(
                Job.experience_level
                == experience_level
            )

        if job_type:

            statement = statement.where(
                Job.job_type
                == job_type
            )

        if source:

            statement = statement.where(
                Job.source
                == source
            )

        # --------------------------------------------------
        # Company filter
        # --------------------------------------------------

        if company:

            company_value = (
                f"%{company.strip()}%"
            )

            statement = (
                statement
                .join(Job.company)
                .where(
                    Company.name.ilike(
                        company_value
                    )
                )
            )

        # --------------------------------------------------
        # Location filters
        # --------------------------------------------------

        if (
            country
            or city
            or remote is not None
        ):

            statement = (
                statement
                .join(Job.location)
            )

            if country:

                statement = (
                    statement.where(
                        Location.country.ilike(
                            country.strip()
                        )
                    )
                )

            if city:

                statement = (
                    statement.where(
                        Location.city.ilike(
                            city.strip()
                        )
                    )
                )

            if remote is not None:

                statement = (
                    statement.where(
                        Location.remote
                        == remote
                    )
                )

        # --------------------------------------------------
        # Skill filter
        # --------------------------------------------------

        if skill:

            statement = (
                statement
                .join(Job.skills)
                .where(
                    Skill.name.ilike(
                        skill.strip()
                    )
                )
            )

        # --------------------------------------------------
        # Count BEFORE pagination
        # --------------------------------------------------

        count_statement = (
            select(
                func.count()
            )
            .select_from(
                statement
                .order_by(None)
                .subquery()
            )
        )

        total = (
            session.scalar(
                count_statement
            )
            or 0
        )

        # --------------------------------------------------
        # Pagination
        # --------------------------------------------------

        offset = (
            page - 1
        ) * page_size

        statement = (
            statement
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
                Job.posted_at.desc().nullslast(),
                Job.id.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        jobs = list(
            session.scalars(
                statement
            ).unique().all()
        )

        total_pages = (
            math.ceil(
                total / page_size
            )
            if total
            else 0
        )

        return PaginatedJobsResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            jobs=jobs,
        )


# ==========================================================
# GET /jobs/{job_id}
# ==========================================================

@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job details",
)
def get_job(
    job_id: int,
) -> JobResponse:

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
            .where(
                Job.id == job_id
            )
        )

        job = session.scalar(
            statement
        )

        if job is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Job {job_id} "
                    f"was not found."
                ),
            )

        # Convert while SQLAlchemy session is alive.
        return JobResponse.model_validate(
            job
        )