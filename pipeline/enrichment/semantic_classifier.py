from __future__ import annotations

from dataclasses import dataclass

from transformers import pipeline

from utils.logger import logger


@dataclass(frozen=True)
class SemanticClassificationResult:
    family: str

    confidence: float

    second_family: str
    second_confidence: float

    margin: float

    accepted: bool


class SemanticJobClassifier:
    """
    Multilingual zero-shot semantic classifier.

    This classifier is intended as the semantic second layer
    after deterministic rules.

    It returns both the highest-scoring and second-highest
    categories so that confidence thresholds can be calibrated
    before production integration.
    """

    MODEL_NAME = (
        "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
    )

    # Temporary thresholds.
    # These will be calibrated using real database jobs.
    MIN_CONFIDENCE = 0.55
    MIN_MARGIN = 0.10

    MAX_DESCRIPTION_CHARS = 1800
    MAX_SKILLS = 30

    LABELS: dict[str, str] = {
        "AI/ML > Generative AI & LLM": (
            "generative AI, large language models, LLM systems, "
            "AI agents, retrieval augmented generation, "
            "AI copilots and prompt engineering"
        ),

        "AI/ML > Computer Vision": (
            "computer vision, image processing, object detection, "
            "image segmentation and visual artificial intelligence"
        ),

        "AI/ML > NLP": (
            "natural language processing, computational linguistics, "
            "text understanding and language artificial intelligence"
        ),

        "AI/ML > Machine Learning": (
            "machine learning, deep learning, predictive models, "
            "ML engineering and MLOps"
        ),

        "Data > Data Science": (
            "data science, statistical modelling, experimentation, "
            "predictive analytics and applied data research"
        ),

        "Data > Data Engineering": (
            "data engineering, ETL, data pipelines, data platforms, "
            "data warehouses and distributed data processing"
        ),

        "Data > Analytics": (
            "data analytics, business intelligence, reporting, "
            "dashboards and business analysis"
        ),

        "DevOps & Cloud": (
            "DevOps, cloud infrastructure, site reliability, "
            "platform engineering and infrastructure automation"
        ),

        "Cybersecurity": (
            "cybersecurity, information security, application security, "
            "security operations and penetration testing"
        ),

        "Software Engineering": (
            "software engineering, application development, backend, "
            "frontend, full stack, mobile and systems development"
        ),

        "Product & Management": (
            "product management, project management, program management "
            "and engineering management"
        ),

        "Other": (
            "a job primarily outside software, artificial intelligence, "
            "data, cloud, cybersecurity and technical product management"
        ),
    }

    def __init__(self) -> None:
        self._classifier = None

    # ======================================================
    # Model loading
    # ======================================================

    def _load_model(self) -> None:

        if self._classifier is not None:
            return

        logger.info(
            f"Loading semantic classifier: "
            f"{self.MODEL_NAME}"
        )

        self._classifier = pipeline(
            task="zero-shot-classification",
            model=self.MODEL_NAME,
            device=-1,
        )

        logger.info(
            "Semantic classifier loaded on CPU."
        )

    # ======================================================
    # Public API
    # ======================================================

    def classify(
        self,
        title: str,
        description: str,
        skills: list[str],
    ) -> SemanticClassificationResult:

        self._load_model()

        text = self._build_input(
            title=title,
            description=description,
            skills=skills,
        )

        candidate_labels = list(
            self.LABELS.values()
        )

        result = self._classifier(
            text,
            candidate_labels=candidate_labels,
            hypothesis_template=(
                "This job is primarily about {}."
            ),
            multi_label=False,
        )

        labels = result["labels"]
        scores = result["scores"]

        best_description = labels[0]
        best_score = float(scores[0])

        second_description = (
            labels[1]
            if len(labels) > 1
            else ""
        )

        second_score = (
            float(scores[1])
            if len(scores) > 1
            else 0.0
        )

        family = self._family_from_description(
            best_description
        )

        second_family = self._family_from_description(
            second_description
        )

        margin = best_score - second_score

        accepted = (
            best_score >= self.MIN_CONFIDENCE
            and margin >= self.MIN_MARGIN
        )

        return SemanticClassificationResult(
            family=family,
            confidence=best_score,
            second_family=second_family,
            second_confidence=second_score,
            margin=margin,
            accepted=accepted,
        )

    # ======================================================
    # Input construction
    # ======================================================

    def _build_input(
        self,
        title: str,
        description: str,
        skills: list[str],
    ) -> str:

        clean_title = (
            title.strip()
            if title
            else ""
        )

        clean_description = (
            description.strip()
            if description
            else ""
        )

        clean_description = clean_description[
            :self.MAX_DESCRIPTION_CHARS
        ]

        clean_skills = [
            skill.strip()
            for skill in skills
            if skill and skill.strip()
        ]

        skills_text = ", ".join(
            clean_skills[:self.MAX_SKILLS]
        )

        return (
            f"Job title: {clean_title}\n"
            f"Skills: {skills_text}\n"
            f"Job description: {clean_description}"
        )

    # ======================================================
    # Label mapping
    # ======================================================

    def _family_from_description(
        self,
        description: str,
    ) -> str:

        for family, label_description in self.LABELS.items():

            if label_description == description:
                return family

        return "Other"