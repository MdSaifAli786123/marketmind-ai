from __future__ import annotations

from typing import Any

from intelligence.answer_generator import (
    AnswerGenerator,
)
from intelligence.context_builder import (
    ContextBuilder,
    GroundedContext,
)
from intelligence.llm_service import (
    LLMService,
)
from intelligence.query_engine import (
    QueryEngine,
)
from intelligence.query_planner import (
    QueryPlan,
    QueryPlanner,
)
from intelligence.response_synthesizer import (
    ResponseSynthesizer,
    SynthesizedResponse,
)


# ==========================================================
# Intelligence Service
# ==========================================================

class IntelligenceService:
    """
    Application-level orchestration service for the
    AI Job Market Intelligence system.

    Complete pipeline:

        User Question
            |
            v
        ContextBuilder
            |
            +--> QueryPlanner
            |
            +--> QueryEngine
            |
            +--> Hybrid / Semantic Retrieval
            |
            v
        GroundedContext
            |
            v
        LLMService
            |
            +--> LLM + Hybrid RAG answer
            |
            +--> deterministic fallback on failure
            |
            v
        ResponseSynthesizer
            |
            v
        Final structured response
    """

    VERSION = "intelligence-service-v3"

    DEFAULT_RAG_K = 5


    # ======================================================
    # Initialization
    # ======================================================

    def __init__(
        self,
    ) -> None:

        # --------------------------------------------------
        # Context / RAG pipeline
        # --------------------------------------------------

        self.context_builder = (
            ContextBuilder()
        )

        # --------------------------------------------------
        # LLM
        # --------------------------------------------------

        self.llm = (
            LLMService()
        )

        # --------------------------------------------------
        # Deterministic fallback
        # --------------------------------------------------

        self.fallback_generator = (
            AnswerGenerator()
        )

        # --------------------------------------------------
        # Final response construction
        # --------------------------------------------------

        self.synthesizer = (
            ResponseSynthesizer()
        )


    # ======================================================
    # Public API
    # ======================================================

    def ask(
        self,
        question: str,
        rag_k: int = DEFAULT_RAG_K,
    ) -> SynthesizedResponse:
        """
        Execute one complete intelligence request.
        """

        question = (
            str(question).strip()
        )

        if not question:

            raise ValueError(
                "Question cannot be empty."
            )

        if rag_k < 1:

            raise ValueError(
                "rag_k must be at least 1."
            )

        # --------------------------------------------------
        # 1. Build complete grounded context
        # --------------------------------------------------

        context = (
            self.context_builder.build(
                question=question,
                rag_k=rag_k,
            )
        )

        # --------------------------------------------------
        # 2. Generate grounded answer
        # --------------------------------------------------

        answer: str
        response_mode: str
        llm_model: str | None

        try:

            answer = (
                self._generate_llm_answer(
                    context
                )
            )

            if not answer.strip():

                raise ValueError(
                    "LLM returned an empty answer."
                )

            response_mode = (
                "LLM + Hybrid RAG"
            )

            llm_model = (
                self._get_llm_model()
            )

        except Exception as exc:

            # ----------------------------------------------
            # LLM failure should not make the intelligence
            # endpoint unusable.
            #
            # Structured evidence has already been produced
            # by QueryEngine, so use AnswerGenerator.
            # ----------------------------------------------

            print(
                "LLM generation failed; "
                "using deterministic fallback:",
                repr(exc),
            )

            answer = (
                self._generate_fallback_answer(
                    context
                )
            )

            response_mode = (
                "Deterministic fallback"
            )

            llm_model = None

        # --------------------------------------------------
        # 3. Build final response
        # --------------------------------------------------

        result = (
            self.synthesizer.synthesize(

                context=context,

                answer=answer,

                response_mode=(
                    response_mode
                ),

                llm_model=(
                    llm_model
                ),

                planner_version=(
                    QueryPlanner.VERSION
                ),

                engine_version=(
                    QueryEngine.VERSION
                ),

                generator_version=(
                    self._generator_version(
                        response_mode
                    )
                ),
            )
        )

        return result


    # ======================================================
    # LLM Generation
    # ======================================================

    def _generate_llm_answer(
        self,
        context: GroundedContext,
    ) -> str:
        """
        Generate an LLM answer from the complete grounded
        context produced by ContextBuilder.

        The complete GroundedContext is passed to LLMService
        so the model receives the grounded context in the
        format expected by LLMService.generate().
        """

        result = (
            self.llm.generate(
                context
            )
        )

        return (
            self._extract_text(
                result
            )
        )


    # ======================================================
    # Deterministic Fallback
    # ======================================================

    def _generate_fallback_answer(
        self,
        context: GroundedContext,
    ) -> str:
        """
        Generate a deterministic answer when the LLM is
        unavailable.

        The QueryPlan already stored in GroundedContext is
        reused. The question is NOT planned a second time.
        """

        plan = (
            self._restore_query_plan(
                context.plan
            )
        )

        result = (
            self.fallback_generator.generate(
                plan,
                context.structured_evidence,
            )
        )

        return (
            self._extract_text(
                result
            )
        )


    # ======================================================
    # Restore QueryPlan
    # ======================================================

    @staticmethod
    def _restore_query_plan(
        data: dict[str, Any],
    ) -> QueryPlan:
        """
        Reconstruct QueryPlan from the dictionary stored in
        GroundedContext.

        QueryPlan currently contains:

            intent
            filters
            skills
            limit
            original_question
            confidence
        """

        if not isinstance(
            data,
            dict,
        ):

            raise ValueError(
                "Grounded context contains "
                "an invalid query plan."
            )

        # --------------------------------------------------
        # Filters
        # --------------------------------------------------

        raw_filters = (
            data.get(
                "filters",
                {},
            )
        )

        if isinstance(
            raw_filters,
            dict,
        ):

            filters = dict(
                raw_filters
            )

        else:

            filters = {}

        # --------------------------------------------------
        # Skills
        # --------------------------------------------------

        raw_skills = (
            data.get(
                "skills",
                [],
            )
        )

        skills: list[str] = []

        if isinstance(
            raw_skills,
            list,
        ):

            seen: set[str] = set()

            for skill in raw_skills:

                cleaned = (
                    str(skill).strip()
                )

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

                skills.append(
                    cleaned
                )

        # --------------------------------------------------
        # Intent
        # --------------------------------------------------

        intent = (
            str(
                data.get(
                    "intent",
                    "market_overview",
                )
            ).strip()
        )

        if not intent:

            intent = (
                "market_overview"
            )

        # --------------------------------------------------
        # Original question
        # --------------------------------------------------

        original_question = (
            str(
                data.get(
                    "original_question",
                    "",
                )
            ).strip()
        )

        # --------------------------------------------------
        # Build QueryPlan
        # --------------------------------------------------

        return QueryPlan(

            intent=intent,

            filters=filters,

            skills=skills,

            limit=(
                IntelligenceService
                ._safe_int(
                    data.get(
                        "limit",
                        QueryPlanner.DEFAULT_LIMIT,
                    ),
                    default=(
                        QueryPlanner.DEFAULT_LIMIT
                    ),
                )
            ),

            original_question=(
                original_question
            ),

            confidence=(
                IntelligenceService
                ._safe_float(
                    data.get(
                        "confidence",
                        0.0,
                    ),
                    default=0.0,
                )
            ),
        )


    # ======================================================
    # LLM Result Adapter
    # ======================================================

    @staticmethod
    def _extract_text(
        result: Any,
    ) -> str:
        """
        Convert common LLM output formats into plain text.
        """

        if result is None:

            return ""

        # --------------------------------------------------
        # String
        # --------------------------------------------------

        if isinstance(
            result,
            str,
        ):

            return (
                result.strip()
            )

        # --------------------------------------------------
        # Dictionary
        # --------------------------------------------------

        if isinstance(
            result,
            dict,
        ):

            for key in (
                "answer",
                "content",
                "text",
                "response",
                "output",
            ):

                value = (
                    result.get(
                        key
                    )
                )

                if value is None:
                    continue

                cleaned = (
                    str(value).strip()
                )

                if cleaned:

                    return cleaned

        # --------------------------------------------------
        # LangChain / message object
        # --------------------------------------------------

        content = (
            getattr(
                result,
                "content",
                None,
            )
        )

        if content is not None:

            if isinstance(
                content,
                str,
            ):

                return (
                    content.strip()
                )

            # ----------------------------------------------
            # Some LLM providers return structured content.
            # ----------------------------------------------

            if isinstance(
                content,
                list,
            ):

                parts: list[str] = []

                for item in content:

                    if isinstance(
                        item,
                        str,
                    ):

                        cleaned = (
                            item.strip()
                        )

                        if cleaned:

                            parts.append(
                                cleaned
                            )

                    elif isinstance(
                        item,
                        dict,
                    ):

                        value = (
                            item.get(
                                "text"
                            )
                            or item.get(
                                "content"
                            )
                        )

                        if value:

                            cleaned = (
                                str(value)
                                .strip()
                            )

                            if cleaned:

                                parts.append(
                                    cleaned
                                )

                if parts:

                    return "\n".join(
                        parts
                    )

            cleaned = (
                str(content).strip()
            )

            if cleaned:

                return cleaned

        # --------------------------------------------------
        # Generic fallback
        # --------------------------------------------------

        return (
            str(result).strip()
        )


    # ======================================================
    # LLM Model Metadata
    # ======================================================

    def _get_llm_model(
        self,
    ) -> str | None:
        """
        Determine the configured model name from LLMService.
        """

        candidates = [

            getattr(
                self.llm,
                "MODEL",
                None,
            ),

            getattr(
                self.llm,
                "MODEL_NAME",
                None,
            ),

            getattr(
                self.llm,
                "model",
                None,
            ),

            getattr(
                self.llm,
                "model_name",
                None,
            ),
        ]

        for candidate in candidates:

            if candidate is None:

                continue

            # ----------------------------------------------
            # Direct model name
            # ----------------------------------------------

            if isinstance(
                candidate,
                str,
            ):

                cleaned = (
                    candidate.strip()
                )

                if cleaned:

                    return cleaned

            # ----------------------------------------------
            # Model/client object
            # ----------------------------------------------

            nested_name = (
                getattr(
                    candidate,
                    "model_name",
                    None,
                )
                or
                getattr(
                    candidate,
                    "model",
                    None,
                )
            )

            if nested_name:

                cleaned = (
                    str(
                        nested_name
                    ).strip()
                )

                if cleaned:

                    return cleaned

        return None


    # ======================================================
    # Generator Version
    # ======================================================

    def _generator_version(
        self,
        response_mode: str,
    ) -> str:
        """
        Return the generator identifier used for the answer.
        """

        if (
            response_mode
            == "Deterministic fallback"
        ):

            return str(
                getattr(
                    self.fallback_generator,
                    "VERSION",
                    "deterministic-generator",
                )
            )

        return (
            "llm-grounded-generator-v1"
        )


    # ======================================================
    # Safe Integer
    # ======================================================

    @staticmethod
    def _safe_int(
        value: Any,
        *,
        default: int,
    ) -> int:

        try:

            result = int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return default

        # Keep the restored plan within the same range
        # enforced by QueryPlanner.

        return max(
            1,
            min(
                result,
                QueryPlanner.MAX_LIMIT,
            ),
        )


    # ======================================================
    # Safe Float
    # ======================================================

    @staticmethod
    def _safe_float(
        value: Any,
        *,
        default: float,
    ) -> float:

        try:

            result = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return default

        return max(
            0.0,
            min(
                result,
                1.0,
            ),
        )


# ==========================================================
# Convenience Function
# ==========================================================

def ask_job_market(
    question: str,
    rag_k: int = 5,
) -> SynthesizedResponse:
    """
    Execute one complete job-market intelligence request.
    """

    service = (
        IntelligenceService()
    )

    return (
        service.ask(
            question=question,
            rag_k=rag_k,
        )
    )