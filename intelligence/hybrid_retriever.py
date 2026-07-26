from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from rag.retriever import (
    RetrievalResult,
    retrieve_jobs,
)


# ==========================================================
# Hybrid Retrieval Result
# ==========================================================

@dataclass
class HybridRetrievalResult:
    """
    Final retrieval result after semantic retrieval,
    deterministic signal scoring, thresholding,
    deduplication, and reranking.

    hybrid_score is a ranking signal, not a probability.
    """

    job_id: int | None
    title: str
    company: str
    country: str | None
    job_family: str | None
    experience_level: str | None
    remote: bool
    skills: list[str]

    semantic_score: float
    metadata_score: float
    skill_score: float
    hybrid_score: float

    content: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ==========================================================
# Hybrid Retriever
# ==========================================================

class HybridRetriever:
    """
    Reranking layer over semantic job retrieval.

    Semantic retrieval supplies candidate documents.
    Planner-derived filters and recognized skills provide
    deterministic signals used to rerank those candidates.
    """

    VERSION = "hybrid-retriever-v1"

    SEMANTIC_WEIGHT = 0.65
    METADATA_WEIGHT = 0.20
    SKILL_WEIGHT = 0.15

    DEFAULT_CANDIDATE_K = 20
    DEFAULT_FINAL_K = 5

    MIN_SEMANTIC_SCORE = 0.30

    # ======================================================
    # Public API
    # ======================================================

    def search(
        self,
        query: str,
        *,
        filters: dict[str, Any] | None = None,
        skills: list[str] | None = None,
        candidate_k: int = DEFAULT_CANDIDATE_K,
        final_k: int = DEFAULT_FINAL_K,
    ) -> list[HybridRetrievalResult]:

        query = query.strip()

        if not query:
            return []

        if candidate_k < 1 or final_k < 1:
            return []

        normalized_skills = self._normalize_skills(
            skills or []
        )

        candidates = retrieve_jobs(
            query=query,
            k=max(candidate_k, final_k),
            filters=filters,
        )

        ranked: list[HybridRetrievalResult] = []

        for candidate in candidates:

            if (
                candidate.relevance_score
                < self.MIN_SEMANTIC_SCORE
            ):
                continue

            metadata_score = (
                self._metadata_score(
                    candidate=candidate,
                    filters=filters,
                )
            )

            skill_score = (
                self._skill_score(
                    candidate=candidate,
                    requested_skills=normalized_skills,
                )
            )

            hybrid_score = (
                self.SEMANTIC_WEIGHT
                * candidate.relevance_score
                + self.METADATA_WEIGHT
                * metadata_score
                + self.SKILL_WEIGHT
                * skill_score
            )

            ranked.append(
                HybridRetrievalResult(
                    job_id=candidate.job_id,
                    title=candidate.title,
                    company=candidate.company,
                    country=candidate.country,
                    job_family=candidate.job_family,
                    experience_level=(
                        candidate.experience_level
                    ),
                    remote=candidate.remote,
                    skills=candidate.skills,

                    semantic_score=round(
                        candidate.relevance_score,
                        4,
                    ),

                    metadata_score=round(
                        metadata_score,
                        4,
                    ),

                    skill_score=round(
                        skill_score,
                        4,
                    ),

                    hybrid_score=round(
                        hybrid_score,
                        4,
                    ),

                    content=candidate.content,
                    metadata=candidate.metadata,
                )
            )

        ranked.sort(
            key=lambda item: (
                item.hybrid_score,
                item.semantic_score,
            ),
            reverse=True,
        )

        return self._deduplicate(
            ranked
        )[:final_k]


    # ======================================================
    # Metadata Score
    # ======================================================

    @staticmethod
    def _metadata_score(
        candidate: RetrievalResult,
        filters: dict[str, Any] | None,
    ) -> float:
        """
        Score how well the retrieved candidate agrees with
        requested metadata filters.

        Because supported filters are already sent to Chroma,
        this acts as a deterministic consistency signal.
        """

        if not filters:
            return 1.0

        candidate_values = {
            "country": candidate.country,
            "remote": candidate.remote,
            "job_family": candidate.job_family,
            "experience_level": (
                candidate.experience_level
            ),
            "job_type": candidate.metadata.get(
                "job_type"
            ),
            "company": candidate.company,
            "source": candidate.metadata.get(
                "source"
            ),
        }

        matches = 0
        considered = 0

        for key, expected in filters.items():

            if expected is None:
                continue

            if key not in candidate_values:
                continue

            considered += 1

            actual = candidate_values.get(
                key
            )

            if HybridRetriever._values_equal(
                actual,
                expected,
            ):
                matches += 1

        if considered == 0:
            return 1.0

        return matches / considered


    # ======================================================
    # Skill Score
    # ======================================================

    @staticmethod
    def _skill_score(
        candidate: RetrievalResult,
        requested_skills: list[str],
    ) -> float:

        if not requested_skills:
            return 1.0

        candidate_skills = {
            skill.casefold().strip()
            for skill in candidate.skills
            if skill.strip()
        }

        if not candidate_skills:
            return 0.0

        matches = sum(
            1
            for skill in requested_skills
            if skill in candidate_skills
        )

        return (
            matches
            / len(requested_skills)
        )


    # ======================================================
    # Helpers
    # ======================================================

    @staticmethod
    def _normalize_skills(
        skills: list[str],
    ) -> list[str]:

        normalized: list[str] = []
        seen: set[str] = set()

        for skill in skills:

            value = str(
                skill
            ).strip().casefold()

            if not value:
                continue

            if value in seen:
                continue

            seen.add(
                value
            )

            normalized.append(
                value
            )

        return normalized


    @staticmethod
    def _values_equal(
        actual: Any,
        expected: Any,
    ) -> bool:

        if isinstance(expected, bool):
            return actual is expected

        if actual is None:
            return False

        return (
            str(actual)
            .strip()
            .casefold()
            ==
            str(expected)
            .strip()
            .casefold()
        )


    @staticmethod
    def _deduplicate(
        results: list[HybridRetrievalResult],
    ) -> list[HybridRetrievalResult]:

        output: list[
            HybridRetrievalResult
        ] = []

        seen_job_ids: set[int] = set()
        seen_fallback_keys: set[
            tuple[str, str]
        ] = set()

        for result in results:

            if result.job_id is not None:

                if result.job_id in seen_job_ids:
                    continue

                seen_job_ids.add(
                    result.job_id
                )

            else:

                fallback_key = (
                    result.title
                    .strip()
                    .casefold(),

                    result.company
                    .strip()
                    .casefold(),
                )

                if (
                    fallback_key
                    in seen_fallback_keys
                ):
                    continue

                seen_fallback_keys.add(
                    fallback_key
                )

            output.append(
                result
            )

        return output


# ==========================================================
# Convenience Function
# ==========================================================

def hybrid_retrieve_jobs(
    query: str,
    *,
    filters: dict[str, Any] | None = None,
    skills: list[str] | None = None,
    candidate_k: int = 20,
    final_k: int = 5,
) -> list[HybridRetrievalResult]:

    retriever = HybridRetriever()

    return retriever.search(
        query=query,
        filters=filters,
        skills=skills,
        candidate_k=candidate_k,
        final_k=final_k,
    )