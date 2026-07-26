from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from pipeline.enrichment.job_enricher import JobEnricher


INPUT_FILE = Path(
    "datasets/evaluation/attribute_evaluation_labeled.csv"
)


def clean(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(
        str(value).split()
    )


def accuracy(
    expected: list[str],
    predicted: list[str],
) -> float:

    if not expected:
        return 0.0

    correct = sum(
        a == b
        for a, b in zip(
            expected,
            predicted,
        )
    )

    return correct / len(expected)


def macro_f1(
    expected: list[str],
    predicted: list[str],
) -> float:

    labels = sorted(
        set(expected)
        | set(predicted)
    )

    scores = []

    for label in labels:

        tp = sum(
            e == label and p == label
            for e, p in zip(
                expected,
                predicted,
            )
        )

        fp = sum(
            e != label and p == label
            for e, p in zip(
                expected,
                predicted,
            )
        )

        fn = sum(
            e == label and p != label
            for e, p in zip(
                expected,
                predicted,
            )
        )

        precision = (
            tp / (tp + fp)
            if tp + fp
            else 0.0
        )

        recall = (
            tp / (tp + fn)
            if tp + fn
            else 0.0
        )

        f1 = (
            2 * precision * recall
            / (precision + recall)
            if precision + recall
            else 0.0
        )

        scores.append(f1)

    return (
        sum(scores) / len(scores)
        if scores
        else 0.0
    )


def main() -> None:

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing evaluation file: "
            f"{INPUT_FILE}"
        )

    enricher = JobEnricher()

    exp_expected = []
    exp_predicted = []

    type_expected = []
    type_predicted = []

    mistakes = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            title = clean(
                row.get("title")
            )

            description = clean(
                row.get("description")
            )

            expected_exp = clean(
                row.get(
                    "human_experience_level"
                )
            )

            expected_type = clean(
                row.get(
                    "human_job_type"
                )
            )

            result = enricher.enrich(
                title=title,
                description=description,
                skills=[],
            )

            predicted_exp = (
                result.experience_level
            )

            predicted_type = (
                result.job_type
            )

            exp_expected.append(
                expected_exp
            )

            exp_predicted.append(
                predicted_exp
            )

            type_expected.append(
                expected_type
            )

            type_predicted.append(
                predicted_type
            )

            if (
                expected_exp
                != predicted_exp
                or expected_type
                != predicted_type
            ):
                mistakes.append(
                    {
                        "id": row.get("id"),
                        "title": title,
                        "exp_expected":
                            expected_exp,
                        "exp_predicted":
                            predicted_exp,
                        "type_expected":
                            expected_type,
                        "type_predicted":
                            predicted_type,
                    }
                )

    print()
    print("=" * 80)
    print("ATTRIBUTE CLASSIFIER EVALUATION")
    print("=" * 80)

    print()
    print("EXPERIENCE LEVEL")
    print("-" * 80)

    print(
        f"Accuracy : "
        f"{accuracy(exp_expected, exp_predicted):.4f}"
    )

    print(
        f"Macro F1 : "
        f"{macro_f1(exp_expected, exp_predicted):.4f}"
    )

    print()
    print("Expected:")
    print(
        Counter(exp_expected)
    )

    print("Predicted:")
    print(
        Counter(exp_predicted)
    )

    print()
    print("JOB TYPE")
    print("-" * 80)

    print(
        f"Accuracy : "
        f"{accuracy(type_expected, type_predicted):.4f}"
    )

    print(
        f"Macro F1 : "
        f"{macro_f1(type_expected, type_predicted):.4f}"
    )

    print()
    print("Expected:")
    print(
        Counter(type_expected)
    )

    print("Predicted:")
    print(
        Counter(type_predicted)
    )

    print()
    print("MISCLASSIFIED JOBS")
    print("-" * 80)

    for item in mistakes:

        print()
        print(
            f"ID={item['id']} | "
            f"{item['title']}"
        )

        if (
            item["exp_expected"]
            != item["exp_predicted"]
        ):
            print(
                f"  EXPERIENCE: "
                f"{item['exp_expected']} "
                f"-> "
                f"{item['exp_predicted']}"
            )

        if (
            item["type_expected"]
            != item["type_predicted"]
        ):
            print(
                f"  JOB TYPE : "
                f"{item['type_expected']} "
                f"-> "
                f"{item['type_predicted']}"
            )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()