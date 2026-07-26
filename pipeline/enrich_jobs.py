from pipeline.enrichment.database_enricher import (
    DatabaseJobEnricher,
)
from utils.logger import logger


def main() -> None:

    logger.info(
        "Starting intelligent job enrichment..."
    )

    enricher = DatabaseJobEnricher()

    enriched, failed = enricher.run()

    logger.info(
        f"Intelligent enrichment finished: "
        f"enriched={enriched}, "
        f"failed={failed}"
    )


if __name__ == "__main__":
    main()