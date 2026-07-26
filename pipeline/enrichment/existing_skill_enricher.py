from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job, Skill
from pipeline.enrichment.skill_normalizer import SkillNormalizer
from utils.logger import logger


class ExistingSkillEnricher:
    """
    Clean and normalize skills already stored in PostgreSQL.

    Skill Taxonomy v2 responsibilities:

    1. Normalize valid aliases to canonical skills.
       Example:
           JS       -> javascript
           K8s      -> kubernetes
           postgres -> postgresql

    2. Remove invalid metadata/category tags from jobs.
       Example:
           remote
           digital nomad
           exec
           finance
           full time

    3. Merge duplicate canonical relationships.

    4. Delete obsolete or invalid Skill rows once they
       are no longer referenced.

    No Job, Company, Location, or other job data is deleted.
    """

    def run(self) -> tuple[int, int, int]:

        normalized_relationships = 0
        deleted_skills = 0
        failed_jobs = 0

        # Additional statistics for logging.
        invalid_relationships_removed = 0
        invalid_skill_rows = 0
        alias_skill_rows = 0

        with SessionLocal() as session:

            try:

                # ==================================================
                # 1. Load all existing Skill records
                # ==================================================

                skills = list(
                    session.scalars(
                        select(Skill)
                        .order_by(Skill.id)
                    ).all()
                )

                logger.info(
                    f"Existing skills found: {len(skills)}"
                )

                # --------------------------------------------------
                # Lookup existing skills by normalized DB name.
                # --------------------------------------------------

                skill_by_name: dict[str, Skill] = {
                    skill.name.strip().lower(): skill
                    for skill in skills
                }

                # ==================================================
                # 2. Classify every existing skill
                # ==================================================
                #
                # valid:
                #
                #     JS -> javascript
                #
                # invalid:
                #
                #     remote -> None
                #
                # ==================================================

                canonical_by_id: dict[
                    int,
                    str | None,
                ] = {}

                for skill in skills:

                    canonical_name = (
                        SkillNormalizer.normalize(
                            skill.name
                        )
                    )

                    is_valid = (
                        SkillNormalizer.is_valid_skill(
                            canonical_name
                        )
                    )

                    # ----------------------------------------------
                    # Invalid tag
                    # ----------------------------------------------

                    if not is_valid:

                        canonical_by_id[
                            skill.id
                        ] = None

                        invalid_skill_rows += 1

                        continue

                    # ----------------------------------------------
                    # Valid skill
                    # ----------------------------------------------

                    canonical_by_id[
                        skill.id
                    ] = canonical_name

                    if (
                        canonical_name
                        != skill.name.strip().lower()
                    ):
                        alias_skill_rows += 1

                    # ----------------------------------------------
                    # Ensure canonical Skill exists
                    # ----------------------------------------------

                    if (
                        canonical_name
                        not in skill_by_name
                    ):

                        canonical_skill = Skill(
                            name=canonical_name
                        )

                        session.add(
                            canonical_skill
                        )

                        skill_by_name[
                            canonical_name
                        ] = canonical_skill

                # Assign IDs to newly created canonical skills.
                session.flush()

                logger.info(
                    "Skill taxonomy analysis: "
                    f"valid_or_alias="
                    f"{len(skills) - invalid_skill_rows}, "
                    f"aliases={alias_skill_rows}, "
                    f"invalid={invalid_skill_rows}"
                )

                # ==================================================
                # 3. Load all jobs with their skill relationships
                # ==================================================

                statement = (
                    select(Job)
                    .options(
                        selectinload(
                            Job.skills
                        )
                    )
                    .order_by(Job.id)
                )

                jobs = list(
                    session.scalars(
                        statement
                    ).all()
                )

                logger.info(
                    f"Jobs loaded for skill cleanup: "
                    f"{len(jobs)}"
                )

                # ==================================================
                # 4. Rebuild each job's skills
                # ==================================================

                for job in jobs:

                    try:

                        cleaned_skills: list[
                            Skill
                        ] = []

                        seen_skill_ids: set[
                            int
                        ] = set()

                        for old_skill in job.skills:

                            canonical_name = (
                                canonical_by_id.get(
                                    old_skill.id
                                )
                            )

                            # ======================================
                            # Invalid tag
                            # ======================================

                            if canonical_name is None:

                                invalid_relationships_removed += 1

                                continue

                            # ======================================
                            # Valid canonical skill
                            # ======================================

                            canonical_skill = (
                                skill_by_name[
                                    canonical_name
                                ]
                            )

                            # --------------------------------------
                            # Prevent duplicate relationships
                            #
                            # Example:
                            #
                            # job -> JS
                            # job -> javascript
                            #
                            # becomes only:
                            #
                            # job -> javascript
                            # --------------------------------------

                            if (
                                canonical_skill.id
                                in seen_skill_ids
                            ):

                                # A redundant old relationship
                                # will disappear when job.skills
                                # is replaced.
                                normalized_relationships += 1

                                continue

                            seen_skill_ids.add(
                                canonical_skill.id
                            )

                            cleaned_skills.append(
                                canonical_skill
                            )

                            # --------------------------------------
                            # Count alias -> canonical redirect
                            # --------------------------------------

                            if (
                                canonical_skill.id
                                != old_skill.id
                            ):
                                normalized_relationships += 1

                        # ------------------------------------------
                        # Replace relationships with clean set
                        # ------------------------------------------

                        job.skills = cleaned_skills

                    except Exception:

                        failed_jobs += 1

                        logger.exception(
                            "Failed to clean skills "
                            f"for job id={job.id}"
                        )

                # ==================================================
                # 5. Flush relationship changes
                # ==================================================

                session.flush()

                # ==================================================
                # 6. Determine every Skill still referenced
                # ==================================================

                referenced_skill_ids: set[int] = {
                    skill.id
                    for job in jobs
                    for skill in job.skills
                }

                # ==================================================
                # 7. Delete obsolete / invalid Skill records
                # ==================================================
                #
                # We only consider the original Skill records here.
                #
                # Newly created canonical skills are retained.
                # ==================================================

                removable_ids: set[int] = set()

                for skill in skills:

                    canonical_name = (
                        canonical_by_id.get(
                            skill.id
                        )
                    )

                    # ----------------------------------------------
                    # Invalid and now unreferenced
                    # ----------------------------------------------

                    if canonical_name is None:

                        if (
                            skill.id
                            not in referenced_skill_ids
                        ):
                            removable_ids.add(
                                skill.id
                            )

                        continue

                    # ----------------------------------------------
                    # Alias and now unreferenced
                    # ----------------------------------------------

                    original_name = (
                        skill.name
                        .strip()
                        .lower()
                    )

                    if (
                        canonical_name
                        != original_name
                        and skill.id
                        not in referenced_skill_ids
                    ):

                        removable_ids.add(
                            skill.id
                        )

                # ==================================================
                # 8. Delete removable Skill rows
                # ==================================================

                if removable_ids:

                    result = session.execute(
                        delete(Skill).where(
                            Skill.id.in_(
                                removable_ids
                            )
                        )
                    )

                    deleted_skills = (
                        result.rowcount
                        or 0
                    )

                # ==================================================
                # 9. Commit atomically
                # ==================================================

                session.commit()

            except Exception:

                session.rollback()

                logger.exception(
                    "Existing skill cleanup failed."
                )

                raise

        # ==========================================================
        # 10. Final report
        # ==========================================================

        logger.info(
            "Existing skill cleanup complete: "
            f"relationships_normalized="
            f"{normalized_relationships}, "
            f"invalid_relationships_removed="
            f"{invalid_relationships_removed}, "
            f"skill_rows_deleted="
            f"{deleted_skills}, "
            f"failed_jobs="
            f"{failed_jobs}, "
            f"taxonomy_version="
            f"{SkillNormalizer.VERSION}"
        )

        return (
            normalized_relationships,
            deleted_skills,
            failed_jobs,
        )