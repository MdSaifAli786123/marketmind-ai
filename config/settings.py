from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# ==========================================================
# Project Paths
# ==========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

ENV_FILE = (
    PROJECT_ROOT
    / ".env"
)


# ==========================================================
# Load Environment
# ==========================================================

load_dotenv(
    dotenv_path=ENV_FILE
)


# ==========================================================
# Settings
# ==========================================================

class Settings:
    """
    Central application configuration.

    Environment-specific values are loaded from environment
    variables and the project's .env file.

    Non-secret application defaults are defined here.
    """

    # ======================================================
    # Application
    # ======================================================

    app_name: str = (
        "AI Job Market Intelligence API"
    )

    app_version: str = "1.2.0"

    environment: str = "development"


    # ======================================================
    # Database
    # ======================================================

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str


    # ======================================================
    # LLM
    # ======================================================

    groq_api_key: str | None

    llm_model: str = (
        "llama-3.3-70b-versatile"
    )

    llm_temperature: float = 0.1


    # ======================================================
    # RAG
    # ======================================================

    embedding_model: str = (
        "sentence-transformers/"
        "all-MiniLM-L6-v2"
    )

    vector_collection: str = (
        "job_market"
    )

    vector_store_dir: Path = (
        PROJECT_ROOT
        / "data"
        / "vector_store"
    )

    rag_k: int = 5


    # ======================================================
    # Logging
    # ======================================================

    log_level: str = "INFO"


    # ======================================================
    # Pipeline
    # ======================================================

    request_timeout: int = 30

    max_ai_records: int = 100


    # ======================================================
    # CORS
    # ======================================================

    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    )


    # ======================================================
    # Initialization
    # ======================================================

    def __init__(self) -> None:

        # ==================================================
        # Application
        # ==================================================

        self.environment = os.getenv(
            "APP_ENV",
            os.getenv(
                "ENVIRONMENT",
                self.environment,
            ),
        )

        self.app_name = os.getenv(
            "APP_NAME",
            self.app_name,
        )

        self.app_version = os.getenv(
            "APP_VERSION",
            self.app_version,
        )


        # ==================================================
        # Database
        # ==================================================

        self.db_host = os.getenv(
            "DB_HOST",
            "localhost",
        )

        self.db_port = self._get_int(
            "DB_PORT",
            5432,
        )

        self.db_name = os.getenv(
            "DB_NAME",
            "ai_job_market",
        )

        self.db_user = os.getenv(
            "DB_USER",
            "postgres",
        )

        self.db_password = os.getenv(
            "DB_PASSWORD",
            "",
        )


        # ==================================================
        # LLM
        # ==================================================

        self.groq_api_key = os.getenv(
            "GROQ_API_KEY"
        )

        self.llm_model = os.getenv(
            "LLM_MODEL",
            self.llm_model,
        )

        self.llm_temperature = (
            self._get_float(
                "LLM_TEMPERATURE",
                self.llm_temperature,
            )
        )


        # ==================================================
        # RAG
        # ==================================================

        self.embedding_model = os.getenv(
            "EMBEDDING_MODEL",
            self.embedding_model,
        )

        self.vector_collection = os.getenv(
            "VECTOR_COLLECTION",
            self.vector_collection,
        )

        vector_directory = os.getenv(
            "VECTOR_STORE_DIR"
        )

        if vector_directory:

            path = Path(
                vector_directory
            )

            if not path.is_absolute():

                path = (
                    PROJECT_ROOT
                    / path
                )

            self.vector_store_dir = (
                path.resolve()
            )

        self.rag_k = self._get_int(
            "RAG_K",
            self.rag_k,
        )


        # ==================================================
        # Logging
        # ==================================================

        self.log_level = os.getenv(
            "LOG_LEVEL",
            self.log_level,
        ).strip().upper()

        if self.log_level not in {
            "CRITICAL",
            "ERROR",
            "WARNING",
            "INFO",
            "DEBUG",
            "NOTSET",
        }:

            raise RuntimeError(
                "LOG_LEVEL must be one of: "
                "CRITICAL, ERROR, WARNING, "
                "INFO, DEBUG, NOTSET."
            )


        # ==================================================
        # Pipeline
        # ==================================================

        self.request_timeout = (
            self._get_int(
                "REQUEST_TIMEOUT",
                self.request_timeout,
            )
        )

        self.max_ai_records = (
            self._get_int(
                "MAX_AI_RECORDS",
                self.max_ai_records,
            )
        )


        # ==================================================
        # CORS
        # ==================================================

        cors_value = os.getenv(
            "CORS_ORIGINS"
        )

        if cors_value:

            self.cors_origins = tuple(
                origin.strip()
                for origin
                in cors_value.split(",")
                if origin.strip()
            )


    # ======================================================
    # Helpers
    # ======================================================

    @staticmethod
    def _get_int(
        name: str,
        default: int,
    ) -> int:

        value = os.getenv(
            name
        )

        if value is None:
            return default

        try:

            return int(
                value
            )

        except ValueError as exc:

            raise RuntimeError(
                f"{name} must be an integer."
            ) from exc


    @staticmethod
    def _get_float(
        name: str,
        default: float,
    ) -> float:

        value = os.getenv(
            name
        )

        if value is None:
            return default

        try:

            return float(
                value
            )

        except ValueError as exc:

            raise RuntimeError(
                f"{name} must be a number."
            ) from exc


# ==========================================================
# Singleton
# ==========================================================

settings = Settings()