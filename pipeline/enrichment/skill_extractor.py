from __future__ import annotations

import re

from pipeline.enrichment.skill_normalizer import SkillNormalizer


class SkillExtractor:
    """
    Extract technical skills from:

    1. Source-provided tags/skills
    2. Job title
    3. Job description

    The extractor uses SkillNormalizer as the canonical
    skill taxonomy.

    Important:
    - Invalid metadata such as "remote" is rejected.
    - Duplicate skills are removed.
    - Aliases are converted to canonical names.
    - Ambiguous terms such as "go" and "r" use stricter
      matching to reduce false positives.
    """

    VERSION = "skill-extractor-v1.1"

    # ==========================================================
    # Extract
    # ==========================================================

    def extract(
        self,
        title: str | None,
        description: str | None,
        source_skills: list[str] | None = None,
    ) -> list[str]:
        """
        Extract canonical skills from the supplied job data.
        """

        extracted: list[str] = []
        seen: set[str] = set()

        # ======================================================
        # 1. Source-provided skills
        # ======================================================
        #
        # These may contain:
        #
        # Python
        # JS
        # remote
        # digital nomad
        #
        # SkillNormalizer removes invalid metadata and converts
        # valid aliases to canonical values.
        # ======================================================

        normalized_source_skills = (
            SkillNormalizer.normalize_many(
                source_skills or []
            )
        )

        for skill in normalized_source_skills:
            self._add(
                skill=skill,
                extracted=extracted,
                seen=seen,
            )

        # ======================================================
        # 2. Prepare searchable text
        # ======================================================

        title_text = self._normalize_text(
            title
        )

        description_text = self._normalize_text(
            description
        )

        combined_text = (
            f"{title_text} {description_text}"
        ).strip()

        if not combined_text:
            return extracted

        # ======================================================
        # 3. Search taxonomy aliases
        # ======================================================
        #
        # We search ALIASES.keys() rather than only canonical
        # names because descriptions may contain aliases such as:
        #
        # ML
        # LLM
        # K8s
        # postgres
        # sklearn
        # GenAI
        #
        # Each matched alias is converted to its canonical skill.
        # ======================================================

        for alias, canonical in (
            SkillNormalizer.ALIASES.items()
        ):

            if self._contains_term(
                text=combined_text,
                term=alias,
            ):
                self._add(
                    skill=canonical,
                    extracted=extracted,
                    seen=seen,
                )

        return extracted

    # ==========================================================
    # Add canonical skill
    # ==========================================================

    @staticmethod
    def _add(
        skill: str,
        extracted: list[str],
        seen: set[str],
    ) -> None:
        """
        Normalize, validate and add a skill exactly once.
        """

        canonical = (
            SkillNormalizer.normalize(
                skill
            )
        )

        if not canonical:
            return

        if not SkillNormalizer.is_valid_skill(
            canonical
        ):
            return

        if canonical in seen:
            return

        seen.add(
            canonical
        )

        extracted.append(
            canonical
        )

    # ==========================================================
    # Normalize text
    # ==========================================================

    @staticmethod
    def _normalize_text(
        text: str | None,
    ) -> str:
        """
        Prepare title/description for matching.
        """

        if not text:
            return ""

        value = str(
            text
        ).lower()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    # ==========================================================
    # Match taxonomy term
    # ==========================================================

    @staticmethod
    def _contains_term(
        text: str,
        term: str,
    ) -> bool:
        """
        Determine whether a taxonomy term occurs in the job text.

        Normal terms use token-boundary matching.

        Ambiguous short terms such as Go and R receive stricter
        handling because they commonly appear in ordinary prose.

        Examples:

        Python
            "Python developer"
            -> MATCH

        Java
            "JavaScript developer"
            -> DOES NOT MATCH Java

        Go
            "ready to go"
            -> DOES NOT MATCH

            "Go developer"
            -> MATCH

            "Golang backend engineer"
            -> MATCH

        R
            ordinary letter "r"
            -> DOES NOT MATCH

            "programming in R"
            -> MATCH

        C++
            supported

        .NET
            supported

        Node.js
            supported

        CI/CD
            supported
        """

        term = term.strip().lower()

        if not term:
            return False

        # ======================================================
        # GO / GOLANG
        # ======================================================
        #
        # "go" is extremely ambiguous.
        #
        # Bad matches:
        #
        #   ready to go
        #   go to market
        #   go through the process
        #
        # Good matches:
        #
        #   Go developer
        #   Go engineer
        #   Go programming
        #   Go backend
        #   Golang
        #   experience in Go
        # ======================================================

        if term == "go":

            patterns = [
                r"\bgolang\b",

                (
                    r"\bgo\s+"
                    r"(?:developer|engineer|programming|"
                    r"backend|language|microservices|"
                    r"service|services)\b"
                ),

                (
                    r"\b(?:developer|engineer|programming|"
                    r"backend|written|code|coding|"
                    r"experience|proficiency|knowledge|"
                    r"skills?)\s+"
                    r"(?:with|in|using)?\s*go\b"
                ),
            ]

            return any(
                re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
                is not None
                for pattern in patterns
            )

        # ======================================================
        # R PROGRAMMING LANGUAGE
        # ======================================================
        #
        # A raw search for "r" would match huge amounts of text.
        # Require programming-related context.
        # ======================================================

        if term == "r":

            patterns = [
                r"\br programming\b",
                r"\br language\b",
                r"\bprogramming in r\b",
                r"\bexperience (?:with|in) r\b",
                r"\bproficiency (?:with|in) r\b",
                r"\bknowledge of r\b",
                r"\busing r\b",
            ]

            return any(
                re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
                is not None
                for pattern in patterns
            )

        # ======================================================
        # AI
        # ======================================================

        if term == "ai":

            pattern = (
                r"(?<![a-z0-9])"
                r"ai"
                r"(?![a-z0-9])"
            )

            return (
                re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
                is not None
            )

        # ======================================================
        # ML
        # ======================================================

        if term == "ml":

            pattern = (
                r"(?<![a-z0-9])"
                r"ml"
                r"(?![a-z0-9])"
            )

            return (
                re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
                is not None
            )

        # ======================================================
        # RL
        # ======================================================

        if term == "rl":

            pattern = (
                r"(?<![a-z0-9])"
                r"rl"
                r"(?![a-z0-9])"
            )

            return (
                re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
                is not None
            )

        # ======================================================
        # CV
        # ======================================================
        #
        # CV can mean Computer Vision but can also mean
        # curriculum vitae.
        #
        # We therefore require technical context rather than
        # accepting every occurrence of "CV".
        # ======================================================

        if term == "cv":

            patterns = [
                r"\bcv\s+(?:engineer|engineering|model|models|system|systems)\b",
                r"\bcomputer vision\b",
                r"\bexperience (?:with|in) cv\b",
                r"\bknowledge of cv\b",
            ]

            return any(
                re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
                is not None
                for pattern in patterns
            )

        # ======================================================
        # NORMAL TAXONOMY TERMS
        # ======================================================
        #
        # (?<![a-z0-9]) and (?![a-z0-9]) prevent substring
        # mistakes.
        #
        # Example:
        #
        # Searching "java" against:
        #
        # javascript
        #
        # will NOT match.
        # ======================================================

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(term)
            + r"(?![a-z0-9])"
        )

        return (
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            is not None
        )