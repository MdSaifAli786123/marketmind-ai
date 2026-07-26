from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document

from rag.vector_store import get_vector_store


# ==========================================================
# Retrieval Result
# ==========================================================

@dataclass
class RetrievalResult:
    """
    One semantically retrieved job document.
    """

    job_id: int | None
    title: str
    company: str
    country: str | None
    job_family: str | None
    experience_level: str | None
    remote: bool
    skills: list[str]

    distance: float
    relevance_score: float

    content: str
    metadata: dict[str, Any]


# ==========================================================
# Retriever
# ==========================================================

class JobRetriever:
    """
    Semantic retrieval interface over the persistent
    job-market Chroma vector store.
    """

    def __init__(self) -> None:

        self.vector_store = (
            get_vector_store()
        )


    # ======================================================
    # Helpers
    # ======================================================

    @staticmethod
    def _parse_skills(
        value: Any,
    ) -> list[str]:

        if not value:
            return []

        if isinstance(value, list):
            return [
                str(skill).strip()
                for skill in value
                if str(skill).strip()
            ]

        return [
            skill.strip()
            for skill in str(value).split(",")
            if skill.strip()
        ]


    @staticmethod
    def _distance_to_relevance(
        distance: float,
    ) -> float:
        """
        Convert Chroma distance into a simple bounded
        relevance value.

        This is useful for ranking/display but should not be
        interpreted as a calibrated probability.
        """

        return round(
            1.0 / (1.0 + max(distance, 0.0)),
            4,
        )


    @staticmethod
    def _build_filter(
        filters: dict[str, Any] | None,
    ) -> dict[str, Any] | None:

        if not filters:
            return None

        allowed_fields = {
            "country",
            "remote",
            "job_family",
            "experience_level",
            "job_type",
            "company",
            "source",
        }

        cleaned = {
            key: value
            for key, value in filters.items()
            if (
                key in allowed_fields
                and value is not None
            )
        }

        if not cleaned:
            return None

        # Chroma requires explicit logical composition
        # when multiple metadata conditions are supplied.
        if len(cleaned) == 1:
            key, value = next(
                iter(cleaned.items())
            )

            return {
                key: {
                    "$eq": value,
                }
            }

        return {
            "$and": [
                {
                    key: {
                        "$eq": value,
                    }
                }
                for key, value
                in cleaned.items()
            ]
        }


    @staticmethod
    def _to_result(
        document: Document,
        distance: float,
    ) -> RetrievalResult:

        metadata = dict(
            document.metadata
        )

        raw_job_id = metadata.get(
            "job_id"
        )

        try:
            job_id = (
                int(raw_job_id)
                if raw_job_id is not None
                else None
            )
        except (
            TypeError,
            ValueError,
        ):
            job_id = None

        return RetrievalResult(
            job_id=job_id,

            title=str(
                metadata.get(
                    "title",
                    "Unknown",
                )
            ),

            company=str(
                metadata.get(
                    "company",
                    "Unknown",
                )
            ),

            country=metadata.get(
                "country"
            ),

            job_family=metadata.get(
                "job_family"
            ),

            experience_level=(
                metadata.get(
                    "experience_level"
                )
            ),

            remote=bool(
                metadata.get(
                    "remote",
                    False,
                )
            ),

            skills=(
                JobRetriever._parse_skills(
                    metadata.get(
                        "skills"
                    )
                )
            ),

            distance=round(
                float(distance),
                4,
            ),

            relevance_score=(
                JobRetriever
                ._distance_to_relevance(
                    float(distance)
                )
            ),

            content=document.page_content,

            metadata=metadata,
        )


    # ======================================================
    # Semantic Search
    # ======================================================

    def search(
        self,
        query: str,
        k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:

        query = query.strip()

        if not query:
            return []

        if k < 1:
            return []

        chroma_filter = (
            self._build_filter(
                filters
            )
        )

        results = (
            self.vector_store
            .similarity_search_with_score(
                query=query,
                k=k,
                filter=chroma_filter,
            )
        )

        retrieval_results: list[
            RetrievalResult
        ] = []

        seen_job_ids: set[int] = set()

        for document, distance in results:

            result = self._to_result(
                document,
                distance,
            )

            # Prevent duplicate job postings from appearing
            # more than once when job_id is available.
            if result.job_id is not None:

                if (
                    result.job_id
                    in seen_job_ids
                ):
                    continue

                seen_job_ids.add(
                    result.job_id
                )

            retrieval_results.append(
                result
            )

        return retrieval_results


# ==========================================================
# Convenience Function
# ==========================================================

def retrieve_jobs(
    query: str,
    k: int = 5,
    filters: dict[str, Any] | None = None,
) -> list[RetrievalResult]:

    retriever = JobRetriever()

    return retriever.search(
        query=query,
        k=k,
        filters=filters,
    )


# ==========================================================
# Development Test
# ==========================================================

if __name__ == "__main__":

    query = (
        "machine learning engineer "
        "with Python cloud Docker AWS"
    )

    print(
        f"\nQuery: {query}\n"
    )

    results = retrieve_jobs(
        query=query,
        k=5,
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            "=" * 70
        )

        print(
            f"RESULT {index}"
        )

        print(
            "=" * 70
        )

        print(
            f"Job ID     : {result.job_id}"
        )

        print(
            f"Title      : {result.title}"
        )

        print(
            f"Company    : {result.company}"
        )

        print(
            f"Country    : {result.country}"
        )

        print(
            f"Job Family : {result.job_family}"
        )

        print(
            f"Experience : "
            f"{result.experience_level}"
        )

        print(
            f"Remote     : {result.remote}"
        )

        print(
            f"Skills     : "
            f"{', '.join(result.skills)}"
        )

        print(
            f"Distance   : "
            f"{result.distance}"
        )

        print(
            f"Relevance  : "
            f"{result.relevance_score}"
        )

        print()