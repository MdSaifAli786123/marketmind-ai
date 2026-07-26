from __future__ import annotations

import csv
from pathlib import Path


LABELED_FILE = Path(
    "datasets/evaluation/job_family_evaluation_labeled.csv"
)

TRANSFORMER_FILE = Path(
    "datasets/evaluation/transformer_predictions.csv"
)


def safe_divide(a: int, b: int) -> float:
    return a / b if b else 0.0


def calculate_metrics(
    y_true: list[str],
    y_pred: list[str],
) -> dict:

    labels = sorted(set(y_true) | set(y_pred))

    correct = sum(
        true == pred
        for true, pred in zip(y_true, y_pred)
    )

    accuracy = safe_divide(correct, len(y_true))

    class_metrics = {}

    for label in labels:

        tp = sum(
            true == label and pred == label
            for true, pred in zip(y_true, y_pred)
        )

        fp = sum(
            true != label and pred == label
            for true, pred in zip(y_true, y_pred)
        )

        fn = sum(
            true == label and pred != label
            for true, pred in zip(y_true, y_pred)
        )

        precision = safe_divide(tp, tp + fp)
        recall = safe_divide(tp, tp + fn)

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

    supported_labels = [
        label
        for label in labels
        if class_metrics[label]["support"] > 0
    ]

    macro_precision = sum(
        class_metrics[label]["precision"]
        for label in supported_labels
    ) / len(supported_labels)

    macro_recall = sum(
        class_metrics[label]["recall"]
        for label in supported_labels
    ) / len(supported_labels)

    macro_f1 = sum(
        class_metrics[label]["f1"]
        for label in supported_labels
    ) / len(supported_labels)

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
        "predicted_other": predicted_other,
        "coverage": coverage,
        "correct": correct,
    }


def load_data():

    # --------------------------------------------------
    # Load labeled Rules-v2 dataset
    # --------------------------------------------------

    with LABELED_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        labeled_rows = list(
            csv.DictReader(file)
        )

    # --------------------------------------------------
    # Load cached Transformer predictions
    # --------------------------------------------------

    with TRANSFORMER_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        transformer_rows = list(
            csv.DictReader(file)
        )

    transformer_by_id = {
        row["job_id"].strip(): row
        for row in transformer_rows
    }

    records = []

    for row in labeled_rows:

        job_id = row["job_id"].strip()

        if not row["human_label"].strip():
            continue

        transformer = transformer_by_id.get(job_id)

        if transformer is None:
            raise ValueError(
                f"Missing Transformer prediction "
                f"for job_id={job_id}"
            )

        records.append(
            {
                "job_id": job_id,
                "title": row["title"],
                "human_label":
                    row["human_label"].strip(),
                "rules_prediction":
                    row["rules_v2_prediction"].strip(),
                "transformer_prediction":
                    transformer[
                        "transformer_prediction"
                    ].strip(),
                "confidence": float(
                    transformer["confidence"]
                ),
                "margin": float(
                    transformer["margin"]
                ),
            }
        )

    return records


def hybrid_predict(
    record: dict,
    confidence_threshold: float,
    margin_threshold: float,
) -> tuple[str, bool]:

    rules_prediction = record[
        "rules_prediction"
    ]

    # Rules remain authoritative whenever they
    # already produced a specific category.
    if rules_prediction != "Other":
        return rules_prediction, False

    transformer_prediction = record[
        "transformer_prediction"
    ]

    # Transformer cannot improve an Other prediction
    # by predicting Other again.
    if transformer_prediction == "Other":
        return "Other", False

    if (
        record["confidence"] >= confidence_threshold
        and record["margin"] >= margin_threshold
    ):
        return transformer_prediction, True

    return "Other", False


def main() -> None:

    records = load_data()

    y_true = [
        record["human_label"]
        for record in records
    ]

    rules_predictions = [
        record["rules_prediction"]
        for record in records
    ]

    baseline = calculate_metrics(
        y_true,
        rules_predictions,
    )

    print()
    print("=" * 110)
    print("HYBRID CLASSIFIER THRESHOLD SEARCH")
    print("=" * 110)

    print(f"Jobs evaluated : {len(records)}")

    print()
    print("RULES BASELINE")
    print("-" * 110)

    print(
        f"Accuracy : "
        f"{baseline['accuracy']:.4f}"
    )

    print(
        f"Macro F1 : "
        f"{baseline['macro_f1']:.4f}"
    )

    print(
        f"Coverage : "
        f"{baseline['coverage']:.2%}"
    )

    print(
        f"Other    : "
        f"{baseline['predicted_other']}"
    )

    # --------------------------------------------------
    # Threshold grid
    # --------------------------------------------------

    confidence_thresholds = [
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.35,
        0.40,
        0.45,
        0.50,
        0.60,
        0.70,
    ]

    margin_thresholds = [
        0.00,
        0.02,
        0.05,
        0.10,
        0.15,
        0.20,
        0.30,
        0.40,
        0.50,
    ]

    results = []

    for confidence_threshold in confidence_thresholds:

        for margin_threshold in margin_thresholds:

            predictions = []
            transformer_used = 0

            for record in records:

                prediction, used = hybrid_predict(
                    record,
                    confidence_threshold,
                    margin_threshold,
                )

                predictions.append(prediction)

                if used:
                    transformer_used += 1

            metrics = calculate_metrics(
                y_true,
                predictions,
            )

            results.append(
                {
                    "confidence":
                        confidence_threshold,
                    "margin":
                        margin_threshold,
                    "transformer_used":
                        transformer_used,
                    **metrics,
                }
            )

    # --------------------------------------------------
    # Sort primarily by Macro F1, then accuracy,
    # then fewer Transformer interventions.
    # --------------------------------------------------

    results.sort(
        key=lambda result: (
            result["macro_f1"],
            result["accuracy"],
            -result["transformer_used"],
        ),
        reverse=True,
    )

    print()
    print("=" * 110)
    print("TOP HYBRID CONFIGURATIONS")
    print("=" * 110)

    print(
        f"{'CONF':>8}"
        f"{'MARGIN':>10}"
        f"{'USED':>8}"
        f"{'ACCURACY':>12}"
        f"{'MACRO F1':>12}"
        f"{'COVERAGE':>12}"
        f"{'OTHER':>8}"
    )

    print("-" * 110)

    for result in results[:20]:

        print(
            f"{result['confidence']:>8.2f}"
            f"{result['margin']:>10.2f}"
            f"{result['transformer_used']:>8}"
            f"{result['accuracy']:>12.4f}"
            f"{result['macro_f1']:>12.4f}"
            f"{result['coverage']:>11.2%}"
            f"{result['predicted_other']:>8}"
        )

    # --------------------------------------------------
    # Best configuration
    # --------------------------------------------------

    best = results[0]

    best_predictions = []

    interventions = []

    for record in records:

        prediction, used = hybrid_predict(
            record,
            best["confidence"],
            best["margin"],
        )

        best_predictions.append(prediction)

        if used:

            interventions.append(
                {
                    **record,
                    "hybrid_prediction":
                        prediction,
                    "correct":
                        prediction
                        == record["human_label"],
                }
            )

    print()
    print("=" * 110)
    print("BEST HYBRID")
    print("=" * 110)

    print(
        f"Confidence threshold : "
        f"{best['confidence']:.2f}"
    )

    print(
        f"Margin threshold     : "
        f"{best['margin']:.2f}"
    )

    print(
        f"Accuracy             : "
        f"{best['accuracy']:.4f}"
    )

    print(
        f"Macro F1             : "
        f"{best['macro_f1']:.4f}"
    )

    print(
        f"Coverage             : "
        f"{best['coverage']:.2%}"
    )

    print(
        f"Transformer used     : "
        f"{best['transformer_used']}"
    )

    print(
        f"Predicted Other      : "
        f"{best['predicted_other']}"
    )

    print()
    print("CHANGE FROM RULES BASELINE")
    print("-" * 110)

    print(
        f"Accuracy : "
        f"{baseline['accuracy']:.4f}"
        f" -> "
        f"{best['accuracy']:.4f}"
    )

    print(
        f"Macro F1 : "
        f"{baseline['macro_f1']:.4f}"
        f" -> "
        f"{best['macro_f1']:.4f}"
    )

    print(
        f"Coverage : "
        f"{baseline['coverage']:.2%}"
        f" -> "
        f"{best['coverage']:.2%}"
    )

    print()
    print("=" * 110)
    print("TRANSFORMER INTERVENTIONS")
    print("=" * 110)

    if not interventions:

        print(
            "Best configuration does not use "
            "the Transformer."
        )

    else:

        for item in interventions:

            status = (
                "CORRECT"
                if item["correct"]
                else "WRONG"
            )

            print()
            print(
                f"ID={item['job_id']} | "
                f"{item['title']}"
            )

            print(
                f"  Human       : "
                f"{item['human_label']}"
            )

            print(
                f"  Rules       : "
                f"{item['rules_prediction']}"
            )

            print(
                f"  Transformer : "
                f"{item['transformer_prediction']}"
            )

            print(
                f"  Confidence  : "
                f"{item['confidence']:.4f}"
            )

            print(
                f"  Margin      : "
                f"{item['margin']:.4f}"
            )

            print(
                f"  Result      : {status}"
            )

    print()
    print("=" * 110)


if __name__ == "__main__":
    main()