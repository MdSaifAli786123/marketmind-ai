from __future__ import annotations

import re


class SkillNormalizer:
    """
    Normalize and validate job-market skills.

    Skill Taxonomy v2
    -----------------
    Goals:
    - Convert aliases to canonical names.
    - Keep useful technical/professional skills.
    - Remove job metadata, seniority, employment type,
      generic roles, and RemoteOK-style category tags.
    """

    VERSION = "skills-v2"

    # ==========================================================
    # Canonical aliases
    # ==========================================================

    ALIASES: dict[str, str] = {

        # ------------------------------------------------------
        # AI / ML
        # ------------------------------------------------------

        "ai": "artificial intelligence",
        "artificial intelligence": "artificial intelligence",

        "ml": "machine learning",
        "machine-learning": "machine learning",
        "machine learning": "machine learning",

        "dl": "deep learning",
        "deep-learning": "deep learning",
        "deep learning": "deep learning",

        "genai": "generative ai",
        "gen ai": "generative ai",
        "generative ai": "generative ai",

        "llm": "large language models",
        "llms": "large language models",
        "large language model": "large language models",
        "large language models": "large language models",

        "nlp": "natural language processing",
        "natural language processing": "natural language processing",

        "cv": "computer vision",
        "computer vision": "computer vision",

        "reinforcement learning": "reinforcement learning",
        "rl": "reinforcement learning",

        # ------------------------------------------------------
        # Programming languages
        # ------------------------------------------------------

        "py": "python",
        "python": "python",

        "js": "javascript",
        "javascript": "javascript",

        "ts": "typescript",
        "typescript": "typescript",

        "golang": "go",
        "go lang": "go",
        "go": "go",

        "java": "java",

        "c++": "c++",
        "cpp": "c++",

        "c#": "c#",
        "c sharp": "c#",

        "ruby": "ruby",
        "php": "php",
        "rust": "rust",
        "kotlin": "kotlin",
        "swift": "swift",
        "scala": "scala",

        "r programming": "r",
        "r language": "r",

        # ------------------------------------------------------
        # Web / Backend
        # ------------------------------------------------------

        "react.js": "react",
        "reactjs": "react",
        "react": "react",

        "next.js": "next.js",
        "nextjs": "next.js",

        "vue.js": "vue",
        "vuejs": "vue",
        "vue": "vue",

        "angular": "angular",

        "node.js": "node.js",
        "nodejs": "node.js",

        "express.js": "express",
        "expressjs": "express",
        "express": "express",

        "fastapi": "fastapi",
        "fast api": "fastapi",

        "django": "django",
        "flask": "flask",

        "spring boot": "spring boot",
        "springboot": "spring boot",

        ".net": ".net",
        "dotnet": ".net",

        "html": "html",
        "html5": "html",

        "css": "css",
        "css3": "css",

        # ------------------------------------------------------
        # Databases / data systems
        # ------------------------------------------------------

        "sql": "sql",

        "postgres": "postgresql",
        "postgresql": "postgresql",

        "mysql": "mysql",

        "mongo": "mongodb",
        "mongodb": "mongodb",

        "redis": "redis",

        "sqlite": "sqlite",

        "elasticsearch": "elasticsearch",
        "elastic search": "elasticsearch",

        "snowflake": "snowflake",

        "bigquery": "bigquery",
        "google bigquery": "bigquery",

        # ------------------------------------------------------
        # Data engineering
        # ------------------------------------------------------

        "apache spark": "spark",
        "spark": "spark",

        "apache kafka": "kafka",
        "kafka": "kafka",

        "apache airflow": "airflow",
        "airflow": "airflow",

        "dbt": "dbt",

        "etl": "etl",

        # ------------------------------------------------------
        # ML libraries
        # ------------------------------------------------------

        "pytorch": "pytorch",
        "py torch": "pytorch",

        "tensorflow": "tensorflow",
        "tensor flow": "tensorflow",

        "sklearn": "scikit-learn",
        "scikit learn": "scikit-learn",
        "scikit-learn": "scikit-learn",

        "keras": "keras",

        "xgboost": "xgboost",

        "opencv": "opencv",
        "open cv": "opencv",

        "pandas": "pandas",
        "numpy": "numpy",

        # ------------------------------------------------------
        # LLM ecosystem
        # ------------------------------------------------------

        "lang chain": "langchain",
        "langchain": "langchain",

        "huggingface": "hugging face",
        "hugging face": "hugging face",

        "transformers": "transformers",

        "rag": "retrieval augmented generation",
        "retrieval-augmented generation":
            "retrieval augmented generation",
        "retrieval augmented generation":
            "retrieval augmented generation",

        # ------------------------------------------------------
        # Cloud
        # ------------------------------------------------------

        "aws": "aws",
        "amazon web services": "aws",

        "azure": "azure",
        "microsoft azure": "azure",

        "gcp": "google cloud",
        "google cloud platform": "google cloud",
        "google cloud": "google cloud",

        # ------------------------------------------------------
        # DevOps
        # ------------------------------------------------------

        "docker": "docker",

        "k8s": "kubernetes",
        "kubernetes": "kubernetes",

        "terraform": "terraform",

        "ansible": "ansible",

        "jenkins": "jenkins",

        "github actions": "github actions",

        "gitlab ci": "gitlab ci",

        "ci/cd": "ci/cd",
        "cicd": "ci/cd",

        # ------------------------------------------------------
        # Development tools / platforms
        # ------------------------------------------------------

        "git": "git",
        "github": "github",
        "gitlab": "gitlab",

        "linux": "linux",

        "unix": "unix",

        # ------------------------------------------------------
        # APIs / architecture
        # ------------------------------------------------------

        "rest": "rest api",
        "rest api": "rest api",
        "restful api": "rest api",

        "graphql": "graphql",

        "microservices": "microservices",
        "microservice": "microservices",

        # ------------------------------------------------------
        # Testing
        # ------------------------------------------------------

        "pytest": "pytest",
        "selenium": "selenium",
        "cypress": "cypress",
        "jest": "jest",

        # ------------------------------------------------------
        # Security
        # ------------------------------------------------------

        "cybersecurity": "cybersecurity",
        "cyber security": "cybersecurity",

        "information security": "information security",

        "penetration testing": "penetration testing",
        "pentesting": "penetration testing",

        "oauth": "oauth",

        # ------------------------------------------------------
        # Infrastructure / administration
        # ------------------------------------------------------

        "system and network administration":
            "system and network administration",

        "system administration":
            "system administration",

        "network administration":
            "network administration",

        # ------------------------------------------------------
        # Useful methodologies / technical practices
        # ------------------------------------------------------

        "agile": "agile",
        "scrum": "scrum",

        "devops": "devops",
        "mlops": "mlops",

        "data visualization": "data visualization",
    }

    # ==========================================================
    # Values that must NEVER become skills
    # ==========================================================

    BLOCKLIST: set[str] = {

        # Work arrangement
        "remote",
        "remote work",
        "work from home",
        "digital nomad",
        "onsite",
        "on-site",
        "hybrid",

        # Employment type
        "full time",
        "full-time",
        "part time",
        "part-time",
        "contract",
        "contractor",
        "freelance",
        "internship",

        # Seniority
        "junior",
        "senior",
        "entry level",
        "entry-level",
        "mid level",
        "mid-level",
        "executive",
        "exec",

        # Generic roles
        "engineer",
        "engineering",
        "developer",
        "dev",
        "chief executives",
        "directors",

        # Generic categories / industries
        "finance",
        "medical",
        "education",
        "hr",
        "human resources",
        "marketing",
        "marketing and communication",
        "customer support",

        # Broad/non-specific labels
        "technical",
        "operations",
        "ops",
        "management",
        "business",
        "sales",

        # Education metadata
        "associate's degree",
        "bachelor's degree",
        "master's degree",
        "degree",
    }

    # ==========================================================
    # Normalization
    # ==========================================================

    @classmethod
    def normalize(
        cls,
        skill: str,
    ) -> str:

        if not skill:
            return ""

        value = str(skill).strip().lower()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        value = value.strip(
            " ,;|"
        )

        return cls.ALIASES.get(
            value,
            value,
        )

    # ==========================================================
    # Validation
    # ==========================================================

    @classmethod
    def is_valid_skill(
        cls,
        skill: str,
    ) -> bool:
        """
        Return True only for skills explicitly represented
        in the technical taxonomy.

        Unknown API tags are intentionally rejected rather
        than automatically inserted into the skills table.
        """

        value = cls.normalize(skill)

        if not value:
            return False

        if value in cls.BLOCKLIST:
            return False

        # Canonical values form the accepted taxonomy.
        valid_skills = set(
            cls.ALIASES.values()
        )

        return value in valid_skills

    # ==========================================================
    # Normalize collection
    # ==========================================================

    @classmethod
    def normalize_many(
        cls,
        skills: list[str],
    ) -> list[str]:

        normalized: list[str] = []
        seen: set[str] = set()

        for skill in skills:

            value = cls.normalize(
                skill
            )

            if not cls.is_valid_skill(
                value
            ):
                continue

            if value in seen:
                continue

            seen.add(value)

            normalized.append(
                value
            )

        return normalized