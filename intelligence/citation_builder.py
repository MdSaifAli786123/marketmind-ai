from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


# ==========================================================
# Citation
# ==========================================================

@dataclass
class JobCitation:
    """
    Source attribution for one retrieved job posting.
    """

    citation_id: int

    job_id: int | None
    title: str
    company: str

    source: str | None
    source_url: str | None

    country: str | None
    remote: bool

    skills: list[str]

    hybrid_score: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ==========================================================
# Citation Builder
# ==========================================================

class CitationBuilder:

    VERSION = "citation-builder-v1"

    # ======================================================
    # Public API
    # ======================================================

    def build(
        self,
        semantic_evidence: list[dict[str, Any]],
    ) -> list[JobCitation]:

        citations: list[JobCitation] = []

        seen_jobs: set[int] = set()
        seen_urls: set[str] = set()

        for item in semantic_evidence:

            job_id = self._safe_int(
                item.get("job_id")
            )

            source_url = self._extract_source_url(
                item
            )

            # ----------------------------------------------
            # Deduplicate
            # ----------------------------------------------

            if job_id is not None:

                if job_id in seen_jobs:
                    continue

                seen_jobs.add(job_id)

            elif source_url:

                if source_url in seen_urls:
                    continue

                seen_urls.add(source_url)

            # ----------------------------------------------
            # Build citation
            # ----------------------------------------------

            citation = JobCitation(
                citation_id=len(citations) + 1,

                job_id=job_id,

                title=self._safe_string(
                    item.get("title"),
                    default="Unknown job",
                ),

                company=self._safe_string(
                    item.get("company"),
                    default="Unknown company",
                ),

                source=self._extract_source(
                    item
                ),

                source_url=source_url,

                country=self._optional_string(
                    item.get("country")
                ),

                remote=bool(
                    item.get(
                        "remote",
                        False,
                    )
                ),

                skills=self._safe_skills(
                    item.get("skills")
                ),

                hybrid_score=self._safe_float(
                    item.get("hybrid_score")
                ),
            )

            citations.append(citation)

        return citations


    # ======================================================
    # Metadata Extraction
    # ======================================================

    @staticmethod
    def _extract_source(
        item: dict[str, Any],
    ) -> str | None:

        source = item.get("source")

        if source:
            return str(source).strip()

        metadata = item.get("metadata")

        if isinstance(metadata, dict):

            source = metadata.get("source")

            if source:
                return str(source).strip()

        return None


    @staticmethod
    def _extract_source_url(
        item: dict[str, Any],
    ) -> str | None:

        source_url = item.get(
            "source_url"
        )

        if source_url:
            return str(
                source_url
            ).strip()

        metadata = item.get(
            "metadata"
        )

        if isinstance(
            metadata,
            dict,
        ):

            source_url = metadata.get(
                "source_url"
            )

            if source_url:

                return str(
                    source_url
                ).strip()

        return None


    # ======================================================
    # Helpers
    # ======================================================

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int | None:

        if value is None:
            return None

        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):
            return None


    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float | None:

        if value is None:
            return None

        try:
            return round(
                float(value),
                4,
            )

        except (
            TypeError,
            ValueError,
        ):
            return None


    @staticmethod
    def _safe_string(
        value: Any,
        *,
        default: str,
    ) -> str:

        if value is None:
            return default

        cleaned = str(
            value
        ).strip()

        return cleaned or default


    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        cleaned = str(
            value
        ).strip()

        return cleaned or None


    @staticmethod
    def _safe_skills(
        value: Any,
    ) -> list[str]:

        if not value:
            return []

        if isinstance(value, list):

            output: list[str] = []

            seen: set[str] = set()

            for skill in value:

                cleaned = str(
                    skill
                ).strip()

                if not cleaned:
                    continue

                key = cleaned.casefold()

                if key in seen:
                    continue

                seen.add(key)
                output.append(cleaned)

            return output

        return [
            skill.strip()
            for skill in str(value).split(",")
            if skill.strip()
        ]


# ==========================================================
# Convenience Function
# ==========================================================

def build_citations(
    semantic_evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    builder = CitationBuilder()

    return [
        citation.to_dict()
        for citation in builder.build(
            semantic_evidence
        )
    ]