from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job, Skill
from pipeline.enrichment.skill_extractor import SkillExtractor
from utils.logger import logger


class JobSkillRebuilder:
    """
    Rebuild job-skill relationships from existing job data.

    Sources:
    - Job title
    - Job description
    - Existing valid skills

    The script:
    - does NOT delete jobs
    - does NOT modify job family
    - does NOT modify company/location
    - does NOT modify descriptions
    - rebuilds only job <-> skill relationships
    """

    def __init__(self) -> None:
        self.extractor = SkillExtractor()

    def run(self) -> tuple[int, int, int]:

        jobs_processed = 0
        relationships_created = 0
        failed_jobs = 0

        with SessionLocal() as session:

            try:

                # ==============================================
                # 1. Load existing Skill records
                # ==============================================

                existing_skills = list(
                    session.scalars(
                        select(Skill)
                    ).all()
                )

                skill_by_name: dict[str, Skill] = {
                    skill.name: skill
                    for skill in existing_skills
                }

                logger.info(
                    f"Existing canonical skills: "
                    f"{len(existing_skills)}"
                )

                # ==============================================
                # 2. Load all jobs and current skills
                # ==============================================

                jobs = list(
                    session.scalars(
                        select(Job)
                        .options(
                            selectinload(Job.skills)
                        )
                        .order_by(Job.id)
                    ).all()
                )

                logger.info(
                    f"Jobs to rebuild: {len(jobs)}"
                )

                # ==============================================
                # 3. Process jobs
                # ==============================================

                for job in jobs:

                    try:

                        current_skill_names = [
                            skill.name
                            for skill in job.skills
                        ]

                        extracted_names = (
                            self.extractor.extract(
                                title=job.title,
                                description=job.description,
                                source_skills=current_skill_names,
                            )
                        )

                        rebuilt_skills: list[Skill] = []

                        for skill_name in extracted_names:

                            skill = skill_by_name.get(
                                skill_name
                            )

                            # ----------------------------------
                            # Create canonical skill if needed
                            # ----------------------------------

                            if skill is None:

                                skill = Skill(
                                    name=skill_name
                                )

                                session.add(skill)

                                # Assign primary key immediately.
                                session.flush()

                                skill_by_name[
                                    skill_name
                                ] = skill

                            rebuilt_skills.append(
                                skill
                            )

                        # --------------------------------------
                        # Replace current relationships
                        # --------------------------------------

                        job.skills = rebuilt_skills

                        relationships_created += len(
                            rebuilt_skills
                        )

                        jobs_processed += 1

                        if jobs_processed % 50 == 0:

                            logger.info(
                                f"Processed "
                                f"{jobs_processed}/"
                                f"{len(jobs)} jobs"
                            )

                    except Exception:

                        failed_jobs += 1

                        logger.exception(
                            "Failed rebuilding skills "
                            f"for job id={job.id}"
                        )

                # ==============================================
                # 4. Persist all changes
                # ==============================================

                session.commit()

            except Exception:

                session.rollback()

                logger.exception(
                    "Job skill rebuild failed."
                )

                raise

        logger.info(
            "Job skill rebuild complete: "
            f"jobs_processed={jobs_processed}, "
            f"relationships={relationships_created}, "
            f"failed_jobs={failed_jobs}, "
            f"extractor={self.extractor.VERSION}"
        )

        return (
            jobs_processed,
            relationships_created,
            failed_jobs,
        )


def main() -> None:

    logger.info(
        "Starting job skill reconstruction..."
    )

    rebuilder = JobSkillRebuilder()

    processed, relationships, failed = (
        rebuilder.run()
    )

    logger.info(
        "Job skill reconstruction finished: "
        f"processed={processed}, "
        f"relationships={relationships}, "
        f"failed={failed}"
    )


if __name__ == "__main__":
    main()