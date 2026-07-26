from __future__ import annotations

from dataclasses import dataclass

from langchain_groq import ChatGroq

from config.settings import settings

from intelligence.context_builder import (
    GroundedContext,
    build_grounded_context,
)


# ==========================================================
# LLM Response
# ==========================================================

@dataclass
class LLMResponse:
    question: str
    answer: str

    intent: str
    planner_confidence: float

    structured_evidence: dict
    semantic_evidence: list[dict]

    model: str

    context_builder_version: str
    llm_service_version: str


# ==========================================================
# LLM Service
# ==========================================================

class LLMService:
    """
    Grounded LLM interface for the job-market
    intelligence system.

    Two public interfaces are provided:

    generate():
        Generate an answer from an already-built
        GroundedContext. This is used by the main
        IntelligenceService pipeline.

    ask():
        Convenience interface for standalone use.
        It builds the GroundedContext internally before
        calling generate().
    """

    VERSION = "llm-service-v3"

    DEFAULT_MODEL = settings.llm_model


    def __init__(
        self,
        model: str | None = None,
    ) -> None:

        # --------------------------------------------------
        # API Key
        # --------------------------------------------------

        api_key = settings.groq_api_key

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )


        # --------------------------------------------------
        # Model
        # --------------------------------------------------

        self.model_name = (
            model
            or settings.llm_model
        )


        # --------------------------------------------------
        # LangChain Groq Client
        # --------------------------------------------------

        self.llm = ChatGroq(
            model=self.model_name,
            temperature=settings.llm_temperature,
            api_key=api_key,
        )


    # ======================================================
    # Generate From Existing Context
    # ======================================================

    def generate(
        self,
        context: GroundedContext,
    ) -> str:
        """
        Generate an evidence-grounded answer from an
        already-built GroundedContext.

        This method does NOT perform retrieval or rebuild
        context. It is intended for IntelligenceService,
        where planning, analytics, and retrieval have
        already been completed.
        """

        if context is None:
            raise ValueError(
                "Grounded context cannot be None."
            )


        # --------------------------------------------------
        # Build Messages
        # --------------------------------------------------

        messages = [
            (
                "system",
                self._system_prompt(),
            ),
            (
                "human",
                self._user_prompt(
                    context
                ),
            ),
        ]


        # --------------------------------------------------
        # Groq Generation
        # --------------------------------------------------

        response = self.llm.invoke(
            messages
        )


        answer = self._extract_text(
            response.content
        )


        if not answer:
            raise RuntimeError(
                "LLM returned an empty response."
            )


        return answer


    # ======================================================
    # Standalone Ask Interface
    # ======================================================

    def ask(
        self,
        question: str,
        rag_k: int | None = None,
    ) -> LLMResponse:
        """
        Standalone convenience interface.

        Builds grounded context internally and then delegates
        generation to generate().
        """

        question = question.strip()


        if not question:
            raise ValueError(
                "Question cannot be empty."
            )


        # --------------------------------------------------
        # Retrieval Count
        # --------------------------------------------------

        retrieval_k = (
            rag_k
            if rag_k is not None
            else settings.rag_k
        )


        if retrieval_k < 1:
            raise ValueError(
                "rag_k must be at least 1."
            )


        # --------------------------------------------------
        # Build Grounded Context
        # --------------------------------------------------

        context = build_grounded_context(
            question=question,
            rag_k=retrieval_k,
        )


        # --------------------------------------------------
        # Generate Answer
        # --------------------------------------------------

        answer = self.generate(
            context
        )


        # --------------------------------------------------
        # Stable Response
        # --------------------------------------------------

        return LLMResponse(
            question=question,

            answer=answer,

            intent=str(
                context.plan.get(
                    "intent",
                    "unknown",
                )
            ),

            planner_confidence=float(
                context.plan.get(
                    "confidence",
                    0.0,
                )
            ),

            structured_evidence=(
                context.structured_evidence
            ),

            semantic_evidence=(
                context.semantic_evidence
            ),

            model=self.model_name,

            context_builder_version=(
                self._context_version()
            ),

            llm_service_version=(
                self.VERSION
            ),
        )


    # ======================================================
    # System Prompt
    # ======================================================

    @staticmethod
    def _system_prompt() -> str:

        return """
You are an AI Job Market Intelligence assistant.

Answer the user's question using ONLY the evidence supplied
by the application's job-market intelligence pipeline.

The evidence can contain two categories.

1. STRUCTURED DATABASE EVIDENCE

This evidence is produced by deterministic database
analytics.

Treat it as authoritative for:

- counts
- percentages
- rankings
- skill frequencies
- market statistics
- comparisons
- aggregate distributions


2. SEMANTIC RAG EVIDENCE

This evidence contains job postings retrieved because they
are semantically relevant to the user's question.

Use it for:

- job requirements
- technologies mentioned in postings
- qualitative observations
- examples of relevant positions
- contextual explanations


GROUNDING RULES

- Never invent statistics.

- Never invent jobs, companies, skills, requirements,
  salaries, locations, or technologies.

- Never present retrieved examples as representing the
  entire market unless structured evidence supports that
  conclusion.

- Prefer structured evidence when structured and semantic
  evidence conflict.

- Retrieval scores are ranking signals, not probabilities.

- Never describe retrieval relevance as statistical
  confidence.

- Do not infer causation from correlation.

- Distinguish aggregate market evidence from individual
  job examples.

- If the supplied evidence is insufficient, explicitly say
  that the available dataset does not support a reliable
  conclusion.

- Answer the actual question directly.

- Keep the response concise, clear, and evidence-grounded.
""".strip()


    # ======================================================
    # User Prompt
    # ======================================================

    @staticmethod
    def _user_prompt(
        context: GroundedContext,
    ) -> str:

        return f"""
Answer the user's question using the grounded evidence
below.

{context.context_text}

Produce the final answer using only this evidence.

Do not mention implementation details such as SQLAlchemy,
Chroma, embedding models, vector databases, prompts,
query planners, retrieval internals, or engine versions
unless the user explicitly asks about the architecture.
""".strip()


    # ======================================================
    # Response Extraction
    # ======================================================

    @staticmethod
    def _extract_text(
        content,
    ) -> str:

        if isinstance(
            content,
            str,
        ):
            return content.strip()


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

                    cleaned = item.strip()

                    if cleaned:
                        parts.append(
                            cleaned
                        )


                elif isinstance(
                    item,
                    dict,
                ):

                    text = item.get(
                        "text"
                    )

                    if text:

                        cleaned = str(
                            text
                        ).strip()

                        if cleaned:
                            parts.append(
                                cleaned
                            )


            return "\n".join(
                parts
            ).strip()


        return str(
            content
        ).strip()


    # ======================================================
    # Context Version
    # ======================================================

    @staticmethod
    def _context_version() -> str:

        from intelligence.context_builder import (
            ContextBuilder,
        )

        return ContextBuilder.VERSION


# ==========================================================
# Convenience Function
# ==========================================================

def ask_llm(
    question: str,
    rag_k: int | None = None,
) -> LLMResponse:

    service = LLMService()


    return service.ask(
        question=question,
        rag_k=rag_k,
    )


# ==========================================================
# Development Entry Point
# ==========================================================

if __name__ == "__main__":

    question = (
        "What are the top 5 skills for "
        "remote software engineering jobs?"
    )


    result = ask_llm(
        question=question,
        rag_k=3,
    )


    print(
        "\n"
        + "=" * 80
    )

    print(
        "QUESTION"
    )

    print(
        "=" * 80
    )

    print(
        result.question
    )


    print(
        "\n"
        + "=" * 80
    )

    print(
        "LLM ANSWER"
    )

    print(
        "=" * 80
    )

    print(
        result.answer
    )


    print(
        "\n"
        + "=" * 80
    )

    print(
        "METADATA"
    )

    print(
        "=" * 80
    )

    print(
        f"Intent     : "
        f"{result.intent}"
    )

    print(
        f"Confidence : "
        f"{result.planner_confidence}"
    )

    print(
        f"Model      : "
        f"{result.model}"
    )