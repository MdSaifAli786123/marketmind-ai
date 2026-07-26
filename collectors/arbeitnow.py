from __future__ import annotations

from collectors.base import BaseCollector
from config.settings import settings
from domain.raw_job import RawJob
from utils.http import create_session
from utils.logger import logger


class ArbeitnowCollector(BaseCollector):
    """
    Collect live job postings from the Arbeitnow public API.
    """

    API_URL = "https://www.arbeitnow.com/api/job-board-api"

    def __init__(self, max_pages: int = 5) -> None:
        self.session = create_session()
        self.max_pages = max_pages

    @property
    def source_name(self) -> str:
        return "Arbeitnow"

    def collect(self) -> list[RawJob]:
        logger.info("Downloading jobs from Arbeitnow...")

        raw_jobs: list[RawJob] = []

        for page in range(1, self.max_pages + 1):
            try:
                response = self.session.get(
                    self.API_URL,
                    params={"page": page},
                    timeout=settings.request_timeout,
                )

                response.raise_for_status()

                payload = response.json()
                jobs = payload.get("data", [])

                if not jobs:
                    break

                raw_jobs.extend(
                    RawJob(
                        source=self.source_name,
                        payload=job,
                    )
                    for job in jobs
                )

            except Exception:
                logger.exception(
                    f"Arbeitnow collection failed on page {page}."
                )
                break

        logger.info(
            f"Downloaded {len(raw_jobs)} jobs from Arbeitnow."
        )

        return raw_jobs