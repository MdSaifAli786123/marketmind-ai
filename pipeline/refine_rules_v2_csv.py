from __future__ import annotations

import csv
from pathlib import Path

from pipeline.enrichment.semantic_classifier import (
    SemanticJobClassifier,
)


INPUT_FILE = Path(
    "datasets/evaluation/job_family_evaluation_labeled.csv"
)

OUTPUT_FILE = Path(
    "datasets/evaluation/job_family_evaluation_refined.csv"
)

# Experimental semantic acceptance threshold.
MIN_CONFIDENCE = 0.20

# Keep a small separation requirement between first and second choice.
MIN_MARGIN = 0.03


def parse_skills(value: str) -> list[str]:
    if not value:
        return []

    return [
        skill.strip()
        for skill in value.split(",")
        if skill.strip()
    ]


def main() -> None:

    classifier = SemanticJobClassifier()

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)
        rows = list(reader)

    required_columns = {
        "job_id",
        "title",
        "description",
        "skills",
        "rules_v2_prediction",
        "human_label",
    }

    if not rows:
        raise ValueError(
            "Input CSV contains no jobs."
        )

    if not required_columns.issubset(
        reader.fieldnames or []
    ):
        raise ValueError(
            "CSV does not contain the expected columns."
        )

    original_other = 0
    replaced = 0
    remained_other = 0

    print()
    print("=" * 90)
    print("REFINING RULES-V2 OTHER PREDICTIONS")
    print("=" * 90)

    for index, row in enumerate(
        rows,
        start=1,
    ):

        current_prediction = (
            row["rules_v2_prediction"].strip()
        )

        # Leave every existing non-Other prediction untouched.
        if current_prediction != "Other":
            continue

        original_other += 1

        result = classifier.classify(
            title=row["title"],
            description=row["description"],
            skills=parse_skills(
                row["skills"]
            ),
        )

        # Do not replace Other with Other.
        semantic_is_specific = (
            result.family != "Other"
        )

        sufficiently_confident = (
            result.confidence >= MIN_CONFIDENCE
        )

        sufficiently_separated = (
            result.margin >= MIN_MARGIN
        )

        if (
            semantic_is_specific
            and sufficiently_confident
            and sufficiently_separated
        ):
            row["rules_v2_prediction"] = (
                result.family
            )

            replaced += 1

            action = (
                f"REPLACED → {result.family}"
            )

        else:
            remained_other += 1
            action = "KEPT → Other"

        print(
            f"{index:03} | "
            f"ID={row['job_id']} | "
            f"{row['title']}"
        )

        print(
            f"      semantic = "
            f"{result.family}"
        )

        print(
            f"      confidence = "
            f"{result.confidence:.4f}"
        )

        print(
            f"      margin = "
            f"{result.margin:.4f}"
        )

        print(
            f"      {action}"
        )

    # IMPORTANT:
    # Write ONLY the original six columns.
    fieldnames = [
        "job_id",
        "title",
        "description",
        "skills",
        "rules_v2_prediction",
        "human_label",
    ]

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
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field: row[field]
                    for field in fieldnames
                }
            )

    print()
    print("=" * 90)
    print("REFINEMENT COMPLETE")
    print("=" * 90)

    print(
        f"Original Other predictions : "
        f"{original_other}"
    )

    print(
        f"Replaced by transformer    : "
        f"{replaced}"
    )

    print(
        f"Still Other                : "
        f"{remained_other}"
    )

    print(
        f"Output                     : "
        f"{OUTPUT_FILE}"
    )

    print("=" * 90)


if __name__ == "__main__":
    main()