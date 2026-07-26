from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from pipeline.enrichment.semantic_classifier import (
    SemanticJobClassifier,
)


INPUT_FILE = Path(
    "datasets/evaluation/job_family_evaluation_labeled.csv"
)

OUTPUT_FILE = Path(
    "datasets/evaluation/transformer_predictions.csv"
)


def safe_divide(a: int, b: int) -> float:
    return a / b if b else 0.0


def parse_skills(value: str) -> list[str]:
    if not value:
        return []

    return [
        skill.strip()
        for skill in value.split(",")
        if skill.strip()
    ]


def calculate_metrics(
    y_true: list[str],
    y_pred: list[str],
) -> tuple[
    float,
    float,
    float,
    float,
    dict,
]:

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

    metrics = {}

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

        metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    # Macro metrics use ground-truth classes only.
    supported_labels = [
        label
        for label in labels
        if metrics[label]["support"] > 0
    ]

    macro_precision = sum(
        metrics[label]["precision"]
        for label in supported_labels
    ) / len(supported_labels)

    macro_recall = sum(
        metrics[label]["recall"]
        for label in supported_labels
    ) / len(supported_labels)

    macro_f1 = sum(
        metrics[label]["f1"]
        for label in supported_labels
    ) / len(supported_labels)

    return (
        accuracy,
        macro_precision,
        macro_recall,
        macro_f1,
        metrics,
    )


def main() -> None:

    # ------------------------------------------------------
    # Read evaluation dataset
    # ------------------------------------------------------

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

    if not required_columns.issubset(
        rows[0].keys()
    ):
        raise ValueError(
            "Evaluation CSV is missing required columns."
        )

    rows = [
        row
        for row in rows
        if row["human_label"].strip()
    ]

    print()
    print("=" * 100)
    print("TRANSFORMER EVALUATION")
    print("=" * 100)

    print(
        f"Jobs to evaluate : {len(rows)}"
    )

    print(
        "Model            : "
        "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
    )

    print("=" * 100)
    print()

    classifier = SemanticJobClassifier()

    predictions = []

    # ------------------------------------------------------
    # Inference
    # ------------------------------------------------------

    for index, row in enumerate(
        rows,
        start=1,
    ):

        result = classifier.classify(
            title=row["title"],
            description=row["description"],
            skills=parse_skills(
                row["skills"]
            ),
        )

        prediction = {
            "job_id": row["job_id"],
            "title": row["title"],
            "human_label": row["human_label"],
            "transformer_prediction":
                result.family,
            "confidence":
                result.confidence,
            "second_prediction":
                result.second_family,
            "second_confidence":
                result.second_confidence,
            "margin":
                result.margin,
        }

        predictions.append(
            prediction
        )

        status = (
            "✓"
            if result.family
            == row["human_label"].strip()
            else "✗"
        )

        print(
            f"{index:03}/{len(rows)} "
            f"{status} "
            f"ID={row['job_id']} | "
            f"{row['title']}"
        )

        print(
            f"      HUMAN : "
            f"{row['human_label']}"
        )

        print(
            f"      MODEL : "
            f"{result.family}"
        )

        print(
            f"      SCORE : "
            f"{result.confidence:.4f} | "
            f"MARGIN: {result.margin:.4f}"
        )

    # ------------------------------------------------------
    # Save predictions
    # ------------------------------------------------------

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
                "transformer_prediction",
                "confidence",
                "second_prediction",
                "second_confidence",
                "margin",
            ],
        )

        writer.writeheader()
        writer.writerows(predictions)

    # ------------------------------------------------------
    # Metrics
    # ------------------------------------------------------

    y_true = [
        prediction["human_label"].strip()
        for prediction in predictions
    ]

    y_pred = [
        prediction[
            "transformer_prediction"
        ].strip()
        for prediction in predictions
    ]

    (
        accuracy,
        macro_precision,
        macro_recall,
        macro_f1,
        metrics,
    ) = calculate_metrics(
        y_true,
        y_pred,
    )

    correct = sum(
        true == pred
        for true, pred in zip(
            y_true,
            y_pred,
        )
    )

    prediction_counts = Counter(
        y_pred
    )

    predicted_other = (
        prediction_counts.get(
            "Other",
            0,
        )
    )

    coverage = safe_divide(
        len(y_pred) - predicted_other,
        len(y_pred),
    )

    # ------------------------------------------------------
    # Report
    # ------------------------------------------------------

    print()
    print("=" * 100)
    print("TRANSFORMER RESULTS")
    print("=" * 100)

    print(
        f"Jobs evaluated       : {len(y_true)}"
    )

    print(
        f"Correct predictions  : {correct}"
    )

    print(
        f"Incorrect predictions: "
        f"{len(y_true) - correct}"
    )

    print()

    print(
        f"Accuracy             : "
        f"{accuracy:.4f}"
    )

    print(
        f"Macro Precision      : "
        f"{macro_precision:.4f}"
    )

    print(
        f"Macro Recall         : "
        f"{macro_recall:.4f}"
    )

    print(
        f"Macro F1             : "
        f"{macro_f1:.4f}"
    )

    print()

    print(
        f"Predicted Other      : "
        f"{predicted_other}"
    )

    print(
        f"Specific coverage    : "
        f"{coverage:.2%}"
    )

    print()
    print("=" * 100)
    print("PER-CLASS PERFORMANCE")
    print("=" * 100)

    print(
        f"{'CLASS':40}"
        f"{'PRECISION':>12}"
        f"{'RECALL':>12}"
        f"{'F1':>12}"
        f"{'SUPPORT':>10}"
    )

    print("-" * 100)

    for label, result in metrics.items():

        print(
            f"{label[:39]:40}"
            f"{result['precision']:>12.4f}"
            f"{result['recall']:>12.4f}"
            f"{result['f1']:>12.4f}"
            f"{result['support']:>10}"
        )

    print()
    print(
        f"Predictions saved to: "
        f"{OUTPUT_FILE}"
    )

    print("=" * 100)


if __name__ == "__main__":
    main()