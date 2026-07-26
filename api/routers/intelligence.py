from __future__ import annotations

import json
from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import (
    BaseModel,
    Field,
)

from database.connection import (
    SessionLocal,
)
from database.models import (
    QueryHistory,
)

from intelligence.intelligence_service import (
    IntelligenceService,
)


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
)


# ==========================================================
# Service
# ==========================================================

service = (
    IntelligenceService()
)


# ==========================================================
# Request Schema
# ==========================================================

class IntelligenceRequest(BaseModel):
    """
    Request body for the AI job-market intelligence
    endpoint.
    """

    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description=(
            "Natural-language question about "
            "the job-market dataset."
        ),
    )

    rag_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description=(
            "Maximum number of semantically relevant "
            "job documents retrieved for RAG."
        ),
    )


# ==========================================================
# Citation Schema
# ==========================================================

class CitationResponse(BaseModel):
    """
    One retrieved job posting exposed as supporting
    evidence for the generated response.
    """

    citation_id: int

    job_id: int | None = None

    title: str

    company: str

    source: str | None = None

    source_url: str | None = None

    country: str | None = None

    remote: bool = False

    skills: list[str] = Field(
        default_factory=list
    )

    hybrid_score: float | None = None


# ==========================================================
# Response Schema
# ==========================================================

class IntelligenceResponse(BaseModel):
    """
    Complete response returned by the AI intelligence
    pipeline.
    """

    # ------------------------------------------------------
    # Question + answer
    # ------------------------------------------------------

    question: str

    answer: str

    # ------------------------------------------------------
    # Query-plan information
    # ------------------------------------------------------

    intent: str

    confidence: float

    filters: dict[str, Any]

    skills: list[str]

    # ------------------------------------------------------
    # Evidence
    # ------------------------------------------------------

    evidence: dict[str, Any]

    semantic_evidence: list[
        dict[str, Any]
    ]

    citations: list[
        CitationResponse
    ]

    # ------------------------------------------------------
    # Generation information
    # ------------------------------------------------------

    response_mode: str

    llm_model: str | None

    # ------------------------------------------------------
    # Evidence diagnostics
    # ------------------------------------------------------

    evidence_scope: int

    retrieval_count: int

    citation_count: int

    # ------------------------------------------------------
    # Pipeline versions
    # ------------------------------------------------------

    planner_version: str

    engine_version: str

    context_version: str

    retrieval_version: str

    generator_version: str

    citation_version: str

    synthesizer_version: str

    service_version: str


# ==========================================================
# POST /intelligence/ask
# ==========================================================

@router.post(
    "/ask",
    response_model=IntelligenceResponse,
    summary=(
        "Ask the AI job-market intelligence engine"
    ),
)
def ask_intelligence(
    request: IntelligenceRequest,
) -> IntelligenceResponse:
    """
    Execute the complete intelligence pipeline.

    Pipeline:

        Question
            ↓
        Query Planner
            ↓
        Structured Query Engine
            ↓
        Hybrid RAG Retrieval
            ↓
        Grounded Context
            ↓
        LLM
            ↓
        Citation Builder
            ↓
        Response Synthesizer
            ↓
        API Response
    """

    question = (
        request.question.strip()
    )

    if not question:

        raise HTTPException(
            status_code=400,
            detail=(
                "Question cannot be empty."
            ),
        )

    try:

        # --------------------------------------------------
        # 1. Execute complete intelligence service
        # --------------------------------------------------

        result = (
            service.ask(
                question=question,
                rag_k=request.rag_k,
            )
        )

        # --------------------------------------------------
        # 2. Save request metadata
        #
        # QueryHistory still contains the historical
        # generated_sql column. We use it to store pipeline
        # metadata as JSON. No generated SQL is executed.
        # --------------------------------------------------

        save_query_history(
            question=question,
            payload={
                "intent": (
                    result.intent
                ),

                "planner_confidence": (
                    result.planner_confidence
                ),

                "filters": (
                    result.filters
                ),

                "skills": (
                    result.skills
                ),

                "response_mode": (
                    result.response_mode
                ),

                "llm_model": (
                    result.llm_model
                ),

                "evidence_scope": (
                    result.evidence_scope
                ),

                "retrieval_count": (
                    result.retrieval_count
                ),

                "citation_count": (
                    result.citation_count
                ),

                "planner_version": (
                    result.planner_version
                ),

                "engine_version": (
                    result.engine_version
                ),

                "context_version": (
                    result.context_version
                ),

                "retrieval_version": (
                    result.retrieval_version
                ),

                "generator_version": (
                    result.generator_version
                ),

                "citation_version": (
                    result.citation_version
                ),

                "synthesizer_version": (
                    result.synthesizer_version
                ),

                "service_version": (
                    service.VERSION
                ),
            },
        )

        # --------------------------------------------------
        # 3. Convert synthesized response into API schema
        #
        # We keep:
        #
        # planner_confidence -> confidence
        # structured_evidence -> evidence
        #
        # so the existing React UI remains compatible.
        # --------------------------------------------------

        return IntelligenceResponse(

            question=(
                result.question
            ),

            answer=(
                result.answer
            ),

            intent=(
                result.intent
            ),

            confidence=(
                result.planner_confidence
            ),

            filters=(
                result.filters
            ),

            skills=(
                result.skills
            ),

            evidence=(
                result.structured_evidence
            ),

            semantic_evidence=(
                result.semantic_evidence
            ),

            citations=[
                CitationResponse(
                    **citation
                )
                for citation
                in result.citations
            ],

            response_mode=(
                result.response_mode
            ),

            llm_model=(
                result.llm_model
            ),

            evidence_scope=(
                result.evidence_scope
            ),

            retrieval_count=(
                result.retrieval_count
            ),

            citation_count=(
                result.citation_count
            ),

            planner_version=(
                result.planner_version
            ),

            engine_version=(
                result.engine_version
            ),

            context_version=(
                result.context_version
            ),

            retrieval_version=(
                result.retrieval_version
            ),

            generator_version=(
                result.generator_version
            ),

            citation_version=(
                result.citation_version
            ),

            synthesizer_version=(
                result.synthesizer_version
            ),

            service_version=(
                service.VERSION
            ),
        )

    # ======================================================
    # Expected validation errors
    # ======================================================

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    # ======================================================
    # Unexpected errors
    # ======================================================

    except Exception as exc:

        print(
            "Intelligence API error:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The intelligence engine could "
                "not process this question."
            ),
        ) from exc


# ==========================================================
# Query History
# ==========================================================

def save_query_history(
    question: str,
    payload: dict[str, Any],
) -> None:
    """
    Persist metadata about an intelligence request.

    QueryHistory currently has a legacy column named
    generated_sql. The column stores serialized pipeline
    metadata until the database model is migrated to a more
    appropriate schema.

    No arbitrary generated SQL is executed.
    """

    serialized_payload = (
        json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
    )

    try:

        with SessionLocal() as session:

            history = (
                QueryHistory(
                    question=question,
                    generated_sql=(
                        serialized_payload
                    ),
                )
            )

            session.add(
                history
            )

            session.commit()

    except Exception as exc:

        # Query-history failure should never make a valid
        # intelligence request fail.

        print(
            "Query history save failed:",
            repr(exc),
        )