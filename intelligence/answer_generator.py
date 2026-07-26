from __future__ import annotations

from typing import Any

from intelligence.query_planner import QueryPlan


class AnswerGenerator:
    """
    Converts structured QueryEngine evidence into a
    human-readable market intelligence response.

    This version is deterministic:
    - no hallucinated statistics
    - no arbitrary SQL
    - every numerical claim comes from QueryEngine
    """

    VERSION = "answer-generator-v1"


    # ======================================================
    # Public API
    # ======================================================

    def generate(
        self,
        plan: QueryPlan,
        evidence: dict[str, Any],
    ) -> str:

        intent = evidence.get(
            "intent",
            plan.intent,
        )

        if intent == "top_skills":
            return self._top_skills(
                plan,
                evidence,
            )

        if intent == "find_jobs":
            return self._find_jobs(
                plan,
                evidence,
            )

        if intent == "skill_comparison":
            return self._skill_comparison(
                plan,
                evidence,
            )

        if intent == "skill_relationships":
            return self._skill_relationships(
                plan,
                evidence,
            )

        if intent == "market_overview":
            return self._market_overview(
                plan,
                evidence,
            )

        return (
            "I could not generate an answer for "
            "this type of market analysis."
        )


    # ======================================================
    # Top Skills
    # ======================================================

    def _top_skills(
        self,
        plan: QueryPlan,
        evidence: dict[str, Any],
    ) -> str:

        data = evidence.get(
            "data",
            [],
        )

        total_jobs = evidence.get(
            "total_matching_jobs",
            0,
        )

        scope = self._describe_scope(
            plan.filters
        )

        if total_jobs == 0:

            return (
                f"No jobs matched {scope}, so there "
                "is not enough evidence to rank skills."
            )

        if not data:

            return (
                f"{total_jobs:,} jobs matched {scope}, "
                "but no normalized skills were available "
                "for those jobs."
            )

        lines = [
            (
                f"I found {total_jobs:,} jobs matching "
                f"{scope}. The leading skills are:"
            )
        ]

        for index, item in enumerate(
            data,
            start=1,
        ):

            skill = item.get(
                "skill",
                "Unknown",
            )

            count = item.get(
                "job_count",
                0,
            )

            percentage = item.get(
                "percentage",
                0.0,
            )

            lines.append(
                f"{index}. {skill} — "
                f"{count:,} jobs "
                f"({percentage:.2f}% of matching jobs)"
            )

        top = data[0]

        lines.append(
            (
                f"The strongest skill signal in this "
                f"subset is {top.get('skill', 'Unknown')}, "
                f"appearing in "
                f"{top.get('job_count', 0):,} jobs."
            )
        )

        return "\n".join(lines)


    # ======================================================
    # Find Jobs
    # ======================================================

    def _find_jobs(
        self,
        plan: QueryPlan,
        evidence: dict[str, Any],
    ) -> str:

        data = evidence.get(
            "data",
            [],
        )

        total_jobs = evidence.get(
            "total_matching_jobs",
            0,
        )

        scope = self._describe_scope(
            plan.filters
        )

        if total_jobs == 0:

            return (
                f"No jobs in the current dataset matched "
                f"{scope}."
            )

        lines = [
            (
                f"I found {total_jobs:,} jobs matching "
                f"{scope}."
            )
        ]

        if not data:

            lines.append(
                "No job records were returned for display."
            )

            return "\n".join(lines)

        lines.append(
            (
                f"Here are {len(data):,} "
                "of the matching positions:"
            )
        )

        for index, job in enumerate(
            data,
            start=1,
        ):

            title = (
                job.get("title")
                or "Unknown position"
            )

            company = (
                job.get("company")
                or "Unknown company"
            )

            location = self._format_location(
                job.get("location")
            )

            lines.append(
                f"{index}. {title} — "
                f"{company} — {location}"
            )

        if total_jobs > len(data):

            lines.append(
                (
                    f"{total_jobs - len(data):,} additional "
                    "matching jobs are available in the "
                    "dataset."
                )
            )

        return "\n".join(lines)


    # ======================================================
    # Skill Comparison
    # ======================================================

    def _skill_comparison(
        self,
        plan: QueryPlan,
        evidence: dict[str, Any],
    ) -> str:

        data = evidence.get(
            "data",
            [],
        )

        message = evidence.get(
            "message"
        )

        if message:
            return message

        if len(data) < 2:

            return (
                "There is not enough skill evidence "
                "to perform the requested comparison."
            )

        total_jobs = evidence.get(
            "total_matching_jobs",
            0,
        )

        scope = self._describe_scope(
            plan.filters
        )

        lines = [
            (
                f"Across {total_jobs:,} jobs matching "
                f"{scope}:"
            )
        ]

        for item in data:

            lines.append(
                (
                    f"- {item.get('skill', 'Unknown')}: "
                    f"{item.get('job_count', 0):,} jobs "
                    f"({item.get('percentage', 0.0):.2f}%)"
                )
            )

        highest = data[0]
        second = data[1]

        highest_count = highest.get(
            "job_count",
            0,
        )

        second_count = second.get(
            "job_count",
            0,
        )

        difference = (
            highest_count
            - second_count
        )

        if highest_count == second_count:

            lines.append(
                (
                    f"{highest.get('skill', 'The first skill')} "
                    f"and {second.get('skill', 'the second skill')} "
                    "have equal demand in this subset."
                )
            )

        else:

            lines.append(
                (
                    f"{highest.get('skill', 'The leading skill')} "
                    "has the stronger demand signal, appearing "
                    f"in {difference:,} more jobs than "
                    f"{second.get('skill', 'the comparison skill')}."
                )
            )

        return "\n".join(lines)


    # ======================================================
    # Skill Relationships
    # ======================================================

    def _skill_relationships(
        self,
        plan: QueryPlan,
        evidence: dict[str, Any],
    ) -> str:

        message = evidence.get(
            "message"
        )

        if message:
            return message

        target_skill = evidence.get(
            "target_skill",
            "the requested skill",
        )

        total_jobs = evidence.get(
            "total_matching_jobs",
            0,
        )

        data = evidence.get(
            "data",
            [],
        )

        if total_jobs == 0:

            return (
                f"No jobs containing {target_skill} were "
                "found in the requested market subset."
            )

        if not data:

            return (
                f"I found {total_jobs:,} jobs containing "
                f"{target_skill}, but no additional normalized "
                "skills co-occurred frequently enough to report."
            )

        lines = [
            (
                f"{target_skill} appears in {total_jobs:,} "
                "matching jobs. The skills most commonly "
                "associated with it are:"
            )
        ]

        for index, item in enumerate(
            data,
            start=1,
        ):

            lines.append(
                (
                    f"{index}. "
                    f"{item.get('skill', 'Unknown')} — "
                    f"{item.get('co_occurrence_count', 0):,} "
                    "co-occurrences "
                    f"({item.get('percentage', 0.0):.2f}%)"
                )
            )

        return "\n".join(lines)


    # ======================================================
    # Market Overview
    # ======================================================

    def _market_overview(
        self,
        plan: QueryPlan,
        evidence: dict[str, Any],
    ) -> str:

        data = evidence.get(
            "data",
            {},
        )

        total_jobs = data.get(
            "total_jobs",
            0,
        )

        total_companies = data.get(
            "total_companies",
            0,
        )

        total_locations = data.get(
            "total_locations",
            0,
        )

        remote_jobs = data.get(
            "remote_jobs",
            0,
        )

        remote_percentage = data.get(
            "remote_percentage",
            0.0,
        )

        scope = self._describe_scope(
            plan.filters
        )

        if total_jobs == 0:

            return (
                f"No jobs matched {scope} in the "
                "current dataset."
            )

        return (
            f"The market subset for {scope} contains "
            f"{total_jobs:,} jobs across "
            f"{total_companies:,} companies and "
            f"{total_locations:,} locations. "
            f"{remote_jobs:,} positions are marked remote, "
            f"representing {remote_percentage:.2f}% "
            "of the matching jobs."
        )


    # ======================================================
    # Scope Description
    # ======================================================

    @staticmethod
    def _describe_scope(
        filters: dict[str, Any],
    ) -> str:

        if not filters:
            return "the current job market dataset"

        parts: list[str] = []


        job_family = filters.get(
            "job_family"
        )

        if job_family:
            parts.append(
                f"job family '{job_family}'"
            )


        experience = filters.get(
            "experience_level"
        )

        if experience:
            parts.append(
                f"experience level '{experience}'"
            )


        job_type = filters.get(
            "job_type"
        )

        if job_type:
            parts.append(
                f"job type '{job_type}'"
            )


        country = filters.get(
            "country"
        )

        if country:
            parts.append(
                f"country '{country}'"
            )


        skill = filters.get(
            "skill"
        )

        if skill:
            parts.append(
                f"skill '{skill}'"
            )


        remote = filters.get(
            "remote"
        )

        if remote is True:
            parts.append(
                "remote positions"
            )

        elif remote is False:
            parts.append(
                "non-remote positions"
            )


        if not parts:
            return "the current job market dataset"


        if len(parts) == 1:
            return parts[0]


        return ", ".join(
            parts[:-1]
        ) + " and " + parts[-1]


    # ======================================================
    # Location Formatting
    # ======================================================

    @staticmethod
    def _format_location(
        location: dict[str, Any] | None,
    ) -> str:

        if not location:
            return "Location unavailable"


        parts = [
            location.get("city"),
            location.get("state"),
            location.get("country"),
        ]


        parts = [
            part
            for part in parts
            if part
        ]


        location_text = (
            ", ".join(parts)
            if parts
            else "Location unavailable"
        )


        if location.get("remote"):

            if location_text == (
                "Location unavailable"
            ):
                return "Remote"

            return (
                f"{location_text} (Remote)"
            )


        return location_text