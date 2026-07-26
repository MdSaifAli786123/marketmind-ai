from __future__ import annotations

import ast
import csv
from collections import Counter
from pathlib import Path

from pipeline.enrichment.job_enricher import JobEnricher


INPUT_FILE = Path(
    "datasets/evaluation/job_family_evaluation_labeled.csv"
)

OUTPUT_FILE = Path(
    "datasets/evaluation/rules_v3_predictions.csv"
)


# ==========================================================
# Helpers
# ==========================================================

def safe_divide(a: int, b: int) -> float:
    return a / b if b else 0.0


def parse_skills(value: str | None) -> list[str]:
    """
    Supports both:

        python-list representation:
        ['python', 'docker', 'aws']

    and:

        comma-separated representation:
        python,docker,aws
    """

    if not value:
        return []

    value = value.strip()

    if not value:
        return []

    # Try Python list representation first.
    if value.startswith("[") and value.endswith("]"):

        try:
            parsed = ast.literal_eval(value)

            if isinstance(parsed, list):
                return [
                    str(skill).strip()
                    for skill in parsed
                    if str(skill).strip()
                ]

        except (
            ValueError,
            SyntaxError,
        ):
            pass

    # Fall back to CSV-style list.
    return [
        skill.strip()
        for skill in value.split(",")
        if skill.strip()
    ]


def calculate_metrics(
    y_true: list[str],
    y_pred: list[str],
) -> dict:

    labels = sorted(
        set(y_true) | set(y_pred)
    )

    correct = sum(
        true == pred
        for true, pred in zip(
            y_true,
            y_pred,
        )
    )

    accuracy = safe_divide(
        correct,
        len(y_true),
    )

    class_metrics = {}

    for label in labels:

        tp = sum(
            true == label and pred == label
            for true, pred in zip(
                y_true,
                y_pred,
            )
        )

        fp = sum(
            true != label and pred == label
            for true, pred in zip(
                y_true,
                y_pred,
            )
        )

        fn = sum(
            true == label and pred != label
            for true, pred in zip(
                y_true,
                y_pred,
            )
        )

        precision = safe_divide(
            tp,
            tp + fp,
        )

        recall = safe_divide(
            tp,
            tp + fn,
        )

        f1 = (
            2 * precision * recall
            / (precision + recall)
            if precision + recall
            else 0.0
        )

        support = sum(
            true == label
            for true in y_true
        )

        class_metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    # Macro metrics only across classes actually represented
    # in the human ground truth.
    supported_labels = [
        label
        for label in labels
        if class_metrics[label]["support"] > 0
    ]

    macro_precision = (
        sum(
            class_metrics[label]["precision"]
            for label in supported_labels
        )
        / len(supported_labels)
    )

    macro_recall = (
        sum(
            class_metrics[label]["recall"]
            for label in supported_labels
        )
        / len(supported_labels)
    )

    macro_f1 = (
        sum(
            class_metrics[label]["f1"]
            for label in supported_labels
        )
        / len(supported_labels)
    )

    predicted_other = sum(
        pred == "Other"
        for pred in y_pred
    )

    coverage = safe_divide(
        len(y_pred) - predicted_other,
        len(y_pred),
    )

    return {
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "correct": correct,
        "incorrect": len(y_true) - correct,
        "predicted_other": predicted_other,
        "coverage": coverage,
        "class_metrics": class_metrics,
    }


# ==========================================================
# Main
# ==========================================================

def main() -> None:

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        rows = list(
            csv.DictReader(file)
        )

    if not rows:
        raise ValueError(
            "Evaluation dataset is empty."
        )

    required_columns = {
        "job_id",
        "title",
        "description",
        "skills",
        "human_label",
    }

    missing_columns = (
        required_columns
        - set(rows[0].keys())
    )

    if missing_columns:
        raise ValueError(
            "Missing required CSV columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    # Only evaluate manually labeled records.
    rows = [
        row
        for row in rows
        if row["human_label"].strip()
    ]

    if not rows:
        raise ValueError(
            "No human-labeled jobs were found."
        )

    enricher = JobEnricher()

    print()
    print("=" * 105)
    print("RULES-V3 REPRODUCIBLE EVALUATION")
    print("=" * 105)

    print(
        f"Jobs evaluated : {len(rows)}"
    )

    print(
        f"Classifier     : {enricher.VERSION}"
    )

    print("=" * 105)

    predictions = []

    y_true = []
    y_pred = []

    # ======================================================
    # Run the REAL classifier
    # ======================================================

    for row in rows:

        job_id = row["job_id"].strip()
        title = row["title"].strip()

        description = (
            row.get("description")
            or ""
        )

        skills = parse_skills(
            row.get("skills")
        )

        human_label = (
            row["human_label"].strip()
        )

        result = enricher.enrich(
            title=title,
            description=description,
            skills=skills,
        )

        prediction = result.job_family

        y_true.append(
            human_label
        )

        y_pred.append(
            prediction
        )

        predictions.append(
            {
                "job_id": job_id,
                "title": title,
                "human_label": human_label,
                "rules_v3_prediction":
                    prediction,
                "job_family_score":
                    result.job_family_score,
                "correct":
                    prediction == human_label,
            }
        )

    # ======================================================
    # Metrics
    # ======================================================

    metrics = calculate_metrics(
        y_true,
        y_pred,
    )

    # ======================================================
    # Save predictions
    # ======================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "job_id",
                "title",
                "human_label",
                "rules_v3_prediction",
                "job_family_score",
                "correct",
            ],
        )

        writer.writeheader()
        writer.writerows(
            predictions
        )

    # ======================================================
    # Summary
    # ======================================================

    print()
    print("=" * 105)
    print("RULES-V3 RESULTS")
    print("=" * 105)

    print(
        f"Jobs evaluated       : "
        f"{len(y_true)}"
    )

    print(
        f"Correct predictions  : "
        f"{metrics['correct']}"
    )

    print(
        f"Incorrect predictions: "
        f"{metrics['incorrect']}"
    )

    print()

    print(
        f"Accuracy             : "
        f"{metrics['accuracy']:.4f}"
    )

    print(
        f"Macro Precision      : "
        f"{metrics['macro_precision']:.4f}"
    )

    print(
        f"Macro Recall         : "
        f"{metrics['macro_recall']:.4f}"
    )

    print(
        f"Macro F1             : "
        f"{metrics['macro_f1']:.4f}"
    )

    print()

    print(
        f"Specific predictions : "
        f"{len(y_pred) - metrics['predicted_other']}"
    )

    print(
        f"Predicted Other      : "
        f"{metrics['predicted_other']}"
    )

    print(
        f"Coverage             : "
        f"{metrics['coverage']:.2%}"
    )

    # ======================================================
    # Per-class metrics
    # ======================================================

    print()
    print("=" * 105)
    print("PER-CLASS PERFORMANCE")
    print("=" * 105)

    print(
        f"{'CLASS':42}"
        f"{'PRECISION':>12}"
        f"{'RECALL':>12}"
        f"{'F1':>12}"
        f"{'SUPPORT':>10}"
    )

    print("-" * 105)

    for label, result in (
        metrics["class_metrics"].items()
    ):

        print(
            f"{label[:41]:42}"
            f"{result['precision']:>12.4f}"
            f"{result['recall']:>12.4f}"
            f"{result['f1']:>12.4f}"
            f"{result['support']:>10}"
        )

    # ======================================================
    # Error transitions
    # ======================================================

    errors = [
        prediction
        for prediction in predictions
        if not prediction["correct"]
    ]

    error_counts = Counter(
        (
            item["human_label"],
            item["rules_v3_prediction"],
        )
        for item in errors
    )

    print()
    print("=" * 105)
    print("MOST COMMON ERRORS")
    print("=" * 105)

    if not error_counts:

        print(
            "No misclassifications."
        )

    else:

        for (
            expected,
            predicted,
        ), count in error_counts.most_common():

            print(
                f"{count:>3} × "
                f"{expected} -> {predicted}"
            )

    # ======================================================
    # Detailed errors
    # ======================================================

    print()
    print("=" * 105)
    print("MISCLASSIFIED JOBS")
    print("=" * 105)

    if not errors:

        print(
            "No misclassified jobs."
        )

    else:

        for item in errors:

            print()

            print(
                f"ID={item['job_id']} | "
                f"{item['title']}"
            )

            print(
                f"  HUMAN : "
                f"{item['human_label']}"
            )

            print(
                f"  RULES : "
                f"{item['rules_v3_prediction']}"
            )

            print(
                f"  SCORE : "
                f"{item['job_family_score']}"
            )

    print()
    print("=" * 105)

    print(
        f"Predictions saved to: "
        f"{OUTPUT_FILE}"
    )

    print("=" * 105)


if __name__ == "__main__":
    main()