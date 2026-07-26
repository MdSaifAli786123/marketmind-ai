from __future__ import annotations

from sqlalchemy import func, select

from database.connection import SessionLocal
from database.models import Job, Skill, job_skills


class SkillAnalytics:
    """
    Read-only analytics for skills associated with jobs.

    No database records are modified.
    """

    # ==========================================================
    # Total skills
    # ==========================================================

    def total_skills(self) -> int:

        with SessionLocal() as session:

            return (
                session.scalar(
                    select(
                        func.count(Skill.id)
                    )
                )
                or 0
            )

    # ==========================================================
    # Top skills globally
    # ==========================================================

    def top_skills(
        self,
        limit: int = 20,
    ) -> list[dict]:

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
                    Skill.name,
                )
                .limit(limit)
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "skill": skill,
                    "job_count": count,
                }
                for skill, count in rows
            ]

    # ==========================================================
    # Top skills for a particular job family
    # ==========================================================

    def top_skills_by_family(
        self,
        job_family: str,
        limit: int = 20,
    ) -> list[dict]:

        with SessionLocal() as session:

            statement = (
                select(
                    Skill.name,
                    func.count(
                        job_skills.c.job_id
                    ).label("job_count"),
                )
                .select_from(Job)
                .join(
                    job_skills,
                    Job.id
                    == job_skills.c.job_id,
                )
                .join(
                    Skill,
                    Skill.id
                    == job_skills.c.skill_id,
                )
                .where(
                    Job.job_family
                    == job_family
                )
                .group_by(
                    Skill.id,
                    Skill.name,
                )
                .order_by(
                    func.count(
                        job_skills.c.job_id
                    ).desc(),
                    Skill.name,
                )
                .limit(limit)
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "skill": skill,
                    "job_count": count,
                }
                for skill, count in rows
            ]

    # ==========================================================
    # Skill demand percentage
    # ==========================================================

    def skill_demand(
        self,
        skill_name: str,
    ) -> dict:

        with SessionLocal() as session:

            total_jobs = (
                session.scalar(
                    select(
                        func.count(Job.id)
                    )
                )
                or 0
            )

            jobs_with_skill = (
                session.scalar(
                    select(
                        func.count(
                            func.distinct(
                                job_skills.c.job_id
                            )
                        )
                    )
                    .select_from(job_skills)
                    .join(
                        Skill,
                        Skill.id
                        == job_skills.c.skill_id,
                    )
                    .where(
                        func.lower(Skill.name)
                        == skill_name.lower()
                    )
                )
                or 0
            )

            percentage = (
                jobs_with_skill
                / total_jobs
                * 100
                if total_jobs
                else 0.0
            )

            return {
                "skill": skill_name,
                "jobs": jobs_with_skill,
                "total_jobs": total_jobs,
                "percentage": round(
                    percentage,
                    2,
                ),
            }

    # ==========================================================
    # Skills occurring together with another skill
    # ==========================================================

    def related_skills(
        self,
        skill_name: str,
        limit: int = 15,
    ) -> list[dict]:

        with SessionLocal() as session:

            target_jobs = (
                select(
                    job_skills.c.job_id
                )
                .join(
                    Skill,
                    Skill.id
                    == job_skills.c.skill_id,
                )
                .where(
                    func.lower(Skill.name)
                    == skill_name.lower()
                )
            )

            statement = (
                select(
                    Skill.name,
                    func.count(
                        func.distinct(
                            job_skills.c.job_id
                        )
                    ).label(
                        "co_occurrence"
                    ),
                )
                .select_from(job_skills)
                .join(
                    Skill,
                    Skill.id
                    == job_skills.c.skill_id,
                )
                .where(
                    job_skills.c.job_id.in_(
                        target_jobs
                    )
                )
                .where(
                    func.lower(Skill.name)
                    != skill_name.lower()
                )
                .group_by(
                    Skill.id,
                    Skill.name,
                )
                .order_by(
                    func.count(
                        func.distinct(
                            job_skills.c.job_id
                        )
                    ).desc(),
                    Skill.name,
                )
                .limit(limit)
            )

            rows = session.execute(
                statement
            ).all()

            return [
                {
                    "skill": skill,
                    "co_occurrence": count,
                }
                for skill, count in rows
            ]

    # ==========================================================
    # Number of jobs containing skills
    # ==========================================================

    def skill_coverage(self) -> dict:

        with SessionLocal() as session:

            total_jobs = (
                session.scalar(
                    select(
                        func.count(Job.id)
                    )
                )
                or 0
            )

            jobs_with_skills = (
                session.scalar(
                    select(
                        func.count(
                            func.distinct(
                                job_skills.c.job_id
                            )
                        )
                    )
                    .select_from(
                        job_skills
                    )
                )
                or 0
            )

            jobs_without_skills = (
                total_jobs
                - jobs_with_skills
            )

            percentage = (
                jobs_with_skills
                / total_jobs
                * 100
                if total_jobs
                else 0.0
            )

            return {
                "total_jobs": total_jobs,
                "jobs_with_skills":
                    jobs_with_skills,
                "jobs_without_skills":
                    jobs_without_skills,
                "coverage_percentage":
                    round(percentage, 2),
            }


# ==============================================================
# Manual test
# ==============================================================

def main() -> None:

    analytics = SkillAnalytics()

    print()
    print("=" * 75)
    print("SKILL MARKET ANALYTICS")
    print("=" * 75)

    print()
    print(
        f"Unique normalized skills: "
        f"{analytics.total_skills()}"
    )

    print()
    print("SKILL COVERAGE")
    print("-" * 75)

    for key, value in (
        analytics.skill_coverage().items()
    ):
        print(
            f"{key:30}: {value}"
        )

    print()
    print("TOP SKILLS")
    print("-" * 75)

    for row in analytics.top_skills():

        print(
            f"{row['skill']:40}"
            f"{row['job_count']:>6}"
        )

    print()
    print("SOFTWARE ENGINEERING SKILLS")
    print("-" * 75)

    rows = analytics.top_skills_by_family(
        "Software Engineering",
        limit=15,
    )

    for row in rows:

        print(
            f"{row['skill']:40}"
            f"{row['job_count']:>6}"
        )

    print()
    print("DEVOPS & CLOUD SKILLS")
    print("-" * 75)

    rows = analytics.top_skills_by_family(
        "DevOps & Cloud",
        limit=15,
    )

    for row in rows:

        print(
            f"{row['skill']:40}"
            f"{row['job_count']:>6}"
        )

    print()
    print("PYTHON DEMAND")
    print("-" * 75)

    python_demand = (
        analytics.skill_demand(
            "python"
        )
    )

    for key, value in (
        python_demand.items()
    ):
        print(
            f"{key:30}: {value}"
        )

    print()
    print("SKILLS RELATED TO PYTHON")
    print("-" * 75)

    for row in (
        analytics.related_skills(
            "python"
        )
    ):

        print(
            f"{row['skill']:40}"
            f"{row['co_occurrence']:>6}"
        )

    print()
    print("=" * 75)


if __name__ == "__main__":
    main()