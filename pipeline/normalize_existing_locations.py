from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.connection import SessionLocal
from database.models import Job
from pipeline.enrichment.location_normalizer import LocationNormalizer
from utils.logger import logger


def run() -> tuple[int, int, int]:
    """
    Normalize locations already stored in PostgreSQL/Neon.

    Existing database convention:
    historical transformers stored the raw source location
    primarily in Location.country.

    This script converts that historical representation into:

        city
        state
        country
        remote

    using LocationNormalizer.

    The transaction is committed only after all jobs have been
    processed successfully.
    """

    normalizer = LocationNormalizer()

    processed = 0
    changed = 0
    without_location = 0

    with SessionLocal() as session:
        try:
            statement = (
                select(Job)
                .options(
                    selectinload(Job.location)
                )
                .order_by(Job.id)
            )

            jobs = list(
                session.scalars(
                    statement
                ).all()
            )

            logger.info(
                f"Jobs loaded for location normalization: "
                f"{len(jobs)}"
            )

            for job in jobs:
                location = job.location

                if location is None:
                    without_location += 1
                    processed += 1
                    continue

                # Historical source transformers stored the
                # complete raw location mainly in country.
                #
                # Therefore use country first. City/state are
                # fallbacks in case some rows already contain
                # partially structured data.
                raw_location = (
                    location.country
                    or location.city
                    or location.state
                )

                old_city = location.city
                old_state = location.state
                old_country = location.country
                old_remote = bool(location.remote)

                result = normalizer.normalize(
                    raw_location=raw_location,
                    remote=old_remote,
                )

                location.city = result.city
                location.state = result.state
                location.country = result.country
                location.remote = result.remote

                if (
                    old_city != result.city
                    or old_state != result.state
                    or old_country != result.country
                    or old_remote != result.remote
                ):
                    changed += 1

                processed += 1

                if processed % 50 == 0:
                    logger.info(
                        f"Processed {processed}/{len(jobs)} jobs"
                    )

            session.commit()

        except Exception:
            session.rollback()

            logger.exception(
                "Existing location normalization failed."
            )

            raise

    logger.info(
        "Existing location normalization complete: "
        f"processed={processed}, "
        f"changed={changed}, "
        f"without_location={without_location}, "
        f"version={normalizer.VERSION}"
    )

    return (
        processed,
        changed,
        without_location,
    )


def main() -> None:
    logger.info(
        "Starting normalization of existing database locations..."
    )

    processed, changed, without_location = run()

    logger.info(
        "Location normalization finished: "
        f"processed={processed}, "
        f"changed={changed}, "
        f"without_location={without_location}"
    )


if __name__ == "__main__":
    main()