from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from intelligence.hybrid_retriever import (
    HybridRetrievalResult,
    HybridRetriever,
    hybrid_retrieve_jobs,
)
from intelligence.query_engine import QueryEngine
from intelligence.query_planner import (
    QueryPlan,
    QueryPlanner,
)


# ==========================================================
# Grounded Context
# ==========================================================

@dataclass
class GroundedContext:
    """
    Complete evidence package prepared for the LLM.

    Contains:
    1. Original user question
    2. Deterministic query plan
    3. Exact structured database evidence
    4. Hybrid semantic retrieval evidence
    5. LLM-ready grounded context
    """

    question: str

    plan: dict[str, Any]

    structured_evidence: dict[str, Any]

    semantic_evidence: list[dict[str, Any]]

    context_text: str

    retrieval_version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ==========================================================
# Context Builder
# ==========================================================

class ContextBuilder:

    VERSION = "context-builder-v3"

    DEFAULT_RAG_K = 5
    DEFAULT_CANDIDATE_K = 20

    def __init__(self) -> None:

        self.planner = QueryPlanner()

        self.engine = QueryEngine()


    # ======================================================
    # Public API
    # ======================================================

    def build(
        self,
        question: str,
        rag_k: int = DEFAULT_RAG_K,
    ) -> GroundedContext:

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        if rag_k < 1:
            raise ValueError(
                "rag_k must be at least 1."
            )

        # --------------------------------------------------
        # 1. Natural language -> deterministic query plan
        # --------------------------------------------------

        plan = self.planner.plan(
            question
        )

        # --------------------------------------------------
        # 2. Query plan -> exact database evidence
        # --------------------------------------------------

        structured_evidence = (
            self.engine.execute(
                plan
            )
        )

        # --------------------------------------------------
        # 3. Planner filters -> Chroma metadata filters
        # --------------------------------------------------

        rag_filters = (
            self._build_rag_filters(
                plan
            )
        )

        # --------------------------------------------------
        # 4. Hybrid retrieval
        #
        # Candidate generation:
        #     SentenceTransformer embeddings + Chroma
        #
        # Reranking:
        #     semantic relevance
        #     + metadata consistency
        #     + requested skill overlap
        # --------------------------------------------------

        retrieval_results = (
            hybrid_retrieve_jobs(
                query=question,
                filters=rag_filters,
                skills=plan.skills,
                candidate_k=max(
                    self.DEFAULT_CANDIDATE_K,
                    rag_k * 4,
                ),
                final_k=rag_k,
            )
        )

        # --------------------------------------------------
        # 5. Serialize retrieved evidence
        #
        # Preserve source/source_url and metadata because
        # downstream citation/source attribution requires
        # these fields.
        # --------------------------------------------------

        semantic_evidence = [
            self._serialize_retrieval_result(
                result
            )
            for result in retrieval_results
        ]

        # --------------------------------------------------
        # 6. Build grounded LLM context
        # --------------------------------------------------

        context_text = (
            self._build_context_text(
                question=question,
                plan=plan,
                structured_evidence=(
                    structured_evidence
                ),
                semantic_evidence=(
                    semantic_evidence
                ),
            )
        )

        # --------------------------------------------------
        # 7. Complete evidence package
        # --------------------------------------------------

        return GroundedContext(
            question=question,

            plan=plan.to_dict(),

            structured_evidence=(
                structured_evidence
            ),

            semantic_evidence=(
                semantic_evidence
            ),

            context_text=context_text,

            retrieval_version=(
                HybridRetriever.VERSION
            ),
        )


    # ======================================================
    # RAG Filter Builder
    # ======================================================

    @staticmethod
    def _build_rag_filters(
        plan: QueryPlan,
    ) -> dict[str, Any] | None:
        """
        Convert planner filters into metadata filters
        supported by the Chroma job collection.

        Skills are intentionally excluded here.

        Skills are stored as document metadata and are used
        by HybridRetriever as a reranking signal instead of
        an exact Chroma metadata filter.
        """

        supported_fields = {
            "country",
            "remote",
            "job_family",
            "experience_level",
            "job_type",
            "company",
            "source",
        }

        filters = {
            key: value
            for key, value
            in plan.filters.items()
            if (
                key in supported_fields
                and value is not None
            )
        }

        return filters or None


    # ======================================================
    # Hybrid Retrieval Serialization
    # ======================================================

    @staticmethod
    def _serialize_retrieval_result(
        result: HybridRetrievalResult,
    ) -> dict[str, Any]:
        """
        Convert one HybridRetrievalResult into a JSON-safe
        dictionary used by:

        - ContextBuilder
        - LLM grounding
        - API responses
        - CitationBuilder
        - frontend evidence display
        """

        metadata = dict(
            result.metadata or {}
        )

        return {
            # ----------------------------------------------
            # Job identity
            # ----------------------------------------------

            "job_id": result.job_id,

            "title": result.title,

            "company": result.company,

            # ----------------------------------------------
            # Job attributes
            # ----------------------------------------------

            "country": result.country,

            "job_family": (
                result.job_family
            ),

            "experience_level": (
                result.experience_level
            ),

            "remote": result.remote,

            "skills": list(
                result.skills
            ),

            # ----------------------------------------------
            # Source attribution
            #
            # Required by CitationBuilder.
            # ----------------------------------------------

            "source": metadata.get(
                "source"
            ),

            "source_url": metadata.get(
                "source_url"
            ),

            # ----------------------------------------------
            # Retrieval diagnostics
            #
            # These are ranking signals, NOT probabilities.
            # ----------------------------------------------

            "semantic_score": (
                result.semantic_score
            ),

            "metadata_score": (
                result.metadata_score
            ),

            "skill_score": (
                result.skill_score
            ),

            "hybrid_score": (
                result.hybrid_score
            ),

            # ----------------------------------------------
            # Retrieved document
            # ----------------------------------------------

            "content": result.content,

            # ----------------------------------------------
            # Original vector-document metadata
            #
            # Preserved for citations and future retrieval
            # features.
            # ----------------------------------------------

            "metadata": metadata,
        }


    # ======================================================
    # Context Formatting
    # ======================================================

    def _build_context_text(
        self,
        question: str,
        plan: QueryPlan,
        structured_evidence: dict[str, Any],
        semantic_evidence: list[
            dict[str, Any]
        ],
    ) -> str:

        sections: list[str] = []

        # --------------------------------------------------
        # User Question
        # --------------------------------------------------

        sections.append(
            "USER QUESTION\n"
            f"{question}"
        )

        # --------------------------------------------------
        # Query Plan
        # --------------------------------------------------

        sections.append(
            self._format_plan(
                plan
            )
        )

        # --------------------------------------------------
        # Structured Evidence
        # --------------------------------------------------

        sections.append(
            self._format_structured_evidence(
                structured_evidence
            )
        )

        # --------------------------------------------------
        # Hybrid Retrieval Evidence
        # --------------------------------------------------

        sections.append(
            self._format_semantic_evidence(
                semantic_evidence
            )
        )

        # --------------------------------------------------
        # Grounding Rules
        # --------------------------------------------------

        sections.append(
            (
                "GROUNDING RULES\n"

                "- Answer only from the supplied evidence.\n"

                "- Use structured database evidence as the "
                "authoritative source for exact counts, "
                "percentages, rankings, distributions, "
                "comparisons, and aggregate statistics.\n"

                "- Use retrieved job documents for "
                "qualitative details, examples, "
                "responsibilities, requirements, and "
                "context from individual postings.\n"

                "- Retrieved job numbers such as [1], [2], "
                "and [3] identify source documents and may "
                "be used when referring to specific job "
                "postings.\n"

                "- Do not convert retrieval scores into "
                "factual confidence percentages.\n"

                "- Semantic score, metadata score, skill "
                "score, and hybrid score are ranking "
                "diagnostics only.\n"

                "- Do not invent jobs, companies, skills, "
                "requirements, locations, salaries, "
                "statistics, URLs, or trends.\n"

                "- If structured evidence and retrieved "
                "documents appear inconsistent, prefer "
                "structured evidence for quantitative "
                "claims.\n"

                "- If no evidence supports the requested "
                "claim, explicitly state that the current "
                "dataset does not provide sufficient "
                "evidence."
            )
        )

        return "\n\n".join(
            sections
        )


    # ======================================================
    # Plan Formatting
    # ======================================================

    @staticmethod
    def _format_plan(
        plan: QueryPlan,
    ) -> str:

        lines = [
            "QUERY PLAN",

            f"Intent: {plan.intent}",

            (
                "Planner confidence: "
                f"{plan.confidence}"
            ),

            f"Limit: {plan.limit}",
        ]

        # --------------------------------------------------
        # Filters
        # --------------------------------------------------

        if plan.filters:

            lines.append(
                "Filters:"
            )

            for key, value in (
                plan.filters.items()
            ):

                lines.append(
                    f"- {key}: {value}"
                )

        else:

            lines.append(
                "Filters: none"
            )

        # --------------------------------------------------
        # Skills
        # --------------------------------------------------

        if plan.skills:

            lines.append(
                "Recognized skills: "
                + ", ".join(
                    plan.skills
                )
            )

        else:

            lines.append(
                "Recognized skills: none"
            )

        return "\n".join(
            lines
        )


    # ======================================================
    # Structured Evidence Formatting
    # ======================================================

    @staticmethod
    def _format_structured_evidence(
        evidence: dict[str, Any],
    ) -> str:

        lines = [
            "STRUCTURED DATABASE EVIDENCE",

            (
                "Intent: "
                f"{evidence.get('intent')}"
            ),
        ]

        # --------------------------------------------------
        # Counts
        # --------------------------------------------------

        if (
            "total_matching_jobs"
            in evidence
        ):

            lines.append(
                "Total matching jobs: "
                f"{evidence.get('total_matching_jobs')}"
            )

        if (
            "returned_jobs"
            in evidence
        ):

            lines.append(
                "Returned jobs: "
                f"{evidence.get('returned_jobs')}"
            )

        # --------------------------------------------------
        # Data
        # --------------------------------------------------

        data = evidence.get(
            "data"
        )

        if isinstance(
            data,
            dict,
        ):

            if not data:

                lines.append(
                    "No structured results."
                )

            else:

                for key, value in (
                    data.items()
                ):

                    lines.append(
                        f"- {key}: {value}"
                    )

        elif isinstance(
            data,
            list,
        ):

            if not data:

                lines.append(
                    "No structured results."
                )

            else:

                for index, item in enumerate(
                    data,
                    start=1,
                ):

                    lines.append(
                        f"{index}. {item}"
                    )

        elif data is not None:

            lines.append(
                f"Data: {data}"
            )

        # --------------------------------------------------
        # Message
        # --------------------------------------------------

        message = evidence.get(
            "message"
        )

        if message:

            lines.append(
                f"Message: {message}"
            )

        return "\n".join(
            lines
        )


    # ======================================================
    # Hybrid Semantic Evidence Formatting
    # ======================================================

    @staticmethod
    def _format_semantic_evidence(
        evidence: list[
            dict[str, Any]
        ],
    ) -> str:

        lines = [
            "HYBRID RETRIEVAL EVIDENCE"
        ]

        if not evidence:

            lines.append(
                "No relevant job documents "
                "were retrieved."
            )

            return "\n".join(
                lines
            )

        for index, item in enumerate(
            evidence,
            start=1,
        ):

            lines.extend(
                [
                    "",

                    (
                        f"Retrieved Job [{index}]"
                    ),

                    (
                        "Job ID: "
                        f"{item.get('job_id')}"
                    ),

                    (
                        "Title: "
                        f"{item.get('title')}"
                    ),

                    (
                        "Company: "
                        f"{item.get('company')}"
                    ),

                    (
                        "Country: "
                        f"{item.get('country')}"
                    ),

                    (
                        "Job Family: "
                        f"{item.get('job_family')}"
                    ),

                    (
                        "Experience Level: "
                        f"{item.get('experience_level')}"
                    ),

                    (
                        "Remote: "
                        f"{item.get('remote')}"
                    ),

                    (
                        "Skills: "
                        + (
                            ", ".join(
                                item.get(
                                    "skills",
                                    [],
                                )
                            )
                            or "None"
                        )
                    ),

                    # --------------------------------------
                    # Source attribution
                    # --------------------------------------

                    (
                        "Source: "
                        f"{item.get('source') or 'Unknown'}"
                    ),

                    (
                        "Source URL: "
                        f"{item.get('source_url') or 'Unavailable'}"
                    ),

                    # --------------------------------------
                    # Ranking diagnostics
                    # --------------------------------------

                    (
                        "Semantic Score: "
                        f"{item.get('semantic_score')}"
                    ),

                    (
                        "Metadata Score: "
                        f"{item.get('metadata_score')}"
                    ),

                    (
                        "Skill Score: "
                        f"{item.get('skill_score')}"
                    ),

                    (
                        "Hybrid Score: "
                        f"{item.get('hybrid_score')}"
                    ),

                    # --------------------------------------
                    # Retrieved document
                    # --------------------------------------

                    "Document:",

                    str(
                        item.get(
                            "content",
                            "",
                        )
                    ),
                ]
            )

        return "\n".join(
            lines
        )


# ==========================================================
# Convenience Function
# ==========================================================

def build_grounded_context(
    question: str,
    rag_k: int = 5,
) -> GroundedContext:

    builder = ContextBuilder()

    return builder.build(
        question=question,
        rag_k=rag_k,
    )


# ==========================================================
# Development Entry Point
# ==========================================================

if __name__ == "__main__":

    question = (
        "What are the top skills for "
        "remote software engineering jobs?"
    )

    context = (
        build_grounded_context(
            question=question,
            rag_k=5,
        )
    )

    print(
        "\n"
        + "=" * 80
    )

    print(
        "GROUNDED HYBRID CONTEXT"
    )

    print(
        "=" * 80
        + "\n"
    )

    print(
        context.context_text
    )