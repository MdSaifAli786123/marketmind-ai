from pipeline.enrichment.existing_skill_enricher import (
    ExistingSkillEnricher,
)
from utils.logger import logger


def main() -> None:
    logger.info(
        "Starting enrichment of existing database skills..."
    )

    enricher = ExistingSkillEnricher()

    normalized, deleted, failed = enricher.run()

    logger.info(
        f"Historical enrichment finished: "
        f"normalized={normalized}, "
        f"deleted={deleted}, "
        f"failed={failed}"
    )


if __name__ == "__main__":
    main()