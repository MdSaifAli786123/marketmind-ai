from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


INPUT_FILE = Path(
    "datasets/evaluation/job_family_evaluation_labeled.csv"
)


def safe_divide(a: int, b: int) -> float:
    return a / b if b else 0.0


def main() -> None:

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise ValueError("Evaluation dataset is empty.")

    required = {
        "job_id",
        "title",
        "rules_v2_prediction",
        "human_label",
    }

    if not required.issubset(rows[0].keys()):
        raise ValueError(
            "Evaluation CSV does not contain the required columns."
        )

    # -------------------------------------------------------
    # Remove rows without ground truth
    # -------------------------------------------------------

    valid_rows = [
        row
        for row in rows
        if row["human_label"].strip()
    ]

    if not valid_rows:
        raise ValueError(
            "No human labels were found."
        )

    y_true = [
        row["human_label"].strip()
        for row in valid_rows
    ]

    y_pred = [
        row["rules_v2_prediction"].strip()
        for row in valid_rows
    ]

    labels = sorted(
        set(y_true) | set(y_pred)
    )

    # -------------------------------------------------------
    # Overall accuracy
    # -------------------------------------------------------

    correct = sum(
        true == pred
        for true, pred in zip(
            y_true,
            y_pred,
        )
    )

    accuracy = safe_divide(
        correct,
        len(valid_rows),
    )

    # -------------------------------------------------------
    # Per-class metrics
    # -------------------------------------------------------

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

    # -------------------------------------------------------
    # Macro metrics
    #
    # Only classes represented in human ground truth are
    # included in macro averaging.
    # -------------------------------------------------------

    ground_truth_labels = [
        label
        for label in labels
        if metrics[label]["support"] > 0
    ]

    macro_precision = (
        sum(
            metrics[label]["precision"]
            for label in ground_truth_labels
        )
        / len(ground_truth_labels)
    )

    macro_recall = (
        sum(
            metrics[label]["recall"]
            for label in ground_truth_labels
        )
        / len(ground_truth_labels)
    )

    macro_f1 = (
        sum(
            metrics[label]["f1"]
            for label in ground_truth_labels
        )
        / len(ground_truth_labels)
    )

    # -------------------------------------------------------
    # Other statistics
    # -------------------------------------------------------

    prediction_counts = Counter(y_pred)

    predicted_other = prediction_counts.get(
        "Other",
        0,
    )

    other_rate = safe_divide(
        predicted_other,
        len(valid_rows),
    )

    specific_predictions = (
        len(valid_rows) - predicted_other
    )

    coverage = safe_divide(
        specific_predictions,
        len(valid_rows),
    )

    # -------------------------------------------------------
    # Error pairs
    # -------------------------------------------------------

    error_pairs = Counter(
        (true, pred)
        for true, pred in zip(
            y_true,
            y_pred,
        )
        if true != pred
    )

    # -------------------------------------------------------
    # Print report
    # -------------------------------------------------------

    print()
    print("=" * 100)
    print("RULES-V2 EVALUATION AGAINST HUMAN GROUND TRUTH")
    print("=" * 100)

    print(f"Jobs evaluated       : {len(valid_rows)}")
    print(f"Correct predictions  : {correct}")
    print(f"Incorrect predictions: {len(valid_rows) - correct}")

    print()
    print(f"Accuracy             : {accuracy:.4f}")
    print(f"Macro Precision      : {macro_precision:.4f}")
    print(f"Macro Recall         : {macro_recall:.4f}")
    print(f"Macro F1             : {macro_f1:.4f}")

    print()
    print(f"Specific predictions : {specific_predictions}")
    print(f"Predicted Other      : {predicted_other}")
    print(f"Coverage             : {coverage:.2%}")
    print(f"Other rate           : {other_rate:.2%}")

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

    for label in labels:

        result = metrics[label]

        print(
            f"{label[:39]:40}"
            f"{result['precision']:>12.4f}"
            f"{result['recall']:>12.4f}"
            f"{result['f1']:>12.4f}"
            f"{result['support']:>10}"
        )

    print()
    print("=" * 100)
    print("MOST COMMON ERRORS")
    print("=" * 100)

    if not error_pairs:
        print("No classification errors.")

    else:

        for (
            true,
            pred,
        ), count in error_pairs.most_common(15):

            print(
                f"{count:>3} × "
                f"{true} -> {pred}"
            )

    print()
    print("=" * 100)
    print("MISCLASSIFIED JOBS")
    print("=" * 100)

    errors_by_type = defaultdict(list)

    for row in valid_rows:

        true = row["human_label"].strip()
        pred = row["rules_v2_prediction"].strip()

        if true != pred:

            errors_by_type[
                (true, pred)
            ].append(
                (
                    row["job_id"],
                    row["title"],
                )
            )

    shown = 0

    for (
        true,
        pred,
    ), jobs in errors_by_type.items():

        print()
        print(
            f"EXPECTED: {true}"
        )

        print(
            f"PREDICTED: {pred}"
        )

        for job_id, title in jobs[:5]:

            print(
                f"  {job_id:<6} {title}"
            )

        shown += 1

        if shown >= 15:
            break

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()