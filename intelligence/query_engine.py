from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job, Location, Skill
from intelligence.query_planner import QueryPlan


class QueryEngine:
    """
    Executes validated QueryPlan objects against the job database.

    The engine never executes LLM-generated SQL.
    Every supported intent maps to predefined SQLAlchemy logic.
    """

    VERSION = "query-engine-v1"

    SUPPORTED_INTENTS = {
        "top_skills",
        "find_jobs",
        "skill_comparison",
        "skill_relationships",
        "market_overview",
    }

    # ======================================================
    # Public API
    # ======================================================

    def execute(
        self,
        plan: QueryPlan,
    ) -> dict[str, Any]:

        if plan.intent not in self.SUPPORTED_INTENTS:
            raise ValueError(
                f"Unsupported intent: {plan.intent}"
            )

        if plan.intent == "top_skills":
            return self._top_skills(plan)

        if plan.intent == "find_jobs":
            return self._find_jobs(plan)

        if plan.intent == "skill_comparison":
            return self._skill_comparison(plan)

        if plan.intent == "skill_relationships":
            return self._skill_relationships(plan)

        if plan.intent == "market_overview":
            return self._market_overview(plan)

        raise ValueError(
            f"No executor exists for intent: {plan.intent}"
        )

    # ======================================================
    # Base Filter Query
    # ======================================================

    def _filtered_job_ids(
        self,
        plan: QueryPlan,
    ):

        statement = select(Job.id)

        filters = plan.filters

        # --------------------------------------------------
        # Job Family
        # --------------------------------------------------

        job_family = filters.get(
            "job_family"
        )

        if job_family:

            statement = statement.where(
                Job.job_family == job_family
            )

        # --------------------------------------------------
        # Experience
        # --------------------------------------------------

        experience = filters.get(
            "experience_level"
        )

        if experience:

            statement = statement.where(
                Job.experience_level
                == experience
            )

        # --------------------------------------------------
        # Job Type
        # --------------------------------------------------

        job_type = filters.get(
            "job_type"
        )

        if job_type:

            statement = statement.where(
                Job.job_type == job_type
            )

        # --------------------------------------------------
        # Location
        # --------------------------------------------------

        country = filters.get(
            "country"
        )

        remote = filters.get(
            "remote"
        )

        if (
            country is not None
            or remote is not None
        ):

            statement = statement.join(
                Job.location
            )

            if country:

                statement = statement.where(
                    Location.country
                    == country
                )

            if remote is not None:

                statement = statement.where(
                    Location.remote
                    == remote
                )

        # --------------------------------------------------
        # Skill
        # --------------------------------------------------

        skill = filters.get(
            "skill"
        )

        if skill:

            statement = statement.join(
                Job.skills
            )

            statement = statement.where(
                func.lower(Skill.name)
                == skill.lower()
            )

        return statement.distinct()

    # ======================================================
    # Top Skills
    # ======================================================

    def _top_skills(
        self,
        plan: QueryPlan,
    ) -> dict[str, Any]:

        job_ids = (
            self._filtered_job_ids(plan)
            .subquery()
        )

        with SessionLocal() as session:

            total_jobs = (
                session.scalar(
                    select(
                        func.count()
                    ).select_from(job_ids)
                )
                or 0
            )

            statement = (
                select(
                    Skill.name,
                    func.count(
                        func.distinct(Job.id)
                    ).label("job_count"),
                )
                .select_from(Job)
                .join(Job.skills)
                .where(
                    Job.id.in_(
                        select(job_ids.c.id)
                    )
                )
                .group_by(Skill.id, Skill.name)
                .order_by(
                    func.count(
                        func.distinct(Job.id)
                    ).desc(),
                    Skill.name.asc(),
                )
                .limit(plan.limit)
            )

            rows = session.execute(
                statement
            ).all()

        data = []

        for name, count in rows:

            percentage = (
                round(
                    (count / total_jobs) * 100,
                    2,
                )
                if total_jobs
                else 0.0
            )

            data.append(
                {
                    "skill": name,
                    "job_count": count,
                    "percentage": percentage,
                }
            )

        return {
            "intent": plan.intent,
            "total_matching_jobs": total_jobs,
            "data": data,
            "filters": plan.filters,
        }

    # ======================================================
    # Find Jobs
    # ======================================================

    def _find_jobs(
        self,
        plan: QueryPlan,
    ) -> dict[str, Any]:

        job_ids = (
            self._filtered_job_ids(plan)
            .subquery()
        )

        with SessionLocal() as session:

            total_jobs = (
                session.scalar(
                    select(
                        func.count()
                    ).select_from(job_ids)
                )
                or 0
            )

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
                    Job.id.in_(
                        select(job_ids.c.id)
                    )
                )
                .order_by(
                    Job.posted_at
                    .desc()
                    .nullslast(),
                    Job.id.desc(),
                )
                .limit(plan.limit)
            )

            jobs = list(
                session.scalars(
                    statement
                ).unique().all()
            )

            data = [
                self._serialize_job(job)
                for job in jobs
            ]

        return {
            "intent": plan.intent,
            "total_matching_jobs": total_jobs,
            "returned_jobs": len(data),
            "data": data,
            "filters": plan.filters,
        }

    # ======================================================
    # Skill Comparison
    # ======================================================

    def _skill_comparison(
        self,
        plan: QueryPlan,
    ) -> dict[str, Any]:

        if len(plan.skills) < 2:

            return {
                "intent": plan.intent,
                "total_matching_jobs": 0,
                "data": [],
                "filters": plan.filters,
                "message": (
                    "At least two recognized skills "
                    "are required for comparison."
                ),
            }

        job_ids = (
            self._filtered_job_ids(plan)
            .subquery()
        )

        normalized_skills = [
            skill.lower()
            for skill in plan.skills
        ]

        with SessionLocal() as session:

            total_jobs = (
                session.scalar(
                    select(
                        func.count()
                    ).select_from(job_ids)
                )
                or 0
            )

            statement = (
                select(
                    Skill.name,
                    func.count(
                        func.distinct(Job.id)
                    ).label("job_count"),
                )
                .select_from(Job)
                .join(Job.skills)
                .where(
                    Job.id.in_(
                        select(job_ids.c.id)
                    )
                )
                .where(
                    func.lower(
                        Skill.name
                    ).in_(
                        normalized_skills
                    )
                )
                .group_by(
                    Skill.id,
                    Skill.name,
                )
                .order_by(
                    func.count(
                        func.distinct(Job.id)
                    ).desc()
                )
            )

            rows = session.execute(
                statement
            ).all()

        counts = {
            skill.lower(): 0
            for skill in plan.skills
        }

        display_names = {
            skill.lower(): skill
            for skill in plan.skills
        }

        for name, count in rows:

            key = name.lower()

            counts[key] = count
            display_names[key] = name

        data = []

        for skill in plan.skills:

            key = skill.lower()

            count = counts.get(
                key,
                0,
            )

            percentage = (
                round(
                    count
                    / total_jobs
                    * 100,
                    2,
                )
                if total_jobs
                else 0.0
            )

            data.append(
                {
                    "skill": (
                        display_names.get(
                            key,
                            skill,
                        )
                    ),
                    "job_count": count,
                    "percentage": percentage,
                }
            )

        data.sort(
            key=lambda item:
                item["job_count"],
            reverse=True,
        )

        return {
            "intent": plan.intent,
            "total_matching_jobs": total_jobs,
            "data": data,
            "filters": plan.filters,
        }

    # ======================================================
    # Skill Relationships
    # ======================================================

    def _skill_relationships(
        self,
        plan: QueryPlan,
    ) -> dict[str, Any]:

        if not plan.skills:

            return {
                "intent": plan.intent,
                "total_matching_jobs": 0,
                "data": [],
                "filters": plan.filters,
                "message": (
                    "A recognized skill is required "
                    "for relationship analysis."
                ),
            }

        target_skill = plan.skills[0]

        job_ids = (
            self._filtered_job_ids(plan)
            .subquery()
        )

        with SessionLocal() as session:

            target_job_statement = (
                select(Job)
                .options(
                    selectinload(
                        Job.skills
                    )
                )
                .join(Job.skills)
                .where(
                    Job.id.in_(
                        select(job_ids.c.id)
                    )
                )
                .where(
                    func.lower(Skill.name)
                    == target_skill.lower()
                )
            )

            jobs = list(
                session.scalars(
                    target_job_statement
                ).unique().all()
            )

            counter: Counter[str] = Counter()

            for job in jobs:

                for skill in job.skills:

                    if (
                        skill.name.lower()
                        == target_skill.lower()
                    ):
                        continue

                    counter[
                        skill.name
                    ] += 1

        total_target_jobs = len(jobs)

        data = []

        for (
            skill_name,
            count,
        ) in counter.most_common(
            plan.limit
        ):

            percentage = (
                round(
                    count
                    / total_target_jobs
                    * 100,
                    2,
                )
                if total_target_jobs
                else 0.0
            )

            data.append(
                {
                    "skill": skill_name,
                    "co_occurrence_count": count,
                    "percentage": percentage,
                }
            )

        return {
            "intent": plan.intent,
            "target_skill": target_skill,
            "total_matching_jobs": (
                total_target_jobs
            ),
            "data": data,
            "filters": plan.filters,
        }

    # ======================================================
    # Market Overview
    # ======================================================

    def _market_overview(
        self,
        plan: QueryPlan,
    ) -> dict[str, Any]:

        job_ids = (
            self._filtered_job_ids(plan)
            .subquery()
        )

        with SessionLocal() as session:

            total_jobs = (
                session.scalar(
                    select(
                        func.count()
                    ).select_from(job_ids)
                )
                or 0
            )

            remote_jobs = (
                session.scalar(
                    select(
                        func.count(
                            func.distinct(
                                Job.id
                            )
                        )
                    )
                    .select_from(Job)
                    .join(Job.location)
                    .where(
                        Job.id.in_(
                            select(
                                job_ids.c.id
                            )
                        )
                    )
                    .where(
                        Location.remote
                        .is_(True)
                    )
                )
                or 0
            )

            company_count = (
                session.scalar(
                    select(
                        func.count(
                            func.distinct(
                                Job.company_id
                            )
                        )
                    )
                    .where(
                        Job.id.in_(
                            select(
                                job_ids.c.id
                            )
                        )
                    )
                )
                or 0
            )

            location_count = (
                session.scalar(
                    select(
                        func.count(
                            func.distinct(
                                Job.location_id
                            )
                        )
                    )
                    .where(
                        Job.id.in_(
                            select(
                                job_ids.c.id
                            )
                        )
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
            "intent": plan.intent,

            "data": {
                "total_jobs": total_jobs,
                "total_companies": company_count,
                "total_locations": location_count,
                "remote_jobs": remote_jobs,
                "remote_percentage": (
                    remote_percentage
                ),
            },

            "filters": plan.filters,
        }

    # ======================================================
    # Job Serialization
    # ======================================================

    @staticmethod
    def _serialize_job(
        job: Job,
    ) -> dict[str, Any]:

        return {
            "id": job.id,

            "title": job.title,

            "company": (
                job.company.name
                if job.company
                else None
            ),

            "location": {
                "city": (
                    job.location.city
                    if job.location
                    else None
                ),

                "state": (
                    job.location.state
                    if job.location
                    else None
                ),

                "country": (
                    job.location.country
                    if job.location
                    else None
                ),

                "remote": (
                    job.location.remote
                    if job.location
                    else False
                ),
            },

            "job_family": (
                job.job_family
            ),

            "experience_level": (
                job.experience_level
            ),

            "job_type": (
                job.job_type
            ),

            "skills": [
                skill.name
                for skill in job.skills
            ],

            "posted_at": (
                job.posted_at.isoformat()
                if job.posted_at
                else None
            ),

            "source": job.source,

            "source_url": (
                job.source_url
            ),
        }