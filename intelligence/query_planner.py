from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


# ==========================================================
# Supported Intents
# ==========================================================

SUPPORTED_INTENTS = {
    "top_skills",
    "find_jobs",
    "skill_comparison",
    "skill_relationships",
    "market_overview",
}


# ==========================================================
# Known Job Families
# ==========================================================

JOB_FAMILY_PATTERNS = {
    "Software Engineering": [
        "software engineering",
        "software engineer",
        "software developer",
        "developer",
        "backend",
        "frontend",
        "full stack",
        "fullstack",
    ],

    "DevOps & Cloud": [
        "devops",
        "cloud",
        "site reliability",
        "sre",
        "platform engineer",
    ],

    "Cybersecurity": [
        "cybersecurity",
        "cyber security",
        "security engineer",
        "information security",
    ],

    "Data > Data Engineering": [
        "data engineering",
        "data engineer",
    ],

    "Data > Data Science": [
        "data science",
        "data scientist",
    ],

    "Data > Analytics": [
        "data analytics",
        "data analyst",
        "analytics",
    ],

    "AI/ML > Machine Learning": [
        "machine learning",
        "ml engineer",
        "machine learning engineer",
    ],

    "AI/ML > Generative AI & LLM": [
        "generative ai",
        "genai",
        "large language model",
        "large language models",
        "llm",
        "llms",
        "rag",
    ],

    "Product & Management": [
        "product management",
        "product manager",
        "project manager",
    ],
}


# ==========================================================
# Experience Patterns
# ==========================================================

EXPERIENCE_PATTERNS = {
    "Entry": [
        "entry level",
        "entry-level",
        "entry",
        "junior",
        "graduate",
        "fresher",
    ],

    "Mid": [
        "mid level",
        "mid-level",
        "intermediate",
    ],

    "Senior": [
        "senior",
        "sr.",
        "sr",
    ],

    "Lead": [
        "lead",
        "team lead",
        "tech lead",
    ],

    "Executive": [
        "executive",
        "director",
        "chief",
        "vp",
        "vice president",
    ],
}


# ==========================================================
# Job Type Patterns
# ==========================================================

JOB_TYPE_PATTERNS = {
    "Full-time": [
        "full time",
        "full-time",
        "fulltime",
    ],

    "Part-time": [
        "part time",
        "part-time",
        "parttime",
    ],

    "Contract": [
        "contract",
        "contractor",
    ],

    "Internship": [
        "internship",
        "intern",
        "trainee",
    ],

    "Freelance": [
        "freelance",
        "freelancer",
    ],

    "Temporary": [
        "temporary",
        "temp job",
    ],
}


# ==========================================================
# Common Skills
# ==========================================================

SKILL_PATTERNS = {
    "python": [
        "python",
    ],

    "java": [
        "java",
    ],

    "javascript": [
        "javascript",
        "js",
    ],

    "typescript": [
        "typescript",
    ],

    "react": [
        "react",
        "reactjs",
        "react.js",
    ],

    "node.js": [
        "node",
        "nodejs",
        "node.js",
    ],

    "sql": [
        "sql",
    ],

    "postgresql": [
        "postgres",
        "postgresql",
    ],

    "mongodb": [
        "mongodb",
        "mongo",
    ],

    "aws": [
        "aws",
        "amazon web services",
    ],

    "azure": [
        "azure",
    ],

    "google cloud": [
        "google cloud",
        "gcp",
    ],

    "docker": [
        "docker",
    ],

    "kubernetes": [
        "kubernetes",
        "k8s",
    ],

    "git": [
        "git",
    ],

    "linux": [
        "linux",
    ],

    "terraform": [
        "terraform",
    ],

    "kafka": [
        "kafka",
    ],

    "spark": [
        "spark",
        "apache spark",
    ],

    "machine learning": [
        "machine learning",
    ],

    "artificial intelligence": [
        "artificial intelligence",
    ],

    "large language models": [
        "large language models",
        "large language model",
        "llm",
        "llms",
    ],

    "retrieval augmented generation": [
        "retrieval augmented generation",
        "rag",
    ],

    "computer vision": [
        "computer vision",
    ],

    "fastapi": [
        "fastapi",
    ],

    "django": [
        "django",
    ],

    "rest api": [
        "rest api",
        "restful api",
        "restful",
    ],

    "ci/cd": [
        "ci/cd",
        "cicd",
        "continuous integration",
    ],

    "devops": [
        "devops",
    ],
}


# ==========================================================
# Query Plan
# ==========================================================

@dataclass
class QueryPlan:
    intent: str

    filters: dict[str, Any] = field(
        default_factory=dict
    )

    skills: list[str] = field(
        default_factory=list
    )

    limit: int = 10

    original_question: str = ""

    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ==========================================================
# Query Planner
# ==========================================================

class QueryPlanner:

    VERSION = "query-planner-v2"

    DEFAULT_LIMIT = 10
    MAX_LIMIT = 50


    # ======================================================
    # Public API
    # ======================================================

    def plan(
        self,
        question: str,
    ) -> QueryPlan:

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        normalized = self._normalize(
            question
        )

        skills = self._extract_skills(
            normalized
        )

        filters: dict[str, Any] = {}


        # --------------------------------------------------
        # Remote
        # --------------------------------------------------

        remote = self._extract_remote(
            normalized
        )

        if remote is not None:
            filters["remote"] = remote


        # --------------------------------------------------
        # Job Family
        # --------------------------------------------------

        job_family = self._extract_from_patterns(
            normalized,
            JOB_FAMILY_PATTERNS,
        )

        if job_family:
            filters["job_family"] = job_family


        # --------------------------------------------------
        # Experience
        # --------------------------------------------------

        experience = self._extract_from_patterns(
            normalized,
            EXPERIENCE_PATTERNS,
        )

        if experience:
            filters["experience_level"] = experience


        # --------------------------------------------------
        # Job Type
        # --------------------------------------------------

        job_type = self._extract_from_patterns(
            normalized,
            JOB_TYPE_PATTERNS,
        )

        if job_type:
            filters["job_type"] = job_type


        # --------------------------------------------------
        # Country
        # --------------------------------------------------

        country = self._extract_country(
            normalized
        )

        if country:
            filters["country"] = country


        # --------------------------------------------------
        # Limit
        # --------------------------------------------------

        limit = self._extract_limit(
            normalized
        )


        # --------------------------------------------------
        # Intent
        # --------------------------------------------------

        intent = self._detect_intent(
            normalized,
            skills,
        )


        # --------------------------------------------------
        # Remove family terms from aggregate skill requests
        # --------------------------------------------------
        #
        # Example:
        #
        # "What technologies are common in DevOps and
        #  cloud roles?"
        #
        # DevOps describes the target job family here.
        # It should not also constrain the analytics to jobs
        # explicitly tagged with the "devops" skill.
        #
        # This cleanup is intentionally limited to aggregate
        # top-skills queries.
        # --------------------------------------------------

        if (
            intent == "top_skills"
            and job_family
        ):

            skills = (
                self._remove_job_family_skills(
                    skills=skills,
                    job_family=job_family,
                )
            )


        # --------------------------------------------------
        # Skill Filter for Find Jobs
        # --------------------------------------------------

        if (
            intent == "find_jobs"
            and len(skills) == 1
        ):
            filters["skill"] = skills[0]


        # --------------------------------------------------
        # Confidence
        # --------------------------------------------------

        confidence = self._estimate_confidence(
            intent=intent,
            filters=filters,
            skills=skills,
        )


        return QueryPlan(
            intent=intent,
            filters=filters,
            skills=skills,
            limit=limit,
            original_question=question,
            confidence=confidence,
        )


    # ======================================================
    # Normalize
    # ======================================================

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        text = text.lower()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()


    # ======================================================
    # Intent Detection
    # ======================================================

    def _detect_intent(
        self,
        text: str,
        skills: list[str],
    ) -> str:

        # --------------------------------------------------
        # 1. Skill Comparison
        # --------------------------------------------------

        comparison_patterns = [
            "compare",
            "comparison",
            "versus",
            "vs",
            "difference between",
            "more demand",
            "more demanded",
            "higher demand",
        ]

        if (
            len(skills) >= 2
            and self._contains_any(
                text,
                comparison_patterns,
            )
        ):
            return "skill_comparison"


        # --------------------------------------------------
        # 2. Skill Relationships
        # --------------------------------------------------

        relationship_patterns = [
            "related to",
            "related skills",
            "commonly occur",
            "commonly occurs",
            "commonly appear",
            "commonly appears",
            "co occur",
            "co-occur",
            "associated with",
            "skills alongside",
            "skills with",
        ]

        if (
            skills
            and self._contains_any(
                text,
                relationship_patterns,
            )
        ):
            return "skill_relationships"


        # --------------------------------------------------
        # 3. Top Skills / Common Technologies
        # --------------------------------------------------

        top_skill_regex_patterns = [

            # Explicit top-N skills
            r"\btop\s+\d+\s+skills?\b",
            r"\btop\s+skills?\b",

            # Demand wording
            r"\bmost\s+demanded\s+skills?\b",
            r"\bmost\s+in[\s-]+demand\s+skills?\b",
            r"\bdemanded\s+skills?\b",
            r"\bskills?\s+in\s+demand\b",
            r"\bskill\s+demand\b",

            # Common/popular skills
            r"\bmost\s+common\s+skills?\b",
            r"\bcommon\s+skills?\b",
            r"\bskills?\s+(?:are\s+)?common\b",
            r"\bcommonly\s+used\s+skills?\b",

            r"\bmost\s+popular\s+skills?\b",
            r"\bpopular\s+skills?\b",

            # Required skills
            r"\bskills?\s+(?:are\s+)?required\b",
            r"\bmost\s+required\s+skills?\b",

            # Explicit top technologies
            r"\btop\s+\d+\s+technologies\b",
            r"\btop\s+technologies\b",
            r"\bmost\s+demanded\s+technologies\b",

            # Common technologies
            r"\bmost\s+common\s+technologies\b",
            r"\bcommon\s+technologies\b",
            r"\btechnologies\s+(?:are\s+)?common\b",
            r"\btechnologies\s+(?:are\s+)?commonly\s+used\b",
            r"\bcommonly\s+used\s+technologies\b",

            # Common tools / tech stacks
            r"\bcommon\s+tools?\b",
            r"\btools?\s+(?:are\s+)?common\b",
            r"\bcommonly\s+used\s+tools?\b",

            r"\bcommon\s+tech(?:nology)?\s+stacks?\b",
            r"\btech(?:nology)?\s+stacks?\s+(?:are\s+)?common\b",
        ]

        if any(
            re.search(
                pattern,
                text,
            )
            for pattern
            in top_skill_regex_patterns
        ):
            return "top_skills"


        # --------------------------------------------------
        # 4. Find Jobs
        # --------------------------------------------------

        job_search_patterns = [
            "find jobs",
            "find job",
            "show jobs",
            "show me jobs",
            "list jobs",
            "job openings",
            "job opportunities",
            "positions",
            "vacancies",
            "roles",
        ]

        if self._contains_any(
            text,
            job_search_patterns,
        ):
            return "find_jobs"


        # --------------------------------------------------
        # 5. Market Overview
        # --------------------------------------------------

        overview_patterns = [
            "market overview",
            "job market overview",
            "market summary",
            "job market summary",
            "overall market",
            "how many jobs",
            "total jobs",
        ]

        if self._contains_any(
            text,
            overview_patterns,
        ):
            return "market_overview"


        # --------------------------------------------------
        # 6. Fallback
        # --------------------------------------------------

        if skills:
            return "find_jobs"

        return "market_overview"


    # ======================================================
    # Skill Extraction
    # ======================================================

    def _extract_skills(
        self,
        text: str,
    ) -> list[str]:

        found: list[str] = []

        for (
            canonical_skill,
            patterns,
        ) in SKILL_PATTERNS.items():

            if self._contains_any(
                text,
                patterns,
            ):

                found.append(
                    canonical_skill
                )

        return found


    # ======================================================
    # Remove Job-Family Skills From Aggregate Query
    # ======================================================

    @staticmethod
    def _remove_job_family_skills(
        skills: list[str],
        job_family: str,
    ) -> list[str]:
        """
        Remove skill terms that are acting as job-family
        descriptors in aggregate top-skills questions.

        This avoids treating a phrase such as "DevOps roles"
        as both:

            job_family = DevOps & Cloud

        and:

            skill = devops

        when the user is asking which technologies are
        common across that job family.
        """

        family_skill_map = {

            "DevOps & Cloud": {
                "devops",
            },

            "AI/ML > Machine Learning": {
                "machine learning",
            },

            "AI/ML > Generative AI & LLM": {
                "large language models",
                "retrieval augmented generation",
            },

            "Cybersecurity": {
                "artificial intelligence",
            },
        }


        removable = (
            family_skill_map.get(
                job_family,
                set(),
            )
        )


        return [
            skill
            for skill in skills
            if skill not in removable
        ]


    # ======================================================
    # Remote Extraction
    # ======================================================

    @staticmethod
    def _extract_remote(
        text: str,
    ) -> bool | None:

        non_remote_patterns = [
            "non remote",
            "non-remote",
            "not remote",
            "on site",
            "on-site",
            "onsite",
        ]

        for pattern in non_remote_patterns:

            if pattern in text:
                return False


        remote_patterns = [
            "remote",
            "work from home",
            "wfh",
        ]

        for pattern in remote_patterns:

            if pattern in text:
                return True

        return None


    # ======================================================
    # Country Extraction
    # ======================================================

    @staticmethod
    def _extract_country(
        text: str,
    ) -> str | None:

        countries = {
            "india": "India",
            "germany": "Germany",
            "united states": "United States",
            "usa": "United States",
            "u.s.": "United States",
            "uk": "United Kingdom",
            "united kingdom": "United Kingdom",
            "australia": "Australia",
            "canada": "Canada",
            "spain": "Spain",
            "brazil": "Brazil",
            "france": "France",
            "philippines": "Philippines",
            "indonesia": "Indonesia",
            "peru": "Peru",
            "ecuador": "Ecuador",
            "venezuela": "Venezuela",
        }


        # Longer aliases first.

        for alias in sorted(
            countries,
            key=len,
            reverse=True,
        ):

            if QueryPlanner._phrase_exists(
                text,
                alias,
            ):

                return countries[
                    alias
                ]

        return None


    # ======================================================
    # Limit Extraction
    # ======================================================

    def _extract_limit(
        self,
        text: str,
    ) -> int:

        patterns = [
            r"\btop\s+(\d{1,3})\b",
            r"\bfirst\s+(\d{1,3})\b",
            r"\bshow\s+(?:me\s+)?(\d{1,3})\b",
            r"\blist\s+(?:the\s+)?(?:top\s+)?(\d{1,3})\b",
        ]


        for pattern in patterns:

            match = re.search(
                pattern,
                text,
            )

            if match:

                value = int(
                    match.group(1)
                )

                return max(
                    1,
                    min(
                        value,
                        self.MAX_LIMIT,
                    ),
                )

        return self.DEFAULT_LIMIT


    # ======================================================
    # Generic Pattern Extraction
    # ======================================================

    @classmethod
    def _extract_from_patterns(
        cls,
        text: str,
        mapping: dict[str, list[str]],
    ) -> str | None:

        # Search longer phrases first.

        candidates: list[
            tuple[str, str]
        ] = []


        for (
            canonical,
            patterns,
        ) in mapping.items():

            for pattern in patterns:

                candidates.append(
                    (
                        canonical,
                        pattern,
                    )
                )


        candidates.sort(
            key=lambda item: len(
                item[1]
            ),
            reverse=True,
        )


        for (
            canonical,
            pattern,
        ) in candidates:

            if cls._phrase_exists(
                text,
                pattern,
            ):

                return canonical

        return None


    # ======================================================
    # Helpers
    # ======================================================

    @classmethod
    def _contains_any(
        cls,
        text: str,
        patterns: list[str],
    ) -> bool:

        return any(
            cls._phrase_exists(
                text,
                pattern,
            )
            for pattern in patterns
        )


    @staticmethod
    def _phrase_exists(
        text: str,
        phrase: str,
    ) -> bool:

        phrase = (
            phrase
            .strip()
            .lower()
        )

        if not phrase:
            return False


        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(
                phrase
            )
            + r"(?![a-z0-9])"
        )


        return bool(
            re.search(
                pattern,
                text,
            )
        )


    # ======================================================
    # Confidence
    # ======================================================

    @staticmethod
    def _estimate_confidence(
        intent: str,
        filters: dict[str, Any],
        skills: list[str],
    ) -> float:

        score = 0.60


        if intent in SUPPORTED_INTENTS:
            score += 0.15


        if filters:
            score += 0.10


        if skills:
            score += 0.10


        return min(
            round(
                score,
                2,
            ),
            0.95,
        )