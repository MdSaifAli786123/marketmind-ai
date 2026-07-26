from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EnrichmentResult:
    experience_level: str
    job_type: str
    job_family: str
    job_family_score: int


class JobEnricher:
    """
    Deterministic job enrichment classifier.

    Rules-v3.2:
    - Preserves the validated rules-v3.1 job-family classifier.
    - Separates internship job type from experience level.
    - Adds Lead as a distinct experience level.
    - Expands German and English experience vocabulary.
    - Expands German and English employment-type vocabulary.
    - Separates Freelance, Contract, and Temporary.
    - Uses explicit evidence rather than assuming employment type.
    """

    VERSION = "rules-v3.2"

    TITLE_WEIGHT = 6
    SKILL_WEIGHT = 3
    DESCRIPTION_WEIGHT = 1

    MIN_FAMILY_SCORE = 6

    # ======================================================
    # Experience
    # ======================================================

    EXPERIENCE_EXECUTIVE_TERMS = (
        "chief executive officer",
        "chief technology officer",
        "chief operating officer",
        "chief information officer",
        "chief data officer",
        "ceo",
        "cto",
        "cio",
        "coo",
        "managing director",
        "geschäftsführer",
        "geschäftsführerin",
    )

    EXPERIENCE_LEAD_TERMS = (
        "head of",
        "team lead",
        "teamlead",
        "teamleiter",
        "teamleiterin",
        "regionalleiter",
        "regionalleiterin",
    )

    EXPERIENCE_SENIOR_TERMS = (
        "senior",
        "sr.",
        "sr ",
        "principal",
        "staff engineer",
        "staff software engineer",
        "staff developer",
        "staff scientist",
    )

    EXPERIENCE_ENTRY_TERMS = (
        "junior",
        "jr.",
        "jr ",
        "entry level",
        "entry-level",
        "graduate engineer",
        "graduate developer",
        "new grad",
        "trainee",
        "working student",
        "werkstudent",
        "werkstudentin",
        "praktikum",
        "pflichtpraktikum",
        "praktikant",
        "praktikantin",
        "ausbildung",
        "apprentice",
    )

    EXPERIENCE_MID_TERMS = (
        "mid level",
        "mid-level",
        "mid level engineer",
        "mid-level engineer",
        "intermediate engineer",
        "intermediate developer",
    )

    # ======================================================
    # Employment type
    # ======================================================

    JOB_TYPE_INTERNSHIP_TERMS = (
        "internship",
        "intern position",
        "summer intern",
        "student intern",
        "praktikum",
        "pflichtpraktikum",
        "praktikant",
        "praktikantin",
    )

    JOB_TYPE_FREELANCE_TERMS = (
        "freelance",
        "freelancer",
        "freiberuflich",
        "freiberufliche",
        "freiberuflicher",
        "freiberuflerin",
        "selbstständig",
        "selbststaendig",
        "self-employed",
    )

    JOB_TYPE_TEMPORARY_TERMS = (
        "temporary",
        "temporary position",
        "fixed-term",
        "fixed term",
        "befristet",
        "befristete",
        "befristeter",
        "interim",
        "elternzeitvertretung",
    )

    JOB_TYPE_PART_TIME_TERMS = (
        "part-time",
        "part time",
        "teilzeit",
        "minijob",
        "mini-job",
        "mini job",
        "working student",
        "werkstudent",
        "werkstudentin",
    )

    JOB_TYPE_CONTRACT_TERMS = (
        "contract role",
        "contract position",
        "contractor",
    )

    JOB_TYPE_FULL_TIME_TERMS = (
        "full-time",
        "full time",
        "vollzeit",
    )

    # ======================================================
    # Strong occupational-title rules
    #
    # Preserved from validated rules-v3.1.
    # ======================================================

    PRODUCT_TITLE_TERMS = (
        "product manager",
        "product owner",
        "program manager",
        "project manager",
        "engineering manager",
        "technical program manager",
        "projektmanager",
        "projekt manager",
        "projektleiter",
        "projektleitung",
        "projekt leitung",

        # Common misspelling observed in scraped data.
        "projektlekitung",
    )

    AI_ENGINEERING_TITLE_TERMS = (
        "ai engineer",
        "artificial intelligence engineer",
        "ai developer",
        "machine learning engineer",
        "ml engineer",
    )

    # ======================================================
    # Explicit GenAI evidence
    # ======================================================

    GENAI_TERMS = (
        "generative ai",
        "gen ai",
        "genai",
        "large language model",
        "large language models",
        "llm",
        "llms",
        "langchain",
        "retrieval augmented generation",
        "retrieval-augmented generation",
        "rag",
        "prompt engineer",
        "prompt engineering",
        "foundation model",
        "foundation models",
        "copilot engineer",
        "agentic ai",
        "ai agent",
        "ai agents",
        "multimodal ai",
    )

    # ======================================================
    # Job families
    # ======================================================

    JOB_FAMILY_RULES = (
        (
            "AI/ML > Generative AI & LLM",
            GENAI_TERMS,
        ),
        (
            "AI/ML > Computer Vision",
            (
                "computer vision",
                "computer vision engineer",
                "vision engineer",
                "image recognition",
                "image segmentation",
                "object detection",
                "opencv",
                "vision transformer",
                "image processing",
            ),
        ),
        (
            "AI/ML > NLP",
            (
                "nlp engineer",
                "natural language processing",
                "computational linguist",
                "text classification",
                "named entity recognition",
                "language model engineer",
            ),
        ),
        (
            "AI/ML > Machine Learning",
            (
                "machine learning",
                "machine learning engineer",
                "ml engineer",
                "mlops",
                "deep learning",
                "robot learning",
                "ai engineer",
                "artificial intelligence engineer",
                "ai developer",
            ),
        ),
        (
            "Data > Data Science",
            (
                "data scientist",
                "data science",
                "applied scientist",
                "research scientist",
                "decision scientist",
            ),
        ),
        (
            "Data > Data Engineering",
            (
                "data engineer",
                "data engineering",
                "analytics engineer",
                "etl developer",
                "etl engineer",
                "data platform engineer",
                "data warehouse engineer",
            ),
        ),
        (
            "Data > Analytics",
            (
                "data analyst",
                "business intelligence analyst",
                "bi analyst",
                "business analyst",
                "analytics analyst",

                # German analytics/research vocabulary.
                "marktforschung",
                "marktforscher",
                "marktanalyse",
                "datenanalyst",
                "datenanalyse",
            ),
        ),
        (
            "DevOps & Cloud",
            (
                "devops engineer",
                "devops",
                "site reliability engineer",
                "site reliability",
                "sre",
                "cloud engineer",
                "cloud architect",
                "platform engineer",
                "infrastructure engineer",
                "cloud platform architect",
                "system engineer",
                "systems engineer",
                "system administrator",
                "systems administrator",
                "systemadministrator",
                "sysadmin",
                "it system engineer",
                "it-system engineer",
                "it infrastructure engineer",
                "infrastructure administrator",

                # v3.1
                "it operations engineer",
                "operations engineer",
                "cloud operations engineer",
                "infrastructure operations",
                "platform operations",
            ),
        ),
        (
            "Cybersecurity",
            (
                "cybersecurity",
                "cyber security",
                "security engineer",
                "security analyst",
                "security consultant",
                "information security",
                "application security",
                "cloud security",
                "soc analyst",
                "penetration tester",
                "isms",
                "information security management",
                "security operations center",
                "soc automation",
                "grc",
                "governance risk compliance",
                "governance risk and compliance",

                # Microsoft information protection / governance.
                "microsoft purview",
                "purview consultant",
                "data loss prevention",
                "information protection",
            ),
        ),
        (
            "Software Engineering",
            (
                "software engineer",
                "software developer",
                "backend engineer",
                "backend developer",
                "frontend engineer",
                "frontend developer",
                "front end engineer",
                "front end developer",
                "full stack engineer",
                "full stack developer",
                "full-stack engineer",
                "full-stack developer",
                "web developer",
                "mobile developer",
                "android developer",
                "ios developer",
                "java developer",
                "python developer",
                "golang developer",
                "c++ developer",
                "c++ engineer",

                # German equivalents.
                "softwareentwickler",
                "software entwickler",
                "softwareentwicklung",
            ),
        ),
        (
            "Product & Management",
            PRODUCT_TITLE_TERMS,
        ),
    )

    # ======================================================
    # Exclusion rules
    # ======================================================

    SAP_ERP_CONSULTING_TERMS = (
        "sap consultant",
        "sap berater",
        "sap beratung",
        "sap sd",
        "sap mm",
        "sap hcm",
        "sap fi",
        "sap fico",
        "sap s/4hana",
        "s/4hana",
        "erp consultant",
        "application consultant",
        "inhouse berater",
    )

    MARKETING_ANALYTICS_TERMS = (
        "performance marketing",
        "performance & analytics",
        "performance analytics manager",
        "google performance",
        "marketing analytics manager",
        "digital marketing",
        "paid media",
        "seo",
        "sem manager",
    )

    IT_SUPPORT_TERMS = (
        "it support",
        "it-support",
        "help desk",
        "helpdesk",
        "service desk",
        "it allrounder",
        "it-allrounder",
        "technical support",
        "support specialist",
    )

    # ======================================================
    # Public API
    # ======================================================

    def enrich(
        self,
        title: str,
        description: str,
        skills: list[str],
    ) -> EnrichmentResult:

        title_text = self._normalize_text(
            title
        )

        description_text = self._normalize_text(
            description
        )

        skill_text = " ".join(
            self._normalize_text(skill)
            for skill in skills
        )

        experience_level = (
            self._infer_experience(
                title_text,
                description_text,
            )
        )

        job_type = self._infer_job_type(
            title_text,
            description_text,
        )

        job_family, score = (
            self._infer_job_family(
                title_text,
                description_text,
                skill_text,
            )
        )

        return EnrichmentResult(
            experience_level=experience_level,
            job_type=job_type,
            job_family=job_family,
            job_family_score=score,
        )

    # ======================================================
    # Experience
    # ======================================================

    def _infer_experience(
        self,
        title: str,
        description: str,
    ) -> str:

        # --------------------------------------------------
        # 1. Strong title hierarchy
        # --------------------------------------------------

        if self._contains_any(
            title,
            self.EXPERIENCE_EXECUTIVE_TERMS,
        ):
            return "Executive"

        if self._contains_any(
            title,
            self.EXPERIENCE_LEAD_TERMS,
        ):
            return "Lead"

        if self._contains_any(
            title,
            self.EXPERIENCE_SENIOR_TERMS,
        ):
            return "Senior"

        if self._contains_any(
            title,
            self.EXPERIENCE_ENTRY_TERMS,
        ):
            return "Entry"

        if self._contains_any(
            title,
            self.EXPERIENCE_MID_TERMS,
        ):
            return "Mid"

        # --------------------------------------------------
        # 2. Explicit required years
        # --------------------------------------------------

        years = self._extract_required_years(
            description
        )

        if years is None:
            return "Unknown"

        # Years alone should not imply an executive role.
        # Executive requires explicit occupational hierarchy.

        if years >= 5:
            return "Senior"

        if years >= 2:
            return "Mid"

        return "Entry"

    # ======================================================
    # Job type
    # ======================================================

    def _infer_job_type(
        self,
        title: str,
        description: str,
    ) -> str:

        # --------------------------------------------------
        # Title evidence
        # --------------------------------------------------

        job_type = (
            self._job_type_from_text(
                title
            )
        )

        if job_type is not None:
            return job_type

        # --------------------------------------------------
        # Description evidence
        # --------------------------------------------------

        job_type = (
            self._job_type_from_text(
                description
            )
        )

        if job_type is not None:
            return job_type

        return "Unknown"

    def _job_type_from_text(
        self,
        text: str,
    ) -> str | None:

        # Internship is checked before general employment
        # types because internship language is highly explicit.

        if self._contains_any(
            text,
            self.JOB_TYPE_INTERNSHIP_TERMS,
        ):
            return "Internship"

        # Freelance is its own enum and must not be collapsed
        # into Contract.

        if self._contains_any(
            text,
            self.JOB_TYPE_FREELANCE_TERMS,
        ):
            return "Freelance"

        # Interim / fixed-term evidence precedes part-time and
        # full-time because duration and weekly hours describe
        # different dimensions.

        if self._contains_any(
            text,
            self.JOB_TYPE_TEMPORARY_TERMS,
        ):
            return "Temporary"

        if self._contains_any(
            text,
            self.JOB_TYPE_PART_TIME_TERMS,
        ):
            return "Part-time"

        if self._contains_any(
            text,
            self.JOB_TYPE_CONTRACT_TERMS,
        ):
            return "Contract"

        if self._contains_any(
            text,
            self.JOB_TYPE_FULL_TIME_TERMS,
        ):
            return "Full-time"

        return None

    # ======================================================
    # Job family
    # ======================================================

    def _infer_job_family(
        self,
        title: str,
        description: str,
        skills: str,
    ) -> tuple[str, int]:

        # --------------------------------------------------
        # 1. Exclusions
        # --------------------------------------------------

        if self._contains_any(
            title,
            self.SAP_ERP_CONSULTING_TERMS,
        ):
            return (
                "Other",
                self.TITLE_WEIGHT,
            )

        if self._contains_any(
            title,
            self.MARKETING_ANALYTICS_TERMS,
        ):
            return (
                "Other",
                self.TITLE_WEIGHT,
            )

        if self._contains_any(
            title,
            self.IT_SUPPORT_TERMS,
        ):
            return (
                "Other",
                self.TITLE_WEIGHT,
            )

        # --------------------------------------------------
        # 2. Occupational-title precedence
        # --------------------------------------------------

        if self._contains_any(
            title,
            self.PRODUCT_TITLE_TERMS,
        ):
            return (
                "Product & Management",
                self.TITLE_WEIGHT,
            )

        # --------------------------------------------------
        # 3. AI engineering title precedence
        # --------------------------------------------------

        if self._contains_any(
            title,
            self.AI_ENGINEERING_TITLE_TERMS,
        ):

            genai_evidence = (
                self._contains_any(
                    title,
                    self.GENAI_TERMS,
                )
                or self._contains_any(
                    skills,
                    self.GENAI_TERMS,
                )
                or self._contains_any(
                    description,
                    self.GENAI_TERMS,
                )
            )

            if genai_evidence:
                return (
                    "AI/ML > Generative AI & LLM",
                    self.TITLE_WEIGHT,
                )

            return (
                "AI/ML > Machine Learning",
                self.TITLE_WEIGHT,
            )

        # --------------------------------------------------
        # 4. Weighted scoring
        # --------------------------------------------------

        family_scores: dict[
            str,
            int,
        ] = {}

        for (
            family,
            keywords,
        ) in self.JOB_FAMILY_RULES:

            score = 0

            for keyword in keywords:

                if self._contains_keyword(
                    title,
                    keyword,
                ):
                    score += (
                        self.TITLE_WEIGHT
                    )

                if self._contains_keyword(
                    skills,
                    keyword,
                ):
                    score += (
                        self.SKILL_WEIGHT
                    )

                if self._contains_keyword(
                    description,
                    keyword,
                ):
                    score += (
                        self.DESCRIPTION_WEIGHT
                    )

            family_scores[
                family
            ] = score

        # --------------------------------------------------
        # 5. Explicit GenAI preference
        # --------------------------------------------------

        genai_score = (
            family_scores.get(
                "AI/ML > Generative AI & LLM",
                0,
            )
        )

        ml_score = (
            family_scores.get(
                "AI/ML > Machine Learning",
                0,
            )
        )

        if (
            genai_score
            >= self.MIN_FAMILY_SCORE
            and genai_score >= ml_score
        ):
            return (
                "AI/ML > Generative AI & LLM",
                genai_score,
            )

        # --------------------------------------------------
        # 6. General winner
        # --------------------------------------------------

        best_family = "Other"
        best_score = 0

        for (
            family,
            score,
        ) in family_scores.items():

            if score > best_score:
                best_family = family
                best_score = score

        if (
            best_score
            < self.MIN_FAMILY_SCORE
        ):
            return (
                "Other",
                best_score,
            )

        return (
            best_family,
            best_score,
        )

    # ======================================================
    # Helpers
    # ======================================================

    @staticmethod
    def _normalize_text(
        text: str | None,
    ) -> str:

        if not text:
            return ""

        text = text.lower()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _contains_keyword(
        text: str,
        keyword: str,
    ) -> bool:

        pattern = (
            r"(?<!\w)"
            + re.escape(keyword)
            + r"(?!\w)"
        )

        return (
            re.search(
                pattern,
                text,
            )
            is not None
        )

    @classmethod
    def _contains_any(
        cls,
        text: str,
        keywords: tuple[str, ...],
    ) -> bool:

        return any(
            cls._contains_keyword(
                text,
                keyword,
            )
            for keyword in keywords
        )

    @staticmethod
    def _extract_required_years(
        text: str,
    ) -> int | None:

        patterns = (
            # English
            r"(\d{1,2})\+?\s*years?\s+of\s+experience",
            r"(\d{1,2})\+?\s*years?\s+experience",
            r"minimum\s+of\s+(\d{1,2})\s*years?",
            r"minimum\s+(\d{1,2})\s*years?",
            r"at\s+least\s+(\d{1,2})\s*years?",

            # German
            r"(\d{1,2})\+?\s*jahre?\s+berufserfahrung",
            r"(\d{1,2})\+?\s*jahren?\s+berufserfahrung",
            r"mindestens\s+(\d{1,2})\s+jahre?",
            r"mind\.\s*(\d{1,2})\s+jahre?",
        )

        years: list[int] = []

        for pattern in patterns:

            matches = re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            for match in matches:

                try:
                    years.append(
                        int(match)
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    continue

        return (
            max(years)
            if years
            else None
        )