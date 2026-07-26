from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from intelligence.citation_builder import (
    CitationBuilder,
)
from intelligence.context_builder import (
    GroundedContext,
)


# ==========================================================
# Synthesized Response
# ==========================================================

@dataclass
class SynthesizedResponse:
    """
    Stable internal representation of one completed
    intelligence request.

    Combines:
    - generated answer
    - query-plan metadata
    - structured database evidence
    - hybrid RAG evidence
    - source citations
    - pipeline/version metadata
    """

    question: str
    answer: str

    intent: str
    planner_confidence: float

    filters: dict[str, Any]
    skills: list[str]

    structured_evidence: dict[str, Any]
    semantic_evidence: list[dict[str, Any]]

    citations: list[dict[str, Any]]

    response_mode: str
    llm_model: str | None

    evidence_scope: int
    retrieval_count: int
    citation_count: int

    planner_version: str
    engine_version: str
    context_version: str
    retrieval_version: str
    generator_version: str
    citation_version: str
    synthesizer_version: str

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return asdict(self)


# ==========================================================
# Response Synthesizer
# ==========================================================

class ResponseSynthesizer:
    """
    Converts the completed intelligence pipeline output into
    a stable response structure.

    This layer does not perform retrieval or generation.

    It combines:

        GroundedContext
            +
        Generated Answer
            +
        Citations
            +
        Pipeline Metadata

    into one response object.
    """

    VERSION = "response-synthesizer-v2"

    def __init__(
        self,
    ) -> None:

        self.citation_builder = (
            CitationBuilder()
        )


    # ======================================================
    # Public API
    # ======================================================

    def synthesize(
        self,
        *,
        context: GroundedContext,
        answer: str,
        response_mode: str,
        llm_model: str | None,
        planner_version: str,
        engine_version: str,
        generator_version: str,
    ) -> SynthesizedResponse:

        # --------------------------------------------------
        # Answer
        # --------------------------------------------------

        cleaned_answer = (
            str(answer).strip()
            if answer is not None
            else ""
        )

        if not cleaned_answer:

            cleaned_answer = (
                "The current dataset does not provide "
                "enough evidence to answer this question."
            )

        # --------------------------------------------------
        # Context components
        # --------------------------------------------------

        plan = (
            context.plan
            or {}
        )

        structured = (
            context.structured_evidence
            or {}
        )

        semantic = (
            context.semantic_evidence
            or []
        )

        # --------------------------------------------------
        # Citation generation
        #
        # Citations are derived only from retrieved
        # documents. CitationBuilder does not invent
        # sources.
        # --------------------------------------------------

        citation_objects = (
            self.citation_builder.build(
                semantic
            )
        )

        citations = [
            citation.to_dict()
            for citation
            in citation_objects
        ]

        # --------------------------------------------------
        # Build response
        # --------------------------------------------------

        return SynthesizedResponse(

            # ----------------------------------------------
            # Question + answer
            # ----------------------------------------------

            question=(
                context.question
            ),

            answer=(
                cleaned_answer
            ),

            # ----------------------------------------------
            # Planner information
            # ----------------------------------------------

            intent=str(
                plan.get(
                    "intent",
                    "unknown",
                )
            ),

            planner_confidence=(
                self._safe_float(
                    plan.get(
                        "confidence",
                        0.0,
                    )
                )
            ),

            filters=(
                self._safe_dict(
                    plan.get(
                        "filters"
                    )
                )
            ),

            skills=(
                self._safe_list(
                    plan.get(
                        "skills"
                    )
                )
            ),

            # ----------------------------------------------
            # Evidence
            # ----------------------------------------------

            structured_evidence=(
                structured
            ),

            semantic_evidence=(
                semantic
            ),

            citations=(
                citations
            ),

            # ----------------------------------------------
            # Generation metadata
            # ----------------------------------------------

            response_mode=(
                response_mode
            ),

            llm_model=(
                llm_model
            ),

            # ----------------------------------------------
            # Evidence diagnostics
            # ----------------------------------------------

            evidence_scope=(
                self._get_evidence_scope(
                    structured
                )
            ),

            retrieval_count=(
                len(semantic)
            ),

            citation_count=(
                len(citations)
            ),

            # ----------------------------------------------
            # Pipeline versions
            # ----------------------------------------------

            planner_version=(
                planner_version
            ),

            engine_version=(
                engine_version
            ),

            context_version=(
                self._get_context_version()
            ),

            retrieval_version=(
                context.retrieval_version
            ),

            generator_version=(
                generator_version
            ),

            citation_version=(
                self.citation_builder.VERSION
            ),

            synthesizer_version=(
                self.VERSION
            ),
        )


    # ======================================================
    # Evidence Scope
    # ======================================================

    @staticmethod
    def _get_evidence_scope(
        evidence: dict[str, Any],
    ) -> int:
        """
        Determine the approximate number of structured
        records represented by the database evidence.

        This value describes evidence scope only. It is not
        a confidence score.
        """

        candidates = [

            evidence.get(
                "total_matching_jobs"
            ),

            evidence.get(
                "returned_jobs"
            ),

            evidence.get(
                "total_jobs"
            ),
        ]

        data = (
            evidence.get(
                "data"
            )
        )

        # --------------------------------------------------
        # Dictionary evidence
        # --------------------------------------------------

        if isinstance(
            data,
            dict,
        ):

            candidates.extend(
                [
                    data.get(
                        "total_jobs"
                    ),

                    data.get(
                        "job_count"
                    ),

                    data.get(
                        "count"
                    ),
                ]
            )

        # --------------------------------------------------
        # Find first valid count
        # --------------------------------------------------

        for value in candidates:

            if value is None:
                continue

            try:

                return max(
                    int(value),
                    0,
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

        # --------------------------------------------------
        # List evidence
        # --------------------------------------------------

        if isinstance(
            data,
            list,
        ):

            return len(
                data
            )

        return 0


    # ======================================================
    # Safe Float
    # ======================================================

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float:

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0.0


    # ======================================================
    # Safe Dictionary
    # ======================================================

    @staticmethod
    def _safe_dict(
        value: Any,
    ) -> dict[str, Any]:

        if isinstance(
            value,
            dict,
        ):

            return dict(
                value
            )

        return {}


    # ======================================================
    # Safe List
    # ======================================================

    @staticmethod
    def _safe_list(
        value: Any,
    ) -> list[str]:
        """
        Convert planner skills into a normalized,
        duplicate-free list while preserving order.
        """

        if not value:
            return []

        # --------------------------------------------------
        # Existing list
        # --------------------------------------------------

        if isinstance(
            value,
            list,
        ):

            output: list[str] = []

            seen: set[str] = set()

            for item in value:

                cleaned = str(
                    item
                ).strip()

                if not cleaned:
                    continue

                key = (
                    cleaned.casefold()
                )

                if key in seen:
                    continue

                seen.add(
                    key
                )

                output.append(
                    cleaned
                )

            return output

        # --------------------------------------------------
        # Single value
        # --------------------------------------------------

        cleaned = str(
            value
        ).strip()

        if not cleaned:
            return []

        return [
            cleaned
        ]


    # ======================================================
    # Context Version
    # ======================================================

    @staticmethod
    def _get_context_version(
    ) -> str:

        from intelligence.context_builder import (
            ContextBuilder,
        )

        return (
            ContextBuilder.VERSION
        )